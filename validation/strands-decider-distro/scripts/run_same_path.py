#!/usr/bin/env python3
"""Same-path diffs: can Decider separate cosmetic vs behavioral at confidence >= 0.9?

Scoring is unified: choice.confidence >= 0.9. No noul p>=0.9 shortcut.
Gold labels live in gold.json (human-assigned; path-filtering cannot produce them).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from load_pinned import load_versions, resolve_decider_path  # noqa: E402

CONF_THRESHOLD = 0.9

TS_CRITERIA = {
    "cosmetic": (
        "Comments, renaming, whitespace, or equivalent refactor. "
        "Runtime outputs and control flow stay the same."
    ),
    "behavioral": (
        "Return values, arithmetic, conditions, or event handling change. "
        "Callers can observe a different result."
    ),
}

YML_CRITERIA = {
    "cosmetic": (
        "Comments or whitespace only. Jobs, steps, images, and graph are unchanged."
    ),
    "scalar": (
        "An existing key's value changes (image tag, resource_class, timeout) "
        "but no job, step, or requires edge is added or removed."
    ),
    "structural": (
        "A job, step, workflow, or requires edge is added, removed, or rewired. "
        "The pipeline graph changes."
    ),
}

TS_Q = (
    "This diff touches only TypeScript under src/. "
    "Does it change runtime behavior, or is it cosmetic?"
)
YML_Q = (
    "This diff touches only .circleci/config.yml. "
    "Is it a comment, a scalar value tweak, or a structural graph change?"
)


def questions_for(kind: str):
    from strands_decider.schema import ChoiceQuestion

    if kind == "ts_behavior":
        return {
            "change": ChoiceQuestion(instructions=TS_Q, criteria=TS_CRITERIA),
        }
    if kind == "yml_shape":
        return {
            "change": ChoiceQuestion(instructions=YML_Q, criteria=YML_CRITERIA),
        }
    raise ValueError(kind)


def main() -> int:
    versions = load_versions()
    out_dir = Path(os.environ.get("BENCH_OUT", "bench-out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    case_dir = ROOT / "inputs" / "same-path"
    gold = json.loads((case_dir / "gold.json").read_text())

    from strands_decider.infer import load_engine

    checkpoint = resolve_decider_path(versions)
    print(f"CHECKPOINT={checkpoint}", flush=True)
    t0 = time.perf_counter()
    engine = load_engine(checkpoint, device="cpu")
    print(f"LOAD_SECONDS={time.perf_counter() - t0:.3f}", flush=True)

    per = []
    n = {"total": 0, "correct": 0, "confident": 0, "confident_correct": 0, "confident_wrong": 0}

    for name, meta in sorted(gold.items()):
        diff = (case_dir / name).read_text()
        qs = questions_for(meta["question"])
        t0 = time.perf_counter()
        resp = engine.ask(diff, qs)
        elapsed = time.perf_counter() - t0
        ans = resp.answers["change"]
        pred = ans.choice
        conf = float(ans.confidence)
        confident = conf >= CONF_THRESHOLD
        correct = pred == meta["gold"]
        n["total"] += 1
        n["correct"] += int(correct)
        n["confident"] += int(confident)
        n["confident_correct"] += int(confident and correct)
        n["confident_wrong"] += int(confident and not correct)
        entry = {
            "id": name,
            "path": meta["path"],
            "gold": meta["gold"],
            "predicted": pred,
            "correct": correct,
            "confidence": round(conf, 4),
            "confident": confident,
            "act_without_check": confident,
            "would_skip_if_cosmetic_confident": bool(
                confident and pred == "cosmetic"
            ),
            "unsafe_skip": bool(confident and pred == "cosmetic" and meta["gold"] != "cosmetic"),
            "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
            "infer_seconds": round(elapsed, 3),
        }
        per.append(entry)
        flag = "OK" if correct else "WRONG"
        band = "HIGH" if confident else "low"
        print(
            f"{name}: gold={meta['gold']} pred={pred} c={conf:.3f} {flag}/{band}",
            flush=True,
        )

    acc = n["correct"] / n["total"] if n["total"] else 0
    conf_acc = (
        n["confident_correct"] / n["confident"] if n["confident"] else None
    )
    report = {
        "confidence_rule": "choice.confidence >= 0.9 (no noul p-shortcut)",
        "threshold": CONF_THRESHOLD,
        "decider_revision": versions["DECIDER_REVISION"],
        "n": n,
        "accuracy": round(acc, 4),
        "high_conf_count": n["confident"],
        "high_conf_accuracy": None if conf_acc is None else round(conf_acc, 4),
        "unsafe_skips": sum(1 for e in per if e["unsafe_skip"]),
        "ts_accuracy": _subset_acc(per, "src/"),
        "yml_accuracy": _subset_acc(per, ".circleci/"),
        "per_case": per,
        "verdict": _verdict(n, per),
    }
    path = out_dir / "same-path-behavior.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in report if k != "per_case"}, indent=2))
    print(f"Wrote {path}")
    return 0


def _subset_acc(per: list[dict], prefix: str) -> float | None:
    rows = [e for e in per if e["path"].startswith(prefix)]
    if not rows:
        return None
    return round(sum(1 for e in rows if e["correct"]) / len(rows), 4)


def _verdict(n: dict, per: list[dict]) -> str:
    if n["confident_wrong"] > 0:
        return "not_safe_high_conf_errors"
    if n["confident"] == 0:
        return "no_high_confidence_on_same_path"
    if any(e["unsafe_skip"] for e in per):
        return "unsafe_would_skip_behavioral"
    return "high_conf_correct_only"


if __name__ == "__main__":
    raise SystemExit(main())
