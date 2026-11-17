#!/usr/bin/env python3
"""Finish two hand-curated Commons photographs and generate the 46-city audit.

This script only runs in the PR asset preparation workflow, never at Streamlit
runtime. The manually chosen files are actual city photographs with Commons
authorship and an open reuse license, not automatic map/diagram thumbnails.
"""
from __future__ import annotations

import json
from pathlib import Path

from curate_missing_destination_photos import (
    ROOT, MANIFEST, licensed_commons_info, create_webp,
)
from ux501_destination_discovery_model import build_destination_discovery

SELECTED_FILES = {
    "saint_louis": "File:Ancienne Mairie Saint-Louis (Haut-Rhin).jpg",
    "amsterdam": "File:Amsterdam Canals - July 2006.jpg",
}
ALT = {
    "saint_louis": "Antiga prefeitura de Saint-Louis, Alto Reno, França",
    "amsterdam": "Canais e casas históricas de Amsterdam, Países Baixos",
}
REPORT = ROOT/"docs/UX_ALL_DESTINATION_PHOTOS_COVERAGE.json"


def main():
    inventory=build_destination_discovery()["destinations"]
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    found,failed=licensed_commons_info(SELECTED_FILES)
    if failed or set(found)!=set(SELECTED_FILES):
        raise RuntimeError("Cannot verify manually chosen photos: "+repr(failed))
    for dest_id, photo in found.items():
        # Force replacement of the non-photographic Amsterdam lead diagram.
        path=ROOT/"assets/destinations"/(dest_id+".webp")
        if path.exists():
            path.unlink()
        size=create_webp(dest_id,photo)
        manifest["assets"][dest_id]={
            "filename":photo["filename"],
            "file":"assets/destinations/"+dest_id+".webp",
            "author":photo["author"],
            "license":photo["license"],
            "license_url":photo["license_url"],
            "source_page":photo["source_page"],
            "alt":ALT[dest_id],
        }
        print("CURATED_OVERRIDE",dest_id,photo["filename"],size,flush=True)
    # Accept genuine copyright-free works with proper Creative Commons PD mark.
    for row in manifest["assets"].values():
        if row["license"].lower().startswith(("public domain","pd-")):
            row["license_url"]="https://creativecommons.org/publicdomain/mark/1.0/"
    manifest["assets"]=dict(sorted(manifest["assets"].items()))
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    coverage=[]
    for d in inventory:
        if d.get("photo"):
            status="editorial"
            src=d["photo"].get("source_page")
        elif d["id"] in manifest["assets"]:
            asset=manifest["assets"][d["id"]]
            path=ROOT/asset["file"]
            if not path.exists() or path.stat().st_size < 5000:
                raise RuntimeError("Missing local file: "+str(path))
            status="local"
            src=asset["source_page"]
        else:
            status="missing"
            src=None
        coverage.append({"destination_id":d["id"],"name":d["name"],
                         "country":d["country"],"status":status,
                         "source_page":src})
    report={
        "catalog_destinations":len(coverage),
        "with_editorial_photo":sum(x["status"]=="editorial" for x in coverage),
        "with_local_photo":sum(x["status"]=="local" for x in coverage),
        "still_missing":sum(x["status"]=="missing" for x in coverage),
        "destinations":coverage,
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print("FINAL_PHOTO_COVERAGE",report["catalog_destinations"],
          report["with_editorial_photo"],report["with_local_photo"],
          report["still_missing"],flush=True)
    if report["still_missing"]:
        raise RuntimeError("Not all destinations have a licensed photo")


if __name__=="__main__":
    main()
