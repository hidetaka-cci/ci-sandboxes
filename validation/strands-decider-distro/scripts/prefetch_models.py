#!/usr/bin/env python3
"""Prefetch Decider + pinned base model into the Hugging Face cache."""
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


def main() -> int:
    versions = load_versions()
    from huggingface_hub import snapshot_download

    decider = snapshot_download(versions["DECIDER_HUB_ID"])
    base = snapshot_download(
        versions["BASE_MODEL_ID"],
        revision=versions["BASE_MODEL_REVISION"],
    )
    print(f"DECIDER_PATH={decider}")
    print(f"BASE_PATH={base}")
    print("prefetch ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
