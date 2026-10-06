#!/usr/bin/env python3
"""Prefetch Hub weights into the image and pin refs/main for offline load."""
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download


def pin_main(hub: Path, repo_id: str, revision: str) -> None:
    refs = hub / ("models--" + repo_id.replace("/", "--")) / "refs"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "main").write_text(revision + "\n")
    print(f"pinned {repo_id} main -> {revision}")


def main() -> None:
    decider_id = os.environ["DECIDER_HUB_ID"]
    base_id = os.environ["BASE_MODEL_ID"]
    base_rev = os.environ["BASE_MODEL_REVISION"]
    hub = Path(os.environ.get("HF_HUB_CACHE") or (Path(os.environ["HF_HOME"]) / "hub"))

    decider = snapshot_download(decider_id)
    base = snapshot_download(base_id, revision=base_rev)
    pin_main(hub, base_id, base_rev)

    # Also pin decider refs/main to the resolved snapshot hash when available.
    decider_snap = Path(decider).name
    pin_main(hub, decider_id, decider_snap)

    size = sum(p.stat().st_size for p in hub.rglob("*") if p.is_file())
    print(f"DECIDER={decider}")
    print(f"BASE={base}")
    print(f"HF_CACHE_BYTES={size}")


if __name__ == "__main__":
    main()
