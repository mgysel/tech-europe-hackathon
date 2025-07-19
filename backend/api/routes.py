"""FastAPI routes for the AI Food-Ordering Assistant."""

from fastapi import APIRouter

from schemas.schemas import OrderRequest, OrderResponse
from services.agent import agent_service

# Create router for order-related endpoints
router = APIRouter()


@router.post("/order", response_model=OrderResponse, tags=["orders"])
async def place_order(req: OrderRequest) -> OrderResponse:
    """
    Process a food order request through the AI agent.
    
    This endpoint allows you to:
    - Send a food order request with conversation history
    - Get AI-powered restaurant recommendations
    - Maintain conversation context across multiple calls using session_id
    
    The AI agent will:
    1. Ask follow-up questions if needed
    2. Research the best 5 restaurants for your use case
    3. Return restaurant names and phone numbers in structured format
    """
    return await agent_service.process_order(req)


@router.get("/healthz", tags=["health"])
def health() -> dict[str, str]:
    """
    Basic liveness probe compatible with Kubernetes etc.
    
    Returns a simple status check to verify the service is running.
    """
    return {"status": "ok"} 