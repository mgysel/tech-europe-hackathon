# main.py
"""FastAPI app integrating LangChain + OpenAI

Key features
------------
* Receives a user order request (e.g. "I need to order pizza for 20 people").
* A LangChain agent replies with any follow‑up questions it needs.
* The agent then invokes a tool call (implemented as an OpenAI function‑calling tool via LangChain) that researches the best 5 restaurants for the use case.
* Finally, it answers with the chosen restaurants’ names & phone numbers in structured JSON.

How to run
~~~~~~~~~~
1. ``pip install fastapi uvicorn langchain~=0.2 langchain-openai python-dotenv``
2. ``export OPENAI_API_KEY="sk-..."`` (or create a ``.env`` file).
3. ``uvicorn main:app --reload``
"""

from __future__ import annotations

import os
import uuid
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_openai_functions_agent
from langchain.agents.agent import AgentExecutor
from langchain.tools import tool

# ---------------------------------------------------------------------------
# Environment & settings
# ---------------------------------------------------------------------------
load_dotenv()  # Loads OPENAI_API_KEY from .env if present

LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.3))


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
        import json

        return json.loads(response.content)
    except Exception as exc:  # noqa: BLE001
        # Fallback: wrap raw content so the caller still gets data.
        return [{"rank": i + 1, "name": line, "phone": "", "notes": "LLM raw"}
                for i, line in enumerate(response.content.splitlines()[:5])]


# ---------------------------------------------------------------------------
# LangChain Agent
# ---------------------------------------------------------------------------
SYSTEM_TEMPLATE = (
    "You are an expert food‑order assistant. Your job is to help the user place "
    "group food orders. Start by asking any follow‑up questions needed to fully "
    "specify the order (dietary restrictions, budget, location, delivery time, "
    "etc.). When you have enough info, call `search_restaurants` with a short "
    "query containing cuisine, size, and location. After the tool returns, "
    "reply **only** with the restaurant list in pretty JSON."
)

llm = ChatOpenAI(model_name=LLM_MODEL, temperature=TEMPERATURE)

# A single reusable tool list (could include more later) ---------------------
TOOLS = [search_restaurants_tool]


# ---------------------------------------------------------------------------
# FastAPI setup
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Food‑Ordering Assistant")


class Message(BaseModel):
    user: str | None = Field(None, description="User message")
    ai: str | None = Field(None, description="AI response message")

class OrderRequest(BaseModel):
    messages: List[Message] = Field(..., example=[
        {"user": "I want pizzas for 30 people by tomorrow evening"},
        {"ai": "Could you please provide me with the following details?\n\n1. Location (city or area) for delivery?\n2. Any dietary restrictions (e.g., vegetarian, gluten-free)?\n3. Budget per person or total budget for the order?\n4. Preferred delivery time tomorrow evening?"},
        {"user": "To Schmidstr. 2F in Berlin. There are no dietary restrictions. It should cost $10/person or less. I want the delivery for 7pm tomorrow evening."}
    ])
    session_id: str | None = Field(
        default=None,
        description="UUID to maintain conversation context across calls. If absent a new session is created.",
    )


class OrderResponse(BaseModel):
    session_id: str
    response: str


# In‑memory session storage: session_id -> ConversationBufferMemory ----------
_SESSION_STORE: dict[str, ConversationBufferMemory] = {}


def get_agent(session_id: str) -> tuple[ConversationBufferMemory, AgentExecutor]:
    """Return (memory, agent) for a given session, creating them on first use."""
    if session_id not in _SESSION_STORE:
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        _SESSION_STORE[session_id] = memory
    memory = _SESSION_STORE[session_id]

    # Create the agent with the system message as a prompt
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(
        llm=llm,
        tools=TOOLS,
        prompt=prompt,
    )
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        memory=memory,
        verbose=False,
    )
    return memory, agent_executor


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/order", response_model=OrderResponse)
async def place_order(req: OrderRequest):
    # Create a new session ID if needed
    session_id = req.session_id or str(uuid.uuid4())
    memory, agent = get_agent(session_id)

    try:
        # Clear existing memory for this session
        memory.clear()
        
        # Process conversation history
        for i, msg in enumerate(req.messages):
            if msg.user:
                # Add user message to memory
                memory.chat_memory.add_user_message(msg.user)
                
                # If this is the last message, invoke the agent
                if i == len(req.messages) - 1:
                    result = agent.invoke({"input": msg.user})
                    return OrderResponse(session_id=session_id, response=str(result["output"]))
            
            if msg.ai:
                # Add AI response to memory
                memory.chat_memory.add_ai_message(msg.ai)
        
        # If no user message in the last item, return an error
        raise HTTPException(status_code=400, detail="Last message must be from user")
        
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/healthz")
def health() -> dict[str, str]:
    """Basic liveness probe compatible with Kubernetes etc."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Optional: CLI helper (python main.py "I need sushi for 10")
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import argparse, asyncio  # noqa: E401

    parser = argparse.ArgumentParser(description="Test the ordering agent from CLI")
    parser.add_argument("message", type=str, nargs="+", help="initial user message")
    args = parser.parse_args()
    msg = " ".join(args.message)

    test_session = str(uuid.uuid4())
    memory, agent = get_agent(test_session)
    out = agent.invoke({"input": msg})
    print(out["output"])
