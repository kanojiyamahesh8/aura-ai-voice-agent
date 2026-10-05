from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.orders import get_order_details


app = FastAPI(
    title="Aura Skincare AI Voice Agent",
    description="Backend API for the Aura Skincare AI customer support agent",
    version="1.0.0"
)


class OrderRequest(BaseModel):
    order_id: str = Field(min_length=1)


class OrderResponse(BaseModel):
    order_id: str
    customer: str
    product: str
    value: int
    status: str

    carrier: Optional[str] = None
    tracking: Optional[str] = None
    expected: Optional[str] = None
    delivered: Optional[str] = None
    ordered: Optional[str] = None
    cancellation_eligible: Optional[bool] = None


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/orders/details", response_model=OrderResponse)
def order_details(request: OrderRequest):

    order = get_order_details(request.order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"Order {request.order_id} was not found."
        )

    return order