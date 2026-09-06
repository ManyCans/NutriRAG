"""
Minimal Streamlit demo for NutriRAG.

Run with:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from src.rag import answer_query
from src.agent import llm_caller

st.set_page_config(page_title="NutriRAG", page_icon="🥗")
st.title("🥗 NutriRAG — Nutrition & Diet Assistant")
st.caption("Answers grounded in WHO fact sheets and USDA guidelines. Only General Health Advice.")

if "history" not in st.session_state:
    st.session_state.history = []

query = st.chat_input("Ask a nutrition question...")

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if query:
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    result = answer_query(query, llm_caller,3,st.session_state.history)

    with st.chat_message("assistant"):
        st.write(result["answer"])
        if result["sources"]:
            st.caption("Sources: " + ", ".join(result["sources"]))

    st.session_state.history.append({"role": "assistant", "content": result["answer"]})
