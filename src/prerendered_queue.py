"""Select the next pre-rendered video without mixing channel queues."""
from __future__ import annotations

import os
import random
import re
import unicodedata


MAHALLE_RELEASE_ASSETS = {
    f"{episode}.bolum.mp4": episode
    for episode in range(1, 12)
}
MINIK_PRIMARY_PREFIX = "minik_kesifler-"
MINIK_LEGACY_PREFIXES = ("leowildadventures-", "mellofromars-")


def canonical_asset_name(filename: str) -> str:
    """Normalize equivalent local and Release-asset names for history checks."""
    basename = os.path.basename(filename)
    stem, extension = os.path.splitext(basename)
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    stem = re.sub(r"_(?:horizontal|vertical)$", "", stem, flags=re.IGNORECASE)
    stem = stem.lower()
    if stem.isdigit():
        stem = str(int(stem))
    return f"{stem}{extension.lower()}"


def _available_assets(local_assets, remote_assets, uploaded_names, predicate):
    assets = {}
    for source, filenames in (("local", local_assets), ("remote", remote_assets)):
        for filename in filenames:
            basename = os.path.basename(filename)
            canonical = canonical_asset_name(basename)
            if not canonical.endswith(".mp4") or canonical in uploaded_names:
                continue
            if predicate(canonical):
                assets.setdefault(canonical, (source, basename))
    return assets


def select_next_asset(profile_key, local_assets, remote_assets, history, chooser=None):
    """Return (source, filename); Mahalle episodes are ordered, Minik is random."""
    chooser = chooser or random.choice
    uploaded_names = {
        canonical_asset_name(item["filename"])
        for item in history
        if isinstance(item, dict) and isinstance(item.get("filename"), str)
    }

    if profile_key == "animai_studio":
        mahalle_assets = _available_assets(
            local_assets,
            remote_assets,
            uploaded_names,
            lambda name: name in MAHALLE_RELEASE_ASSETS,
        )
        if mahalle_assets:
            return min(
                mahalle_assets.values(),
                key=lambda asset: MAHALLE_RELEASE_ASSETS[canonical_asset_name(asset[1])],
            )

        kasa_assets = _available_assets(
            (),
            remote_assets,
            uploaded_names,
            lambda name: re.fullmatch(r"\d+\.mp4", name) is not None,
        )
        if kasa_assets:
            return min(
                kasa_assets.values(),
                key=lambda asset: int(os.path.splitext(asset[1])[0]),
            )
        return None

    if profile_key == "minik_maceralar":
        primary_assets = _available_assets(
            local_assets,
            remote_assets,
            uploaded_names,
            lambda name: name.startswith(MINIK_PRIMARY_PREFIX),
        )
        if primary_assets:
            return chooser(list(primary_assets.values()))

        legacy_assets = _available_assets(
            local_assets,
            remote_assets,
            uploaded_names,
            lambda name: name.startswith(MINIK_LEGACY_PREFIXES),
        )
        if legacy_assets:
            return chooser(list(legacy_assets.values()))
        return None

    raise ValueError(f"Unsupported prerendered profile: {profile_key!r}")
