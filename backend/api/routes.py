"""FastAPI routes for the AI Food-Ordering Assistant."""

from fastapi import APIRouter

from schemas.schemas import OrderRequest, OrderResponse
from services.agent import agent_service

# Create router for order-related endpoints
router = APIRouter()


@router.post("/order", response_model=OrderResponse)
async def place_order(req: OrderRequest) -> OrderResponse:
    """Process a food order request through the AI agent."""
    return await agent_service.process_order(req)


@router.get("/healthz")
def health() -> dict[str, str]:
    """Basic liveness probe compatible with Kubernetes etc."""
    return {"status": "ok"} 