import os

from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from livekit import api

from pydantic import BaseModel, Field

from app.orders import get_order_details
from app.agent import run_agent

from pathlib import Path
from fastapi.staticfiles import StaticFiles


load_dotenv(".env.local")


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


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    response = run_agent(request.message)

    return {
        "response": response
    }


@app.get("/token")
async def get_livekit_token():

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are not configured."
        )

    room_name = "aura-room"
    agent_name = "aura-ai"

    # --------------------------------------------------------
    # Create a LiveKit access token for the customer
    # --------------------------------------------------------

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("customer")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name
            )
        )
        .to_jwt()
    )

    # --------------------------------------------------------
    # Explicitly dispatch the Aura AI agent to the room
    # --------------------------------------------------------

    async with api.LiveKitAPI() as lkapi:

        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name
            )
        )

    return {
        "token": token,
        "url": livekit_url,
        "room": room_name
    }
    
# Serve the frontend
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)