#!/usr/bin/env python3
"""Timed load + inference for strands-decider distribution comparison (single process)."""
from __future__ import annotations

import json
import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NOUL = "Does this change alter runtime behavior?"
SCORE_Q = "What is the risk level of this change?"
SCORE_LEVELS = ["low", "medium", "high", "critical"]
CHOICE_Q = "Which test suites should run?"
CHOICE_OPTS = ["smoke", "unit", "integration", "e2e", "config"]


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


def format_answers(response) -> str:
    lines: list[str] = []
    for name, ans in response.answers.items():
        if ans.type == "noul":
            lines.append(f"{name} noul = {ans.noul:.3f}")
        elif ans.type == "choice":
            lines.append(f"{name} -> {ans.choice} (confidence {ans.confidence:.3f})")
            for opt, p in sorted(ans.probabilities.items(), key=lambda kv: -kv[1]):
                lines.append(f"    {opt:<24} {p:.3f}")
        else:
            lines.append(f"{name} score = {ans.score:.2f} (confidence {ans.confidence:.3f})")
            probs = ans.probabilities
            if isinstance(probs, dict):
                items = list(probs.items())
            else:
                items = [(str(i), p) for i, p in enumerate(probs)]
            for label, p in items:
                lines.append(f"    {label:<24} {p:.3f}")
    return "\n".join(lines) + "\n"


def main() -> int:
    method = os.environ.get("METHOD", "A")
    versions = load_versions()
    hub_id = versions["DECIDER_HUB_ID"]
    out_dir = Path(os.environ.get("BENCH_OUT", "bench-out"))
    out_dir.mkdir(parents=True, exist_ok=True)

    from strands_decider.infer import load_engine
    from strands_decider.schema import ChoiceQuestion, NoulQuestion, ScoreQuestion

    questions = {
        "behavior_change": NoulQuestion(instructions=NOUL),
        "risk": ScoreQuestion(instructions=SCORE_Q, criteria=SCORE_LEVELS),
        "suites": ChoiceQuestion(
            instructions=CHOICE_Q,
            criteria={o: "" for o in CHOICE_OPTS},
        ),
    }

    print(f"=== [{method}] load engine ===", flush=True)
    t0 = time.perf_counter()
    engine = load_engine(hub_id, device="cpu")
    load_s = time.perf_counter() - t0
    peak_after_load = peak_rss_kb()
    base_rev = None
    cfg = getattr(getattr(engine, "model", None), "config", None)
    if cfg is not None:
        base_rev = getattr(cfg, "base_revision", None)
    print(f"LOAD_SECONDS={load_s:.3f}", flush=True)
    print(f"LOADED_BASE_REVISION={base_rev}", flush=True)

    small = (ROOT / "inputs" / "diff-small.txt").read_text()
    large = (ROOT / "inputs" / "diff-large.txt").read_text()

    print(f"=== [{method}] infer small (~{len(small) // 4} approx tokens) ===", flush=True)
    t0 = time.perf_counter()
    resp_small = engine.ask(small, questions)
    small_s = time.perf_counter() - t0
    (out_dir / f"result-small-{method}.txt").write_text(format_answers(resp_small))
    print(format_answers(resp_small), flush=True)

    print(f"=== [{method}] infer large (~{len(large) // 4} approx tokens) ===", flush=True)
    t0 = time.perf_counter()
    resp_large = engine.ask(large, questions)
    large_s = time.perf_counter() - t0
    (out_dir / f"result-large-{method}.txt").write_text(format_answers(resp_large))
    print(format_answers(resp_large), flush=True)

    peak_final = peak_rss_kb()
    metrics = {
        "method": method,
        "strands_decider_version": versions["STRANDS_DECIDER_VERSION"],
        "decider_hub_id": hub_id,
        "base_model_id": versions["BASE_MODEL_ID"],
        "base_model_revision_expected": versions["BASE_MODEL_REVISION"],
        "base_model_revision_loaded": base_rev,
        "revision_match": (
            base_rev == versions["BASE_MODEL_REVISION"] if base_rev else None
        ),
        "load_seconds": round(load_s, 3),
        "infer_small_seconds": round(small_s, 3),
        "infer_large_seconds": round(large_s, 3),
        "peak_rss_kb_after_load": peak_after_load,
        "peak_rss_kb_final": peak_final,
        "circle_build_num": os.environ.get("CIRCLE_BUILD_NUM", ""),
        "circle_job": os.environ.get("CIRCLE_JOB", ""),
        "circle_workflow_id": os.environ.get("CIRCLE_WORKFLOW_ID", ""),
        "circle_pipeline_id": os.environ.get("CIRCLE_PIPELINE_ID", ""),
    }
    metrics_path = out_dir / f"metrics-{method}.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"Wrote {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
