# Integrating observability into NutriRAG


## 1. Run the app
`streamlit run app/streamlit_app.py` — traces now accumulate in
`data/traces.db` (created automatically) with zero changes needed to the
Streamlit file itself.

## 2. Check what you're getting
```python
from src.observability import summarize
print(summarize())
# {'latency': {'retrieve': {'p50_ms': 12.3, 'p95_ms': 41.0, 'count': 8}, ...},
#  'cost': {'total_usd': 0.0021, 'avg_usd_per_request': 0.00026, 'num_requests': 8}}
```

## 3. Eval harness
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


## Honest gaps to disclose if asked
- Trace storage is a single local SQLite file — fine for a portfolio
  project, but you'd talk through what changes for multi-instance
  production (centralized store, OpenTelemetry collector, etc.) if asked.
- The LLM-as-judge scorer is a good starting point but is itself an LLM
  call with its own variance — worth mentioning you'd add a human-reviewed
  sample check periodically in a real system.