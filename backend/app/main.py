from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.orders import get_order_details


app = FastAPI(
    title="Aura Skincare AI Voice Agent",
    description="Backend API for the Aura Skincare AI customer support agent",
    version="1.0.0"
)


class OrderRequest(BaseModel):
    order_id: str


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/orders/details")
def order_details(request: OrderRequest):

    order = get_order_details(request.order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"Order {request.order_id} was not found."
        )

    return order
