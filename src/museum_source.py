"""Fetches a random public-domain museum object (real photo + verified
metadata) from the Metropolitan Museum of Art's Open Access API - free, no
API key, no auth required. This grounds the "Müze Sırları" channel's
scripts in a real, catalogued artifact instead of anything the LLM invents,
and gives the video a genuine (public-domain licensed) photo background
instead of a procedural gradient.
"""
import random

import requests

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"

# Broad, history-rich search terms so consecutive videos don't cluster on
# the same culture/era.
SEARCH_TERMS = [
    "ancient egypt", "islamic art", "medieval europe", "ancient greece",
    "roman empire", "ottoman", "persian manuscript", "byzantine",
    "ancient china", "mesopotamia", "renaissance", "viking", "ancient rome sculpture",
]


def fetch_random_object(out_image_path: str) -> dict | None:
    """Downloads a suitable object's photo to `out_image_path` and returns
    its metadata, or None if nothing suitable was found - callers must
    treat None as "try again" / "skip today", never crash the pipeline
    over a single museum API hiccup."""
    query = random.choice(SEARCH_TERMS)
    try:
        resp = requests.get(SEARCH_URL, params={"q": query, "hasImages": "true"}, timeout=15)
        resp.raise_for_status()
        object_ids = resp.json().get("objectIDs") or []
    except Exception as e:
        print(f"Museum search failed ({query!r}): {e}")
        return None

    random.shuffle(object_ids)
    for object_id in object_ids[:25]:
        try:
            obj_resp = requests.get(OBJECT_URL.format(object_id), timeout=15)
            obj_resp.raise_for_status()
            obj = obj_resp.json()
        except Exception:
            continue

        if not obj.get("isPublicDomain"):
            continue
        image_url = obj.get("primaryImage")
        if not image_url:
            continue

        facts = ", ".join(filter(None, [
            obj.get("culture"), obj.get("period"), obj.get("dynasty"),
            obj.get("artistDisplayName"), obj.get("objectDate"),
        ]))
        description = obj.get("objectDescription") or obj.get("creditLine") or ""
        if len(facts) < 8 and not description:
            continue

        try:
            img_resp = requests.get(image_url, timeout=30)
            img_resp.raise_for_status()
            with open(out_image_path, "wb") as f:
                f.write(img_resp.content)
        except Exception as e:
            print(f"Museum image download failed: {e}")
            continue

        return {
            "title": obj.get("title") or "İsimsiz Eser",
            "culture": obj.get("culture") or "",
            "period": obj.get("period") or "",
            "dynasty": obj.get("dynasty") or "",
            "artist": obj.get("artistDisplayName") or "",
            "date": obj.get("objectDate") or "",
            "medium": obj.get("medium") or "",
            "department": obj.get("department") or "",
            "description": description,
            "credit_line": obj.get("creditLine") or "",
            "museum": "The Metropolitan Museum of Art",
            "source_url": f"https://www.metmuseum.org/art/collection/search/{object_id}",
        }

    print(f"No suitable public-domain object found for query {query!r}")
    return None
