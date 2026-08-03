"""
Minimal Streamlit demo for NutriRAG.

Run with:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from src.rag import answer_query  # noqa: E402
from src.agent import llm_caller

st.set_page_config(page_title="NutriRAG", page_icon="🥗")
st.title("🥗 NutriRAG — Nutrition & Diet Assistant")
st.caption("Answers grounded in WHO fact sheets and USDA guidelines. Not personalized medical advice.")


# def dummy_llm_call(system_prompt: str, user_prompt: str) -> str:
#     """Placeholder — replace with your actual Anthropic API call."""
#     return "Wire up your LLM call in dummy_llm_call() / rag.py's llm_call_fn."


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

    # result = answer_query(query, dummy_llm_call)
    result = answer_query(query, llm_caller)

    with st.chat_message("assistant"):
        st.write(result["answer"])
        if result["sources"]:
            st.caption("Sources: " + ", ".join(result["sources"]))

    st.session_state.history.append({"role": "assistant", "content": result["answer"]})
