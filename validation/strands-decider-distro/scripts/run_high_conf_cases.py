#!/usr/bin/env python3
"""Cases designed so Decider can actually emit high-confidence answers.

Previous run asked policy questions ("should we run tests?") with empty option
text. This run uses the model's strong families: fact, intent, routing, and
classification with described options — including CI-adjacent change-kind.
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

KIND_CRITERIA = {
    "documentation": (
        "Markdown, comments, or docs only. No application source and no CI YAML."
    ),
    "application_code": (
        "TypeScript/JavaScript under src/ that the app or Vitest executes, "
        "including tests next to that code. Not CI workflow YAML."
    ),
    "ci_config": (
        "CircleCI or GitHub Actions YAML under .circleci/ or .github/workflows/. "
        "Pipeline wiring only, not application source."
    ),
}

KIND_Q = (
    "What kind of change is this? Select exactly one. "
    "Match the files in the state, not what someone might do later."
)


def cases():
    from strands_decider.schema import ChoiceQuestion, NoulQuestion, ScoreQuestion

    math_diff = (ROOT / "inputs" / "prs" / "commit-0ae9290.diff").read_text()
    ci_diff = (ROOT / "inputs" / "prs" / "pr-04.diff").read_text()[:6000]
    docs_diff = (ROOT / "inputs" / "prs" / "pr-08.diff").read_text()[:4000]

    return [
        {
            "id": "official_payouts",
            "family": "official_demo",
            "state": "Help! My payouts have been failing for 3 days.",
            "questions": {
                "is_urgent": NoulQuestion(
                    instructions="Does this convey urgency?",
                    criteria={
                        "true": "the writer needs help immediately",
                        "false": "the message is calm or informational",
                    },
                ),
                "team": ChoiceQuestion(
                    instructions="Which team should handle this?",
                    criteria={
                        "billing": "payments, invoices, payouts, charges, refunds",
                        "technical": "bugs, outages, API errors, crashes",
                        "sales": "pricing, upgrades, and buying a plan",
                    },
                ),
                "frustration": ScoreQuestion(
                    instructions="How frustrated is the writer?",
                    criteria=["calm", "frustrated", "very angry"],
                ),
            },
        },
        {
            "id": "fact_sky_blue",
            "family": "fact",
            "state": "The sky is blue.",
            "questions": {
                "sky_is_blue": NoulQuestion(
                    instructions="The sky is described as blue.",
                    criteria={
                        "true": "the state says the sky is blue",
                        "false": "the state does not say the sky is blue",
                    },
                ),
                "sky_is_green": NoulQuestion(
                    instructions="The sky is described as green.",
                    criteria={
                        "true": "the state says the sky is green",
                        "false": "the state does not say the sky is green",
                    },
                ),
            },
        },
        {
            "id": "fact_arithmetic",
            "family": "fact",
            "state": "Two plus two equals four.",
            "questions": {
                "two_plus_two_is_four": NoulQuestion(
                    instructions="The state asserts that two plus two equals four.",
                    criteria={
                        "true": "the arithmetic claim 2+2=4 is present",
                        "false": "no such claim is present",
                    },
                ),
            },
        },
        {
            "id": "language_zulu",
            "family": "classification",
            "state": "sihamba ngokushesha",
            "questions": {
                "language": ChoiceQuestion(
                    instructions="What language is this phrase?",
                    criteria={
                        "english": "English words such as the, hello, payouts",
                        "zulu": "Zulu / isiZulu, e.g. sihamba, ngokushesha, sawubona",
                        "dutch": "Dutch words such as hallo, graag, uitkering",
                    },
                ),
            },
        },
        {
            "id": "intent_refund",
            "family": "intent",
            "state": "I was charged twice on my credit card. I want a refund today.",
            "questions": {
                "intent": ChoiceQuestion(
                    instructions="What is the customer's intent?",
                    criteria={
                        "refund": "get money back for a charge or payment",
                        "bug_report": "report software that does not work",
                        "upgrade": "buy or change a subscription plan",
                    },
                ),
            },
        },
        {
            "id": "tool_weather_city_missing",
            "family": "tool_selection",
            "state": "What's the weather?",
            "questions": {
                "has_city": NoulQuestion(
                    instructions="The user named a city or location.",
                    criteria={
                        "true": "a city, region, or place name is present",
                        "false": "no location is named",
                    },
                ),
                "tool": ChoiceQuestion(
                    instructions="Which tool should run next?",
                    criteria={
                        "ask_city": "ask the user which city before calling weather",
                        "get_weather": "call the weather API now; the city is already known",
                        "search_web": "search the public web for unrelated facts",
                    },
                ),
            },
        },
        {
            "id": "ci_kind_app_code",
            "family": "ci_change_kind",
            "state": math_diff,
            "questions": {
                "kind": ChoiceQuestion(instructions=KIND_Q, criteria=KIND_CRITERIA),
                "touches_src": NoulQuestion(
                    instructions="This diff changes files under src/.",
                    criteria={
                        "true": "a path under src/ is added, removed, or modified",
                        "false": "no src/ path appears in the diff",
                    },
                ),
            },
        },
        {
            "id": "ci_kind_ci_yaml",
            "family": "ci_change_kind",
            "state": ci_diff,
            "questions": {
                "kind": ChoiceQuestion(instructions=KIND_Q, criteria=KIND_CRITERIA),
                "touches_circleci": NoulQuestion(
                    instructions="This diff changes files under .circleci/.",
                    criteria={
                        "true": "a .circleci/ YAML path is added, removed, or modified",
                        "false": "no .circleci/ path appears in the diff",
                    },
                ),
            },
        },
        {
            "id": "ci_kind_docs",
            "family": "ci_change_kind",
            "state": docs_diff,
            "questions": {
                "kind": ChoiceQuestion(instructions=KIND_Q, criteria=KIND_CRITERIA),
                "touches_src": NoulQuestion(
                    instructions="This diff changes files under src/.",
                    criteria={
                        "true": "a path under src/ is added, removed, or modified",
                        "false": "no src/ path appears in the diff",
                    },
                ),
            },
        },
        {
            "id": "routing_payouts_only_choice",
            "family": "routing",
            "state": (
                "Ticket: payouts have failed for 3 days. Status: failed. "
                "Last error: bank_transfer_rejected. Amount: $1200."
            ),
            "questions": {
                "queue": ChoiceQuestion(
                    instructions="Route this ticket to one queue.",
                    criteria={
                        "payments": "payouts, transfers, banks, invoices, charges",
                        "infra": "servers, kubernetes, disk, CPU, networking",
                        "content": "docs, blog posts, marketing copy",
                    },
                ),
            },
        },
    ]


def noul_confident(p: float) -> bool:
    return p >= NOUL_HI or p <= NOUL_LO


def answer_record(ans) -> dict:
    if ans.type == "noul":
        p = float(ans.noul)
        return {
            "type": "noul",
            "noul": round(p, 4),
            "derived_confidence": round(abs(2 * p - 1), 4),
            "confident": noul_confident(p),
        }
    if ans.type == "choice":
        return {
            "type": "choice",
            "choice": ans.choice,
            "confidence": round(float(ans.confidence), 4),
            "confident": float(ans.confidence) >= CONF_THRESHOLD,
            "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
        }
    probs = ans.probabilities
    if isinstance(probs, dict):
        probs_out = {k: round(v, 4) for k, v in probs.items()}
    else:
        probs_out = [round(x, 4) for x in probs]
    return {
        "type": "score",
        "score": round(float(ans.score), 4),
        "confidence": round(float(ans.confidence), 4),
        "confident": float(ans.confidence) >= CONF_THRESHOLD,
        "probabilities": probs_out,
    }


def main() -> int:
    versions = load_versions()
    out_dir = Path(os.environ.get("BENCH_OUT", "bench-out"))
    out_dir.mkdir(parents=True, exist_ok=True)

    from strands_decider.infer import load_engine

    checkpoint = resolve_decider_path(versions)
    print(f"CHECKPOINT={checkpoint}", flush=True)
    print(f"HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}", flush=True)

    t0 = time.perf_counter()
    engine = load_engine(checkpoint, device="cpu")
    load_s = time.perf_counter() - t0
    print(f"LOAD_SECONDS={load_s:.3f}", flush=True)

    per = []
    totals = {"answers": 0, "confident": 0}
    by_family: dict[str, dict[str, int]] = {}

    for case in cases():
        t0 = time.perf_counter()
        resp = engine.ask(case["state"], case["questions"])
        elapsed = time.perf_counter() - t0
        answers = {name: answer_record(ans) for name, ans in resp.answers.items()}
        conf_n = sum(1 for a in answers.values() if a["confident"])
        totals["answers"] += len(answers)
        totals["confident"] += conf_n
        fam = by_family.setdefault(case["family"], {"answers": 0, "confident": 0})
        fam["answers"] += len(answers)
        fam["confident"] += conf_n
        entry = {
            "id": case["id"],
            "family": case["family"],
            "infer_seconds": round(elapsed, 3),
            "confident_answers": conf_n,
            "total_answers": len(answers),
            "answers": answers,
        }
        per.append(entry)
        bits = []
        for name, a in answers.items():
            if a["type"] == "noul":
                bits.append(f"{name} p={a['noul']:.3f} conf={a['confident']}")
            elif a["type"] == "choice":
                bits.append(f"{name}->{a['choice']} c={a['confidence']:.3f} conf={a['confident']}")
            else:
                bits.append(f"{name} s={a['score']:.2f} c={a['confidence']:.3f} conf={a['confident']}")
        print(f"{case['id']}: {conf_n}/{len(answers)}  " + "; ".join(bits), flush=True)

    rate = totals["confident"] / totals["answers"] if totals["answers"] else 0.0
    report = {
        "threshold": CONF_THRESHOLD,
        "noul_confident_rule": f"noul>={NOUL_HI} or noul<={NOUL_LO}",
        "load_seconds": round(load_s, 3),
        "decider_revision": versions["DECIDER_REVISION"],
        "hf_hub_offline": os.environ.get("HF_HUB_OFFLINE"),
        "answer_confidence_rate": round(rate, 4),
        "confident_answers": totals["confident"],
        "total_answers": totals["answers"],
        "by_family": {
            k: {**v, "rate": round(v["confident"] / v["answers"], 4) if v["answers"] else 0}
            for k, v in by_family.items()
        },
        "cases_with_any_confident": sum(1 for e in per if e["confident_answers"] > 0),
        "case_count": len(per),
        "per_case": per,
        "verdict": (
            "can_emit_high_confidence"
            if totals["confident"] > 0
            else "still_no_high_confidence"
        ),
    }
    path = out_dir / "high-conf-cases.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    summary = {k: report[k] for k in report if k != "per_case"}
    print(json.dumps(summary, indent=2))
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
