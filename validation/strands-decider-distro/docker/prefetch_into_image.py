#!/usr/bin/env python3
"""Prefetch Hub weights into the image as real local directories for offline load."""
from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import snapshot_download


def dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def patch_decider_base(decider_dir: Path, base_dir: Path) -> None:
    """Point the checkpoint config at the local base weights for offline load."""
    for name in ("hobson_config.json", "strands_decider_config.json"):
        cfg_path = decider_dir / name
        if not cfg_path.is_file():
            continue
        cfg = json.loads(cfg_path.read_text())
        cfg["base_model"] = str(base_dir)
        cfg["base_revision"] = None
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
        print(f"patched {cfg_path} base_model -> {base_dir}", flush=True)


def main() -> None:
    decider_id = os.environ["DECIDER_HUB_ID"]
    base_id = os.environ["BASE_MODEL_ID"]
    base_rev = os.environ["BASE_MODEL_REVISION"]
    materialize = Path(os.environ.get("MODEL_MATERIALIZE_DIR", "/opt/models"))
    materialize.mkdir(parents=True, exist_ok=True)

    decider_local = materialize / "decider"
    base_local = materialize / "base"
    print("downloading decider...", flush=True)
    snapshot_download(decider_id, local_dir=str(decider_local))
    print("downloading base...", flush=True)
    snapshot_download(base_id, revision=base_rev, local_dir=str(base_local))
    patch_decider_base(decider_local, base_local)

    decider_bytes = dir_bytes(decider_local)
    base_bytes = dir_bytes(base_local)
    print(f"DECIDER_LOCAL={decider_local} bytes={decider_bytes}", flush=True)
    print(f"BASE_LOCAL={base_local} bytes={base_bytes}", flush=True)
    for label, path, minimum in (
        ("decider", decider_local, 50_000_000),
        ("base", base_local, 2_000_000_000),
    ):
        if dir_bytes(path) < minimum:
            raise SystemExit(
                f"{label} materialization too small ({dir_bytes(path)} bytes); "
                "likely pointer/incomplete download"
            )

    Path("/opt/models/DECIDER_LOCAL_PATH").write_text(str(decider_local) + "\n")
    print("prefetch ok", flush=True)


if __name__ == "__main__":
    main()
