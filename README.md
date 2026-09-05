# Integrating observability into NutriRAG

## 1. Drop in the new file
Copy `src/observability.py` into your `src/` folder as-is. Nothing to edit.

## 2. Merge two small diffs
- `src/rag_patched.py` shows the exact changes to make in your real `src/rag.py`:
  import `traced`/`new_request_id`, add `@traced("retrieve")` and
  `@traced("build_context")`, call `new_request_id()` once at the top of
  `answer_query()`.
- `src/agent_patched.py` shows the same for `llm_caller()` in `src/agent.py`:
  add `@traced("llm_generate")`, and after the Groq call, pull
  `chat_completion.usage` and call `log_llm_usage(...)`.

These are small, surgical additions — nothing else in either file changes.

## 3. Run the app as normal
`streamlit run app/streamlit_app.py` — traces now accumulate in
`data/traces.db` (created automatically) with zero changes needed to the
Streamlit file itself.

## 4. Check what you're getting
```python
from src.observability import summarize
print(summarize())
# {'latency': {'retrieve': {'p50_ms': 12.3, 'p95_ms': 41.0, 'count': 8}, ...},
#  'cost': {'total_usd': 0.0021, 'avg_usd_per_request': 0.00026, 'num_requests': 8}}
```

## 5. Eval harness
- `eval/golden_set.json` — starter set of 5 questions. Expand this to 20-30
  as you find real edge cases (ambiguous questions, questions your corpus
  doesn't cover, adversarial phrasing).
- `eval/run_eval.py` — runs the golden set through your real pipeline,
  LLM-judges each answer, and writes `eval/eval_report.json` combining
  quality + latency + cost:
  ```
  python eval/run_eval.py --gate
  ```
  First run with `--gate` writes the baseline. Every run after that compares
  against it and exits nonzero on regression (quality drop beyond 5
  percentage points, or latency/cost more than 1.5x baseline — tune these
  thresholds in `check_regression()`).

## 6. CI
`.github/workflows/eval-gate.yml` runs the above on every PR and push to
main, uploads the report as a build artifact, and auto-commits the new
baseline on main after a passing run. Add `GROQ_API_KEY` (and `FDC_API_KEY`
if the nutrient lookup tool gets exercised in eval) as repo secrets.

## What this gets you for interviews
- A real answer to "how do you monitor a RAG system in production" backed
  by actual p50/p95 numbers from your own traffic.
- A real answer to "how do you catch quality regressions before they ship"
  — the CI gate, not just a description of one.
- A real cost-per-request number, which almost nobody in a portfolio
  project can produce on demand.

## Honest gaps to disclose if asked
- Trace storage is a single local SQLite file — fine for a portfolio
  project, but you'd talk through what changes for multi-instance
  production (centralized store, OpenTelemetry collector, etc.) if asked.
- The LLM-as-judge scorer is a good starting point but is itself an LLM
  call with its own variance — worth mentioning you'd add a human-reviewed
  sample check periodically in a real system.