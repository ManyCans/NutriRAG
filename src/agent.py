"""
Agent loop: decides per-query whether to answer from the RAG corpus or call
a tool (nutrient lookup, web search), then synthesizes a final answer.

This is hand-rolled rather than framework-based on purpose — it keeps the
control flow visible, which is a good thing to point to in an interview.
"""
from src.rag import answer_query, retrieve, build_context, SYSTEM_PROMPT
from src.tools.nutrient_lookup import lookup_food, TOOL_SCHEMA as NUTRIENT_TOOL_SCHEMA
from src.tools.web_search import web_search, TOOL_SCHEMA as WEB_SEARCH_TOOL_SCHEMA
import os
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

MAX_ITERATIONS = 3

TOOLS = [NUTRIENT_TOOL_SCHEMA, WEB_SEARCH_TOOL_SCHEMA]

TOOL_FUNCTIONS = {
    "nutrient_lookup": lambda args: lookup_food(args["food_name"]),
    "web_search": lambda args: web_search(args["query"]),
}


def run_agent(query: str, llm_call_fn) -> dict:
    """
    llm_call_fn: function(messages, tools) -> response object from your LLM
    client (Anthropic API), following the standard tool-use response shape
    (content blocks of type 'text' or 'tool_use').

    This is intentionally left as an interface rather than hardcoding the
    Anthropic SDK call, so you can wire it up however you're calling the API
    in this project.
    """
    messages = [{"role": "user", "content": query}]
    sources_used = []

    for _ in range(MAX_ITERATIONS):
        response = llm_call_fn(messages, TOOLS, SYSTEM_PROMPT)

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            # Model answered directly (should mean it used RAG context you
            # fed it, or determined no tool was needed)
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"answer": text, "sources": sources_used}

        # Execute each requested tool call and feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in tool_use_blocks:
            fn = TOOL_FUNCTIONS.get(block.name)
            result = fn(block.input) if fn else {"error": f"Unknown tool {block.name}"}
            sources_used.append(block.name)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })
        messages.append({"role": "user", "content": tool_results})

    return {"answer": "Reached max iterations without a final answer.", "sources": sources_used}


def route_and_answer(query: str, llm_call_fn) -> dict:
    """
    Simpler alternative to a full tool-use loop: retrieve RAG context first,
    let the model decide inline whether it also needs a tool. Use this if you
    want a lighter-weight agent for the weekend build, and upgrade to
    run_agent() above if you have time for the full loop.
    """
    hits = retrieve(query)
    context = build_context(hits)
    return answer_query(query, llm_call_fn)


llm_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def llm_caller(system_query:str, input_query:str,chat_history:list):
    chat_completion = llm_client.chat.completions.create(
        messages = [
            {"role": "system", "content": system_query},
            *chat_history[-3:-1],
            {"role": "user", "content": input_query}
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content