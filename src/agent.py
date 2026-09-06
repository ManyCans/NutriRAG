"""
Only the llm_caller() function changes — everything else in your agent.py
stays as-is. Shown here in isolation for clarity; drop this back into your
real agent.py in place of the existing llm_caller.

CHANGES vs your original:
  - @traced("llm_generate") on llm_caller
  - after the Groq call, pull chat_completion.usage and call log_llm_usage()
    to record prompt/completion tokens and estimated cost against the
    current request_id (set by new_request_id() in rag.answer_query)
"""
import os

from groq import Groq
from dotenv import load_dotenv

from src.observability import traced, log_llm_usage

load_dotenv()

llm_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL_NAME = "openai/gpt-oss-20b"


@traced("llm_generate")
def llm_caller(system_query: str, input_query: str, chat_history: list):
    chat_completion = llm_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_query},
            *chat_history[-3:-1],
            {"role": "user", "content": input_query},
        ],
        model=MODEL_NAME,
    )
    usage = getattr(chat_completion, "usage", None)
    if usage is not None:
        log_llm_usage(
            model=MODEL_NAME,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )

    return chat_completion.choices[0].message.content
