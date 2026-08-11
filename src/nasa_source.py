"""Fetches a real NASA image (real photo + verified caption) from NASA's
Image and Video Library - free, no API key, no auth required. All NASA
media is public domain by default (US federal government work); items from
non-NASA partners set a "copyright" field, which we skip. This grounds the
"Uzayın Sırları" channel's scripts in real, NASA-captioned imagery instead
of anything the LLM invents, and gives the video a genuine, correctly
licensed space photo background.
"""
import random

import requests

SEARCH_URL = "https://images-api.nasa.gov/search"
ASSET_URL = "https://images-api.nasa.gov/asset/{}"

# Broad, visually dramatic search terms so consecutive videos don't cluster
# on the same kind of object.
SEARCH_TERMS = [
    "black hole", "nebula", "galaxy collision", "supernova", "exoplanet",
    "saturn rings", "jupiter storm", "aurora", "solar flare", "spacewalk",
    "hubble deep field", "mars rover", "international space station",
    "moon landing", "comet", "milky way", "star cluster", "solar eclipse",
]


def _pick_image_link(nasa_id: str) -> str | None:
    try:
        resp = requests.get(ASSET_URL.format(nasa_id), timeout=15)
        resp.raise_for_status()
        hrefs = [item["href"] for item in resp.json().get("collection", {}).get("items", [])]
    except Exception:
        return None
    for suffix in ("~large.jpg", "~orig.jpg", "~medium.jpg"):
        for href in hrefs:
            if href.endswith(suffix):
                return href
    return None


def fetch_random_nasa_item(out_image_path: str) -> dict | None:
    """Downloads a suitable image's photo to `out_image_path` and returns
    its metadata, or None if nothing suitable was found - callers must
    treat None as "try again" / "skip today", never crash the pipeline
    over a single NASA API hiccup."""
    query = random.choice(SEARCH_TERMS)
    try:
        resp = requests.get(SEARCH_URL, params={"q": query, "media_type": "image"}, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("collection", {}).get("items") or []
    except Exception as e:
        print(f"NASA search failed ({query!r}): {e}")
        return None

    random.shuffle(items)
    for item in items[:20]:
        data = (item.get("data") or [{}])[0]
        if data.get("copyright"):
            continue  # not public domain - skip
        title = data.get("title") or ""
        # Descriptions often end with unrelated social-media/credit boilerplate
        # ("Follow us on Twitter...") - keep only the front part with the
        # actual scientific content.
        description = (data.get("description") or "")[:700]
        nasa_id = data.get("nasa_id")
        if not nasa_id or len(description) < 20:
            continue

        image_url = _pick_image_link(nasa_id)
        if not image_url:
            continue

        try:
            img_resp = requests.get(image_url, timeout=30)
            img_resp.raise_for_status()
            with open(out_image_path, "wb") as f:
                f.write(img_resp.content)
        except Exception as e:
            print(f"NASA image download failed: {e}")
            continue

        return {
            "title": title,
            "description": description,
            "date_created": data.get("date_created") or "",
            "center": data.get("center") or "",
            "keywords": ", ".join(data.get("keywords") or []),
            "source_url": f"https://images.nasa.gov/details/{nasa_id}",
        }

    print(f"No suitable public-domain NASA item found for query {query!r}")
    return None
