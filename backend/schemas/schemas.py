from typing import List
from pydantic import BaseModel, Field


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


class CustomVariable(BaseModel):
    key: str
    value: str


class SynthflowCallRequest(BaseModel):
    phone: str
    name: str
    sourcing_request: str 