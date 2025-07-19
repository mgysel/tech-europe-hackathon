"""FastAPI routes for the AI Food-Ordering Assistant."""

from fastapi import APIRouter

from schemas.schemas import OrderRequest, OrderResponse
from services.agent import agent_service

# Create router for order-related endpoints
router = APIRouter()


@router.post("/order", response_model=OrderResponse, tags=["orders"])
async def place_order(req: OrderRequest) -> OrderResponse:
    """
    Process a food order request through the AI agent using Firestore task data.
    
    This endpoint allows you to:
    - Provide a task_id to retrieve conversation history from Firestore
    - Get AI-powered restaurant recommendations based on the task messages
    
    The AI agent will:
    1. Fetch all messages for the given task_id from Firestore
    2. Process the conversation history to understand the order requirements
    3. Ask follow-up questions if needed
    4. Research the best 5 restaurants for your use case
    5. Return restaurant names and phone numbers in structured format
    
    Firestore Structure:
    - tasks/{task_id}/messages/{message_id}
    - Messages should have 'user', 'ai', or 'message' fields
    """
    return await agent_service.process_order(req)


@router.get("/healthz", tags=["health"])
def health() -> dict[str, str]:
    """
    Basic liveness probe compatible with Kubernetes etc.
    
    Returns a simple status check to verify the service is running.
    """
    return {"status": "ok"} 