"""Optional royalty-free stock video backgrounds via the Pexels API.

Fully optional and off by default: a profile only uses this if it sets
"use_stock_video": True AND the PEXELS_API_KEY env var is set (a free key
from pexels.com/api - no payment required). If either is missing, or the
API call fails for any reason (network, quota, no matching clip), the
caller falls back to the procedural gradient background - the system never
depends on this for its "completely free, always works" guarantee.
"""
import os
import random

import requests

PEXELS_API = "https://api.pexels.com/videos/search"


def fetch_background_video(query: str, out_path: str, min_duration: int = 15) -> str | None:
    """Downloads a portrait-orientation stock clip matching `query` to
    `out_path`. Returns the path on success, None on any failure."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.get(
            PEXELS_API,
            headers={"Authorization": api_key},
            params={"query": query, "orientation": "portrait", "per_page": 10},
            timeout=15,
        )
        resp.raise_for_status()
        videos = [v for v in resp.json().get("videos", []) if v.get("duration", 0) >= min_duration]
        if not videos:
            return None
        video = random.choice(videos)
        portrait_files = [f for f in video["video_files"] if f.get("height", 0) >= f.get("width", 1)]
        if not portrait_files:
            return None
        best = max(portrait_files, key=lambda f: f.get("height", 0))

        video_resp = requests.get(best["link"], timeout=30)
        video_resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(video_resp.content)
        return out_path
    except Exception as e:
        print(f"Stock video fetch failed ({query!r}): {e}")
        return None
