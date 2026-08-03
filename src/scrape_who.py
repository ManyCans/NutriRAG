"""
Fetch and parse WHO nutrition-related fact sheets into structured JSON
documents for downstream chunking/embedding.

Usage:
    python src/scrape_who.py
"""
import json
import time
from pathlib import Path

import requests
import trafilatura

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "who"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Slug -> display title. Add/remove entries here as needed.
FACT_SHEETS = {
    "healthy-diet": "Healthy diet",
    "obesity-and-overweight": "Obesity and overweight",
    "malnutrition": "Malnutrition",
    "sodium-reduction": "Sodium reduction",
    "trans-fat": "Trans fat",
    "sugars-and-dental-caries": "Sugars and dental caries",
    "infant-and-young-child-feeding": "Infant and young child feeding",
    "anaemia": "Anaemia",
    "food-additives": "Food additives",
    "pesticide-residues-in-food": "Pesticide residues in food",
}

BASE_URL = "https://www.who.int/news-room/fact-sheets/detail/{}"
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio-project RAG demo)"}


def fetch_fact_sheet(slug: str, title: str) -> dict | None:
    url = BASE_URL.format(slug)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        print(f"  [!] failed ({resp.status_code}): {url}")
        return None

    # trafilatura strips nav/footer/boilerplate and returns clean article text
    text = trafilatura.extract(resp.text, include_tables=True, favor_recall=True)
    if not text:
        print(f"  [!] no extractable content: {url}")
        return None

    return {
        "title": title,
        "slug": slug,
        "url": url,
        "source": "WHO",
        "category": "nutrition",
        "text": text,
    }


def main():
    documents = []
    for slug, title in FACT_SHEETS.items():
        print(f"Fetching: {title} ({slug})")
        doc = fetch_fact_sheet(slug, title)
        if doc:
            out_path = RAW_DIR / f"{slug}.json"
            out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            documents.append(doc)
        time.sleep(1)  # be polite between requests

    print(f"\nSaved {len(documents)}/{len(FACT_SHEETS)} fact sheets to {RAW_DIR}")


if __name__ == "__main__":
    main()
