"""
Tool: web search, for questions needing freshness beyond the static corpus
(e.g. "latest research on X"). Plug in whichever search API you have access
to (Tavily, Serper, Bing, etc.) — this is a thin interface so agent.py
doesn't care which one you pick.
"""


def web_search(query: str) -> dict:
    """
    Replace this stub with a real API call, e.g.:

        import requests
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 3},
        )
        return resp.json()
    """
    raise NotImplementedError("Wire up a web search provider here (Tavily/Serper/Bing).")


TOOL_SCHEMA = {
    "name": "web_search",
    "description": (
        "Search the web for current information not covered by the static "
        "nutrition document corpus — e.g. recent studies or news."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"],
    },
}
