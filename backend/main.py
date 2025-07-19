"""FastAPI app integrating LangChain + OpenAI

Key features
------------
* Receives a user order request (e.g. "I need to order pizza for 20 people").
* A LangChain agent replies with any follow‑up questions it needs.
* The agent then invokes a tool call (implemented as an OpenAI function‑calling tool via LangChain) that researches the best 5 restaurants for the use case.
* Finally, it answers with the chosen restaurants' names & phone numbers in structured JSON.

How to run
~~~~~~~~~~
1. ``pip install fastapi uvicorn langchain~=0.2 langchain-openai python-dotenv``
2. ``export OPENAI_API_KEY="sk-..."`` (or create a ``.env`` file).
3. ``uvicorn main:app --reload``

For CLI testing:
~~~~~~~~~~
``python cli.py "I need sushi for 10 people"``
"""

from fastapi import FastAPI

from config import APP_TITLE, APP_VERSION
from api.routes import router


# ---------------------------------------------------------------------------
# FastAPI setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="AI-powered food ordering assistant using LangChain and OpenAI",
    openapi_tags=[
        {
            "name": "orders",
            "description": "Operations with food orders. Send your order request and get AI-powered restaurant recommendations."
        },
        {
            "name": "health",
            "description": "Health check endpoints for monitoring and deployment."
        }
    ]
)

# Include all routes
app.include_router(router)
