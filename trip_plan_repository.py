"""Versioned GitHub JSON repository with SHA-based optimistic locking.

The UI must gate any write behind an authenticated owner session; this module
never supplies authorization or reads tokens from files.
"""
from __future__ import annotations
import base64
import json
import re
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from trip_plan_model import validate_plan

REPO="clevertondecker/europe-trip"
ID_PATTERN=re.compile(r"^trip-[a-f0-9]{12}$")
def safe_path(plan_id:str)->str:
    if not ID_PATTERN.fullmatch(plan_id):raise ValueError("Invalid plan ID")
    return "data/user_plans/"+plan_id+".json"

class GitHubPlanRepository:
    def __init__(self, token:str,repo:str=REPO):
        if not token or repo!=REPO: raise ValueError("Configured GitHub repository and token required")
        self.token=token
        self.root=f"https://api.github.com/repos/{repo}/contents/"
    def _request(self,path,method="GET",payload=None):
        body=None if payload is None else json.dumps(payload).encode("utf-8")
        req=Request(self.root+path,data=body,method=method,headers={
            "Authorization":"Bearer "+self.token,"Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28","User-Agent":"nossa-europa-2027-advisor",
            "Content-Type":"application/json"})
        with urlopen(req,timeout=12) as response:
            return json.loads(response.read())
    def load(self,plan_id:str)->tuple[dict,str]:
        obj=self._request(safe_path(plan_id))
        content=base64.b64decode(obj["content"]).decode("utf-8")
        plan=json.loads(content)
        validate_plan(plan)
        if plan["plan_id"]!=plan_id:raise ValueError("Persisted ID mismatch")
        return plan,obj["sha"]
    def save(self,plan:dict,expected_sha:str|None)->str:
        validate_plan(plan)
        path=safe_path(plan["plan_id"])
        try:
            existing=self.load(plan["plan_id"])
        except HTTPError as exc:
            if exc.code!=404:raise
            existing=None
        if existing is None:
            if expected_sha is not None or plan["revision"]!=0:
                raise ValueError("New plan requires first revision, no SHA")
        else:
            old,actual_sha=existing
            if expected_sha!=actual_sha:
                raise ValueError("Repository changed: load latest before saving")
            if plan["revision"]!=old["revision"]+1:
                raise ValueError("Revision must advance exactly once")
        encoded=base64.b64encode(
            (json.dumps(plan,ensure_ascii=False,indent=2)+"\n").encode("utf-8")).decode("ascii")
        payload={"message":"Update travel plan "+plan["plan_id"]+" r"+str(plan["revision"]),
                 "content":encoded,"branch":"main"}
        if expected_sha:payload["sha"]=expected_sha
        try:
            response=self._request(path,"PUT",payload)
        except HTTPError as exc:
            if exc.code in (409,422):raise ValueError("GitHub revision conflict") from exc
            raise
        return response["content"]["sha"]
