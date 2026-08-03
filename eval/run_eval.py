"""
Simple eval harness: checks whether retrieval surfaces the expected source,
and (for tool-type questions) whether the agent picks the right tool.

Usage:
    python eval/run_eval.py
"""
import json
from pathlib import Path

from src.rag import retrieve

EVAL_SET = Path(__file__).parent / "eval_set.jsonl"


def load_eval_set() -> list[dict]:
    return [json.loads(line) for line in EVAL_SET.read_text().splitlines() if line.strip()]


def score_rag_question(item: dict, k: int = 4) -> bool:
    hits = retrieve(item["question"], k=k)
    urls = [h["metadata"]["url"] for h in hits]
    return any(item["expected_source_contains"] in url for url in urls)


def main():
    items = load_eval_set()
    rag_items = [i for i in items if i["type"] == "rag"]
    tool_items = [i for i in items if i["type"] == "tool"]

    rag_correct = sum(score_rag_question(i) for i in rag_items)
    print(f"RAG retrieval: {rag_correct}/{len(rag_items)} correct source in top-k")

    # Tool-routing eval requires wiring up your actual agent/LLM call —
    # left as a manual step until agent.py's llm_call_fn is implemented.
    print(f"Tool-routing questions: {len(tool_items)} (evaluate manually via agent.py once wired up)")


if __name__ == "__main__":
    main()
