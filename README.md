# 🥗 NutriRAG — Nutrition & Diet Research Assistant

NutriRAG is a **Retrieval-Augmented Generation (RAG)** application that answers nutrition and diet-related questions using trusted public health resources. The system combines **semantic search** with **Groq-powered LLM inference** to generate context-aware responses grounded in reliable nutrition documents.

The project ingests nutrition documents, converts them into vector embeddings using **ChromaDB**, retrieves the most relevant context for a user's query, and generates accurate responses using Groq's LLM.

---

## ✨ Features

* 📄 Ingests nutrition documents from trusted public health sources.
* 🔍 Semantic search using **ChromaDB** vector database.
* 🤖 Fast response generation powered by **Groq LLM**.
* 📚 Context-aware Retrieval-Augmented Generation (RAG).
* 🌐 Streamlit web interface for interactive question answering.
* 📊 Evaluation pipeline for testing retrieval and response quality.

---

## 🛠 Tech Stack

* **Language:** Python
* **LLM:** Groq
* **Vector Database:** ChromaDB
* **Framework:** LangChain
* **Embeddings:** Sentence Transformers
* **Frontend:** Streamlit

---

## 📂 Data Sources

* WHO Nutrition Fact Sheets
* USDA Dietary Guidelines
* USDA FoodData Central

All information comes from publicly available and trusted nutrition resources.

---

## 📁 Project Structure

```text
nutrirag/
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/
│   └── processed/
├── eval/
│   ├── eval_set.jsonl
│   └── run_eval.py
├── src/
│   ├── agent.py
│   ├── ingest.py
│   ├── rag.py
│   ├── scrape_who.py
│   └── tools/
│       ├── nutrient_lookup.py
│       └── web_search.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
git clone <repository-url>
cd nutrirag

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## 🚀 Running the Project

### 1. Download WHO documents

```bash
python src/scrape_who.py
```

### 2. Build the Vector Database

```bash
python src/ingest.py
```

### 3. Launch the Streamlit App

```bash
streamlit run app/streamlit_app.py
```

### 4. Run Evaluation

```bash
python eval/run_eval.py
```

---

## 🔄 RAG Pipeline

1. Collect nutrition documents from WHO and USDA sources.
2. Clean and split documents into chunks.
3. Generate embeddings for each chunk.
4. Store embeddings in **ChromaDB**.
5. Retrieve the most relevant chunks for a user query.
6. Pass retrieved context to **Groq LLM**.
7. Generate an accurate, context-aware response.

---

## 📈 Future Improvements

* Add citation highlighting for retrieved passages.
* Support multiple embedding models.
* Enable document uploads for custom nutrition datasets.
* Add conversation memory.
* Improve retrieval using reranking.
* Deploy the application on Streamlit Cloud.

---

## ⚠️ Disclaimer

This project is intended for educational and portfolio purposes only. It provides evidence-based nutritional information from public sources and should not be considered medical or dietary advice. Always consult a qualified healthcare professional for personalized recommendations.
