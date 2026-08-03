# NutriRAG — Nutrition & Diet Research Assistant

A RAG + tool-using agent that answers nutrition and diet questions by retrieving
from public health sources (WHO fact sheets, USDA Dietary Guidelines) and
falling back to tools (nutrient lookup, web search) when a question needs
computation or freshness that retrieval alone can't provide.

## Why this project

Demonstrates a full, practical LLM application stack:
- Document ingestion + chunking from real-world public sources
- Embedding + vector search (Chroma)
- An agent layer that decides between "answer from retrieved docs" vs
  "call a tool" (nutrient calculator, web search)
- A small evaluation harness (retrieval + answer quality)
- A minimal demo UI (Streamlit)

## Data sources

All sources are public/government (no licensing required):
- WHO fact sheets (nutrition-related subset — see `data/raw/who/SOURCES.md`)
- USDA Dietary Guidelines for Americans
- USDA FoodData Central (used as a live lookup tool, not static RAG text)

## Project structure

```
nutrirag/
├── data/
│   ├── raw/            # scraped/downloaded source documents, untouched
│   └── processed/      # cleaned, chunked documents ready for embedding
├── src/
│   ├── scrape_who.py       # fetch + parse WHO fact sheets
│   ├── ingest.py           # chunk + embed documents into the vector store
│   ├── agent.py            # agent loop: routes between RAG and tools
│   ├── tools/
│   │   ├── nutrient_lookup.py   # USDA FoodData Central query tool
│   │   └── web_search.py        # web search tool for freshness
│   └── rag.py               # retrieval + generation logic
├── eval/
│   ├── eval_set.jsonl       # ~15 test questions with expected sources/answers
│   └── run_eval.py          # scores retrieval + answer quality
├── app/
│   └── streamlit_app.py     # demo chat UI
├── notebooks/                # scratch/exploration
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline order

1. `python src/scrape_who.py` — pulls fact sheet text into `data/raw/who/`
2. `python src/ingest.py` — chunks + embeds everything into `data/processed/` and the vector store
3. `python app/streamlit_app.py` — run the demo
4. `python eval/run_eval.py` — score retrieval/answer quality against `eval_set.jsonl`

## Design notes (fill in as you build)

- **Chunking strategy:** _why you chose it_
- **Vector store:** Chroma (local, no server needed for a weekend project)
- **Agent routing:** _how the agent decides RAG vs tool call_
- **What I'd do with more time:** _tradeoffs you'd revisit_

## Content note

Answers are framed as "guidelines/evidence suggest X," not personalized medical
or dietary advice. This is a portfolio/demo project, not a substitute for
professional nutrition guidance.
