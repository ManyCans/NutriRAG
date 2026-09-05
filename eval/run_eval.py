"""
Run the golden eval set through NutriRAG, score answer quality with an
LLM-as-judge call, and write a structured report combining quality +
latency + cost. This report is what CI compares against a committed
baseline to gate regressions.

Usage:
    python eval/run_eval.py --out eval/eval_report.json

Requires GROQ_API_KEY set (same as the app itself).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.rag import answer_query          # noqa: E402  (use rag_patched.py once merged in)
from src.agent import llm_caller          # noqa: E402  (use agent_patched.py once merged in)
from src.observability import summarize   # noqa: E402

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

JUDGE_MODEL = "openai/gpt-oss-20b"
_judge_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def judge_answer(query: str, answer: str, must_contain_facts: list[str]) -> dict:
    """LLM-as-judge: ask a fresh model call whether the answer covers the
    required facts. Returns {"pass": bool, "reasoning": str}."""
    facts_list = "\n".join(f"- {f}" for f in must_contain_facts)
    judge_prompt = f"""You are grading an AI assistant's answer to a nutrition question.

Question: {query}

Answer given:
{answer}

The answer should cover these facts/criteria:
{facts_list}

Respond in strict JSON only, no markdown fences:
{{"pass": true or false, "reasoning": "one sentence"}}
"""
    resp = _judge_client.chat.completions.create(
        messages=[{"role": "user", "content": judge_prompt}],
        model=JUDGE_MODEL,
        temperature=0,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"pass": False, "reasoning": f"Judge response not valid JSON: {raw[:200]}"}


def run_eval(golden_set_path: Path) -> dict:
    golden_set = json.loads(golden_set_path.read_text())
    results = []

    for item in golden_set:
        result = answer_query(item["query"], llm_caller)
        verdict = judge_answer(item["query"], result["answer"], item["must_contain_facts"])
        results.append({
            "id": item["id"],
            "query": item["query"],
            "pass": verdict["pass"],
            "reasoning": verdict["reasoning"],
        })
        time.sleep(0.3)  # light rate-limit courtesy

    pass_count = sum(1 for r in results if r["pass"])
    quality = {
        "pass_rate": round(pass_count / len(results), 3) if results else 0.0,
        "num_questions": len(results),
        "results": results,
    }

    perf = summarize()  # latency (p50/p95) + cost, pulled from the trace DB

    return {
        "timestamp": time.time(),
        "quality": quality,
        "performance": perf,
    }


def check_regression(report: dict, baseline: dict, quality_tolerance: float = 0.05) -> list[str]:
    """Compare a fresh report against a committed baseline. Returns a list
    of failure reasons; empty list means no regression."""
    failures = []

    new_pass = report["quality"]["pass_rate"]
    old_pass = baseline["quality"]["pass_rate"]
    if new_pass < old_pass - quality_tolerance:
        failures.append(
            f"Quality regression: pass_rate {new_pass} vs baseline {old_pass} "
            f"(tolerance {quality_tolerance})"
        )

    new_llm_p95 = report["performance"]["latency"].get("llm_generate", {}).get("p95_ms", 0)
    old_llm_p95 = baseline["performance"]["latency"].get("llm_generate", {}).get("p95_ms", 0)
    if old_llm_p95 and new_llm_p95 > old_llm_p95 * 1.5:
        failures.append(
            f"Latency regression: llm_generate p95 {new_llm_p95}ms vs baseline {old_llm_p95}ms"
        )

    new_cost = report["performance"]["cost"]["avg_usd_per_request"]
    old_cost = baseline["performance"]["cost"]["avg_usd_per_request"]
    if old_cost and new_cost > old_cost * 1.5:
        failures.append(
            f"Cost regression: avg cost/request ${new_cost} vs baseline ${old_cost}"
        )

    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="eval/golden_set.json")
    parser.add_argument("--out", default="eval/eval_report.json")
    parser.add_argument("--baseline", default="eval/eval_baseline.json")
    parser.add_argument("--gate", action="store_true", help="Exit nonzero on regression")
    args = parser.parse_args()

    report = run_eval(Path(args.golden_set))
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"Wrote {args.out} — pass_rate={report['quality']['pass_rate']}")

    baseline_path = Path(args.baseline)
    if args.gate:
        if not baseline_path.exists():
            print(f"No baseline at {baseline_path} yet — writing this run as the new baseline.")
            baseline_path.write_text(json.dumps(report, indent=2))
        else:
            baseline = json.loads(baseline_path.read_text())
            failures = check_regression(report, baseline)
            if failures:
                print("REGRESSION DETECTED:")
                for f in failures:
                    print(f"  - {f}")
                sys.exit(1)
            print("No regression detected.")