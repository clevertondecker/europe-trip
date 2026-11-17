#!/usr/bin/env python3
"""Fetch licensed, explicitly selected Commons photographs as local WebP assets.

Run only during curation (CI once), never when the Streamlit app renders.
Requires Pillow; no API for choosing imagery at runtime.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/destination_photo_assets.json"
HEADERS={"User-Agent":"NossaEuropa2027/1.0 (https://github.com/clevertondecker/europe-trip; travel imagery curation)"}


def commons_thumbnail(filename: str, width: int = 960) -> str:
    """Direct upload.wikimedia.org thumbnail path, bypassing Action API/redirect."""
    title=filename.replace(" ", "_")
    md5=hashlib.md5(title.encode("utf-8")).hexdigest()
    part=quote(title,safe="(),'!_-")
    return (f"https://upload.wikimedia.org/wikipedia/commons/thumb/"
            f"{md5[0]}/{md5[:2]}/{part}/{width}px-{part}")


def fetch_image(filename: str) -> Image.Image:
    # Wikimedia can serve optimized thumbnails from either upload or thumb host.
    url=commons_thumbnail(filename)
    errors=[]
    for candidate in (url, url.replace("upload.wikimedia.org","thumb.wikimedia.org")):
        try:
            response=requests.get(candidate,headers=HEADERS,timeout=35)
            response.raise_for_status()
            if not response.headers.get("Content-Type","").startswith("image/"):
                raise ValueError("Not an image response")
            if len(response.content) < 2048:
                raise ValueError("Image was suspiciously small")
            image=Image.open(io.BytesIO(response.content))
            image.load()
            if image.width < 400 or image.height < 350:
                raise ValueError("Insufficient source resolution")
            return image
        except (OSError, requests.RequestException, ValueError) as error:
            errors.append(str(error))
    raise RuntimeError("Could not fetch licensed Commons file "+filename+": "+"; ".join(errors))


def build_assets() -> list[Path]:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    saved=[]
    for city, metadata in data["assets"].items():
        path=ROOT/metadata["file"]
        if path.exists() and path.stat().st_size >= 5000:
            with Image.open(path) as current:
                if current.format=="WEBP" and current.size==(800,450):
                    saved.append(path)
                    continue
        image=fetch_image(metadata["filename"])
        image=ImageOps.exif_transpose(image).convert("RGB")
        image=ImageOps.fit(image,(800,450),method=Image.Resampling.LANCZOS,
                           centering=(0.5,0.45))
        path.parent.mkdir(parents=True,exist_ok=True)
        image.save(path,"WEBP",quality=76,method=6)
        with Image.open(path) as test:
            test.verify()
        if not 5000<=path.stat().st_size<=250000:
            path.unlink(missing_ok=True)
            raise RuntimeError(city+": invalid optimized WebP size")
        print(city,path.relative_to(ROOT),path.stat().st_size)
        saved.append(path)
    return saved


if __name__=="__main__":
    result=build_assets()
    total=len(json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"])
    if len(result)!=total:
        raise SystemExit(f"Expected {total} local destination photos, got {len(result)}")
