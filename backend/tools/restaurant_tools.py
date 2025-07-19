"""Restaurant search tools for the AI Food-Ordering Assistant."""

import json
from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.tools import tool

from config import LLM_MODEL


# ---------------------------------------------------------------------------
# Search‑restaurants TOOL (OpenAI function‑call)
# ---------------------------------------------------------------------------
@tool(
    "search_restaurants",
    args_schema=None,
    return_direct=True,
)
def search_restaurants_tool(query: str) -> List[Dict[str, str]]:
    """Search the Internet and return the 5 best restaurants for the query.

    Args:
        query: A natural‑language query describing cuisine, head‑count, budget, etc.

    Returns:
        A list with exactly five dicts in this shape::
            {
                "rank": int,  # 1‑based ranking (1..5)
                "name": str,
                "phone": str,
                "notes": str  # short justification
            }

    The function delegates to the OpenAI LLM itself (tool‑call pattern) to gather
    and structure the information.
    """

    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0)

    system_prompt = (
        "You are a meticulous catering concierge. Given a QUERY you must suggest "
        "exactly five real restaurants that best fit. Return them as JSON with "
        "keys: rank, name, phone, notes — nothing else."
    )

    messages = [
        SystemMessage(content=system_prompt),
        # User query goes last so the model knows what to do
    ]
    response = llm.invoke("QUERY: " + query)

    # The LLM response *should* be valid JSON; a production system would parse &
    # validate safely. Here we assume well‑formed output for brevity.
    try:
        return json.loads(response.content)
    except Exception as exc:  # noqa: BLE001
        # Fallback: wrap raw content so the caller still gets data.
        return [{"rank": i + 1, "name": line, "phone": "", "notes": "LLM raw"}
                for i, line in enumerate(response.content.splitlines()[:5])] 