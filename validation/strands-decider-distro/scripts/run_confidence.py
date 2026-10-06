#!/usr/bin/env python3
"""Measure confidence rates on real PR/commit diffs with redesigned questions.

Routing convention (from strands-decider docs): act without check at confidence >= 0.9.
For noul, treat as confident when P(true) >= 0.9 or <= 0.1 (i.e. |2p-1| >= 0.8).
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
NOUL_HI = 0.9
NOUL_LO = 0.1

REPO_CONTEXT = """\
Repository: hidetaka-cci/ci-sandboxes
Stack: TypeScript + Vitest demo app, plus CircleCI / GitHub Actions configs.
What test groups mean HERE:
- unit: Vitest tests under src/**/*.test.ts (npm test / vitest run). Covers app/runtime code.
- smoke: smallest sanity subset; cheap signal that the tree still boots.
- integration: multi-file or suite-interaction checks (e.g. DTS / auto-rerun harnesses).
- e2e: browser or end-to-end UI flows (rarely present in this repo).
- config: CircleCI YAML / GitHub Actions workflow validity and pipeline wiring only.
"""

# Score levels: ordered low -> critical, labels carry meaning.
RISK_LEVELS = [
    "low_docs_or_comments_only",
    "medium_tests_or_ci_wiring",
    "high_runtime_logic_change",
    "critical_security_or_data_loss",
]


def build_questions():
    from strands_decider.schema import NoulQuestion, ScoreQuestion

    return {
        "behavior_change": NoulQuestion(
            instructions=(
                "Does this diff change application runtime behavior "
                "(TypeScript/JavaScript that the app or Vitest executes), "
                "as opposed to documentation-only or CI-config-only changes?"
            )
        ),
        "risk": ScoreQuestion(
            instructions=(
                "How risky is merging this change for the ci-sandboxes demo repo? "
                "Use the level labels: low=docs/comments only; "
                "medium=tests or CI wiring; high=runtime logic; "
                "critical=security or data-loss risk."
            ),
            criteria=RISK_LEVELS,
        ),
        # Multi-select via independent yes/no (not a single N-way choice).
        "need_unit": NoulQuestion(
            instructions=(
                "Should we run the Vitest unit suite (src/**/*.test.ts) for this diff? "
                "Yes if src/ app or test code changed; No if only docs or CI YAML changed."
            )
        ),
        "need_smoke": NoulQuestion(
            instructions=(
                "Should we run a smoke / sanity subset for this diff? "
                "Yes for almost any code or config change; No only for pure markdown docs."
            )
        ),
        "need_integration": NoulQuestion(
            instructions=(
                "Should we run integration-style harness tests "
                "(multi-file / DTS / auto-rerun style) for this diff? "
                "Yes if those harnesses or shared test helpers changed; otherwise No."
            )
        ),
        "need_e2e": NoulQuestion(
            instructions=(
                "Should we run browser/e2e UI flows for this diff? "
                "Yes only if UI pages, Vite app shell, or e2e harnesses changed; "
                "otherwise No (this repo rarely has e2e)."
            )
        ),
        "need_config": NoulQuestion(
            instructions=(
                "Should we validate CircleCI / GitHub Actions config for this diff? "
                "Yes if .circleci/** or .github/workflows/** changed; otherwise No."
            )
        ),
    }


def noul_confident(p: float) -> bool:
    return p >= NOUL_HI or p <= NOUL_LO


def answer_confident(ans) -> bool:
    if ans.type == "noul":
        return noul_confident(float(ans.noul))
    return float(ans.confidence) >= CONF_THRESHOLD


def truncate_diff(text: str, max_chars: int = 14000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[diff truncated for model window]\n"


def main() -> int:
    versions = load_versions()
    out_dir = Path(os.environ.get("BENCH_OUT", "bench-out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir = ROOT / "inputs" / "prs"

    from strands_decider.infer import load_engine

    questions = build_questions()
    checkpoint = resolve_decider_path(versions)
    print(f"CHECKPOINT={checkpoint}", flush=True)
    print(f"HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}", flush=True)
    print(f"TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')}", flush=True)

    t0 = time.perf_counter()
    engine = load_engine(checkpoint, device="cpu")
    load_s = time.perf_counter() - t0
    print(f"LOAD_SECONDS={load_s:.3f}", flush=True)

    diff_files = sorted(
        p
        for p in diffs_dir.iterdir()
        if p.is_file() and p.suffix == ".diff" and p.stat().st_size > 100
    )
    per_diff = []
    totals = {"answers": 0, "confident": 0, "by_question": {}}

    for path in diff_files:
        state = REPO_CONTEXT + "\nPR or commit diff:\n" + truncate_diff(path.read_text(errors="replace"))
        t0 = time.perf_counter()
        resp = engine.ask(state, questions)
        elapsed = time.perf_counter() - t0

        answers = {}
        conf_count = 0
        for name, ans in resp.answers.items():
            conf = answer_confident(ans)
            conf_count += int(conf)
            totals["answers"] += 1
            totals["confident"] += int(conf)
            qstat = totals["by_question"].setdefault(
                name, {"answers": 0, "confident": 0}
            )
            qstat["answers"] += 1
            qstat["confident"] += int(conf)

            if ans.type == "noul":
                answers[name] = {
                    "type": "noul",
                    "noul": round(float(ans.noul), 4),
                    "confident": conf,
                    "derived_confidence": round(abs(2 * float(ans.noul) - 1), 4),
                }
            elif ans.type == "choice":
                answers[name] = {
                    "type": "choice",
                    "choice": ans.choice,
                    "confidence": round(float(ans.confidence), 4),
                    "confident": conf,
                    "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
                }
            else:
                answers[name] = {
                    "type": "score",
                    "score": round(float(ans.score), 4),
                    "confidence": round(float(ans.confidence), 4),
                    "confident": conf,
                    "probabilities": (
                        {k: round(v, 4) for k, v in ans.probabilities.items()}
                        if isinstance(ans.probabilities, dict)
                        else [round(x, 4) for x in ans.probabilities]
                    ),
                }

        entry = {
            "id": path.name,
            "bytes": path.stat().st_size,
            "infer_seconds": round(elapsed, 3),
            "confident_answers": conf_count,
            "total_answers": len(answers),
            "answers": answers,
        }
        per_diff.append(entry)
        print(
            f"{path.name}: confident {conf_count}/{len(answers)} in {elapsed:.2f}s",
            flush=True,
        )

    rate = (totals["confident"] / totals["answers"]) if totals["answers"] else 0.0
    by_q = {
        k: {
            **v,
            "rate": round(v["confident"] / v["answers"], 4) if v["answers"] else 0.0,
        }
        for k, v in totals["by_question"].items()
    }
    # Diff-level: all answers confident
    diffs_all_conf = sum(1 for d in per_diff if d["confident_answers"] == d["total_answers"])
    # Routing proxy: behavior_change confident AND at least one suite noul confident
    routing_ready = 0
    for d in per_diff:
        a = d["answers"]
        if a.get("behavior_change", {}).get("confident") and any(
            a.get(k, {}).get("confident")
            for k in ("need_unit", "need_smoke", "need_integration", "need_e2e", "need_config")
        ):
            routing_ready += 1

    report = {
        "threshold": CONF_THRESHOLD,
        "noul_confident_rule": f"noul>={NOUL_HI} or noul<={NOUL_LO}",
        "load_seconds": round(load_s, 3),
        "decider_hub_id": versions["DECIDER_HUB_ID"],
        "decider_revision": versions["DECIDER_REVISION"],
        "base_model_revision": versions["BASE_MODEL_REVISION"],
        "hf_hub_offline": os.environ.get("HF_HUB_OFFLINE"),
        "diff_count": len(per_diff),
        "answer_confidence_rate": round(rate, 4),
        "confident_answers": totals["confident"],
        "total_answers": totals["answers"],
        "diffs_all_answers_confident": diffs_all_conf,
        "diffs_routing_proxy_ready": routing_ready,
        "by_question": by_q,
        "per_diff": per_diff,
        "verdict": (
            "usable_for_routing"
            if rate >= 0.5
            else "not_usable_low_confidence"
        ),
        "note": (
            "usable_for_routing is a soft bar (half of answers at >=0.9). "
            "Production still needs domain review of wrong confident answers."
        ),
    }
    out = out_dir / "confidence-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in report if k != "per_diff"}, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
