#!/usr/bin/env python3
"""Shared helpers: load versions and resolve a pinned local Decider checkpoint."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_versions() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / "versions.env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k] = v
    return env


def resolve_decider_path(versions: dict[str, str] | None = None) -> str:
    """Return a local snapshot path for the pinned Decider revision."""
    versions = versions or load_versions()
    local_marker = Path("/opt/models/DECIDER_LOCAL_PATH")
    if local_marker.is_file():
        local_path = local_marker.read_text().strip()
        if local_path and Path(local_path).is_dir():
            return local_path

    from huggingface_hub import snapshot_download

    offline = os.environ.get("HF_HUB_OFFLINE") == "1"
    return snapshot_download(
        versions["DECIDER_HUB_ID"],
        revision=versions["DECIDER_REVISION"],
        local_files_only=offline,
    )
