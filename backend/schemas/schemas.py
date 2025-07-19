from typing import List
from pydantic import BaseModel, Field


class Message(BaseModel):
    user: str | None = Field(
        None, 
        description="User message in the conversation",
        example="I want pizzas for 30 people by tomorrow evening"
    )
    ai: str | None = Field(
        None, 
        description="AI response message in the conversation",
        example="Could you please provide me with the following details?\n\n1. Location (city or area) for delivery?\n2. Any dietary restrictions (e.g., vegetarian, gluten-free)?\n3. Budget per person or total budget for the order?\n4. Preferred delivery time tomorrow evening?"
    )


class OrderRequest(BaseModel):
    task_id: str = Field(
        ..., 
        description="Firestore task ID to retrieve messages from",
        example="task_abc123def456"
    )


class OrderResponse(BaseModel):
    session_id: str = Field(
        description="UUID of the conversation session",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    response: str = Field(
        description="AI response with restaurant recommendations or follow-up questions",
        example="Based on your requirements, here are the top 5 pizza restaurants in Berlin that can deliver to Schmidstr. 2F:\n\n1. Pizza Palace - (030) 1234-5678\n2. Bella Pizza - (030) 2345-6789\n3. Roma Pizza - (030) 3456-7890\n4. Napoli Express - (030) 4567-8901\n5. Pizza Express - (030) 5678-9012\n\nAll restaurants offer delivery for 30 people within your budget of $10/person."
    ) 


class CustomVariable(BaseModel):
    key: str
    value: str


class SynthflowCallRequest(BaseModel):
    phone: str
    name: str
    sourcing_request: str 