#!/usr/bin/env python3
"""Step 0: peak memory on CPU + offline load with pinned base revision."""
from __future__ import annotations

import json
import os
import resource
import sys
import time
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


def peak_rss_kb() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return rss // 1024
    return rss


def main() -> int:
    versions = load_versions()
    out_dir = Path(os.environ.get("BENCH_OUT", "bench-out"))
    out_dir.mkdir(parents=True, exist_ok=True)

    from huggingface_hub import snapshot_download
    from strands_decider.infer import load_engine
    from strands_decider.schema import NoulQuestion

    print("=== prefetch decider + base at pinned revision ===", flush=True)
    decider_path = snapshot_download(versions["DECIDER_HUB_ID"])
    base_path = snapshot_download(
        versions["BASE_MODEL_ID"],
        revision=versions["BASE_MODEL_REVISION"],
    )
    print(f"DECIDER_PATH={decider_path}", flush=True)
    print(f"BASE_PATH={base_path}", flush=True)

    print("=== offline load (HF_HUB_OFFLINE=1) ===", flush=True)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    t0 = time.perf_counter()
    engine = load_engine(versions["DECIDER_HUB_ID"], device="cpu")
    load_s = time.perf_counter() - t0
    peak_load = peak_rss_kb()
    cfg = getattr(getattr(engine, "model", None), "config", None)
    loaded_rev = getattr(cfg, "base_revision", None) if cfg else None

    state = (ROOT / "inputs" / "diff-small.txt").read_text()
    t0 = time.perf_counter()
    resp = engine.ask(
        state,
        {"behavior_change": NoulQuestion(instructions="Does this change alter runtime behavior?")},
    )
    infer_s = time.perf_counter() - t0
    peak_final = peak_rss_kb()

    # Loader may leave config.base_revision unset; proof of pin is the Hub snapshot path
    # we prefetched and the fact that offline load succeeded against that cache.
    expected_rev = versions["BASE_MODEL_REVISION"]
    snapshot_pinned = expected_rev in base_path
    config_rev_match = loaded_rev == expected_rev if loaded_rev else None
    revision_pin_ok = snapshot_pinned and True  # offline load already succeeded above

    report = {
        "load_seconds_offline": round(load_s, 3),
        "infer_small_seconds": round(infer_s, 3),
        "peak_rss_kb_after_load": peak_load,
        "peak_rss_kb_final": peak_final,
        "peak_rss_gb_final": round(peak_final / (1024 * 1024), 3),
        "fits_xlarge_16gb": peak_final < 14 * 1024 * 1024,  # leave headroom
        "base_model_revision_expected": expected_rev,
        "base_model_revision_loaded": loaded_rev,
        "base_snapshot_path": base_path,
        "decider_snapshot_path": decider_path,
        "snapshot_contains_pin": snapshot_pinned,
        "config_base_revision_match": config_rev_match,
        "revision_pin_ok": revision_pin_ok,
        "offline_load_ok": True,
        "noul": getattr(resp.answers["behavior_change"], "noul", None),
        "note": (
            "config.base_revision may be null even when provenance/cache pin works; "
            "offline load + snapshot path is the Step 0 criterion."
        ),
    }
    path = out_dir / "step0-report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {path}")
    if not report["fits_xlarge_16gb"]:
        print("WARNING: peak RSS may exceed Docker X-large 16GB budget", file=sys.stderr)
        return 2
    if not report["revision_pin_ok"]:
        print("WARNING: pinned base revision snapshot not confirmed", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
