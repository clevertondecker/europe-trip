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
from public_plan_safety import ensure_public_plan_is_minimal

REPO="clevertondecker/europe-trip"
ID_PATTERN=re.compile(r"^trip-[a-f0-9]{12}$")
def safe_path(plan_id:str)->str:
    if not ID_PATTERN.fullmatch(plan_id):raise ValueError("Invalid plan ID")
    return "data/user_plans/"+plan_id+".json"

def order_saved_plans(plan_ids:list[str], commits:list[dict])->list[dict]:
    """Order repository-backed IDs by most recent saved commit, newest first.

    Never fabricate a stored plan from commit metadata; only accept IDs from
    a successful contents listing. A file can be listed even if its last commit
    is outside the 100 newest entries.
    """
    known={x for x in plan_ids if ID_PATTERN.fullmatch(x)}
    result=[]
    for entry in commits:
        message=entry.get("commit",{}).get("message","")
        found=re.match(r"^Update travel plan (trip-[a-f0-9]{12}) r([0-9]+)\b",message)
        if not found:
            continue
        pid=found.group(1)
        if pid not in known:
            continue
        known.remove(pid)
        result.append({"plan_id":pid,
                       "saved_at":entry.get("commit",{}).get("committer",{}).get("date"),
                       "revision":int(found.group(2))})
    result.extend({"plan_id":pid,"saved_at":None,"revision":None}
                  for pid in sorted(known))
    return result


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
    def list_plans(self)->list[str]:
        try:
            items=self._request("data/user_plans")
        except HTTPError as exc:
            if exc.code==404:return []
            raise
        return sorted(x["name"][:-5] for x in items
            if x["name"].endswith(".json") and ID_PATTERN.fullmatch(x["name"][:-5]))

    def recent_plans(self)->list[dict]:
        """Look up saved plans without knowing their random session IDs."""
        ids=self.list_plans()
        if not ids:
            return []
        req=Request(f"https://api.github.com/repos/{REPO}/commits?path=data/user_plans&per_page=100",
             headers={"Authorization":"Bearer "+self.token,
                      "Accept":"application/vnd.github+json",
                      "User-Agent":"nossa-europa-2027-advisor"})
        try:
            with urlopen(req,timeout=12) as response:
                commits=json.loads(response.read())
        except HTTPError as exc:
            if exc.code not in (403,404):
                raise
            commits=[]
        return order_saved_plans(ids,commits)

    def history(self,plan_id:str)->list[dict]:
        """Read Git revisions without exposing the underlying token."""
        path=safe_path(plan_id)
        req=Request(f"https://api.github.com/repos/{REPO}/commits?path={path}&per_page=30",
             headers={"Authorization":"Bearer "+self.token,
                      "Accept":"application/vnd.github+json",
                      "User-Agent":"nossa-europa-2027-advisor"})
        with urlopen(req,timeout=12) as response:
            results=json.loads(response.read())
        return [{"sha":x["sha"],"date":x["commit"]["committer"]["date"],
                 "message":x["commit"]["message"].splitlines()[0]} for x in results]

    def load_at_commit(self,plan_id:str,commit_sha:str)->dict:
        if not re.fullmatch(r"[a-f0-9]{40}",commit_sha):
            raise ValueError("Invalid commit SHA")
        obj=self._request(safe_path(plan_id)+"?ref="+commit_sha)
        data=json.loads(base64.b64decode(obj["content"]).decode("utf-8"))
        validate_plan(data)
        if data["plan_id"]!=plan_id:raise ValueError("Mismatched plan")
        return data

    def save(self,plan:dict,expected_sha:str|None)->str:
        validate_plan(plan)
        ensure_public_plan_is_minimal(plan)
        path=safe_path(plan["plan_id"])
        try:
            existing=self.load(plan["plan_id"])
        except HTTPError as exc:
            if exc.code!=404:raise
            existing=None
        if existing is None:
            if expected_sha is not None:
                raise ValueError("New plan must not supply a previous SHA")
        else:
            old,actual_sha=existing
            if expected_sha!=actual_sha:
                raise ValueError("Repository changed: load latest before saving")
            if plan["revision"]<=old["revision"]:
                raise ValueError("Revision must be greater than the stored plan revision")
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
