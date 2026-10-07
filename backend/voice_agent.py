# ============================================================
# AURA AI — REALTIME VOICE AGENT
# ============================================================
#
# This file contains the realtime voice version of Aura.
#
# The project originally started with a text-based Groq agent
# in:
#
#     app/agent.py
#
# That earlier agent established the core:
#
#     User message
#          ↓
#     LLM tool calling
#          ↓
#     get_order_details()
#          ↓
#     orders.json
#          ↓
#     LLM response
#
# The current voice agent extends that architecture by adding
# realtime speech:
#
#     User voice
#          ↓
#        STT
#          ↓
#        LLM
#          ↓
#     order lookup tool
#          ↓
#        TTS
#          ↓
#     Spoken response
#
# The original text agent is intentionally kept in app/agent.py
# rather than duplicated here.
# ============================================================


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

from dotenv import load_dotenv
# Loads local environment variables from .env.local.
#
# .env.local contains the credentials required for local
# LiveKit development and the Groq API integration.


load_dotenv(".env.local")


# ============================================================
# LIVEKIT AGENT COMPONENTS
# ============================================================

from livekit import agents
# Provides the LiveKit agent runtime and application CLI.


from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    RunContext,
    function_tool,
)
# Agent:
#     Defines Aura's behavior and instructions.
#
# AgentServer:
#     Registers and runs the LiveKit agent worker.
#
# AgentSession:
#     Manages a realtime conversational session.
#
# RunContext:
#     Provides context to tools when the LLM calls them.
#
# function_tool:
#     Converts a Python function into a tool that the LLM
#     can call.


# ============================================================
# GROQ VOICE COMPONENTS
# ============================================================

from livekit.plugins import groq
# Provides Groq integrations for:
#
# STT → Speech-to-Text
# LLM → Large Language Model
# TTS → Text-to-Speech
#
# We use Groq for all three stages of this initial voice
# implementation.


# ============================================================
# EXISTING BUSINESS LOGIC
# ============================================================

from app.orders import get_order_details
# Reuses the existing order lookup function.
#
# This is important architecturally:
#
# The voice layer does NOT directly read orders.json.
#
# Instead:
#
#     voice agent
#          ↓
#     get_order_details()
#          ↓
#     orders.json
#
# This keeps business logic separate from the voice interface.


# ============================================================
# AURA VOICE AGENT
# ============================================================

class AuraVoiceAgent(Agent):
    """
    Realtime voice customer-support agent for Aura Skincare.
    """

    def __init__(self) -> None:

        super().__init__(
            instructions="""
You are Aura, a friendly and professional voice customer support
specialist for Aura Skincare.

Keep your spoken responses concise, natural, and conversational.
Do not use markdown, bullet points, or complicated formatting.

AURA SKINCARE POLICIES

Delivery:
- Free delivery for orders above ₹499.
- Orders below ₹499 have a ₹50 shipping charge.
- Standard delivery takes 3–5 business days.

Returns:
- Returns are accepted within 7 days of delivery.
- Products must be unopened and unused and must be in their
  original packaging.

Damaged or defective products:
- Customers must report damage or defects within 48 hours.
- Photos are required for a replacement request.

Cancellation:
- Orders can only be cancelled while their status is Processing.
- Shipped or Out for Delivery orders cannot be cancelled.
- A customer may refuse the package at the doorstep if it cannot
  be cancelled.

Cash on Delivery:
- COD is available for orders up to ₹2,500.
- Customers can pay by cash or UPI.

ORDER LOOKUP

You have access to an order lookup tool.

Use the order lookup tool whenever the customer asks about a
specific order or wants information such as:
- order status
- delivery information
- tracking information
- cancellation eligibility
- order details

If the customer gives an order ID, use the tool.

If the customer asks about an order but does not provide an
order ID, politely ask for the order ID.

Never invent an order ID or order information.

If the order lookup tool says that an order was not found,
tell the customer that you could not find that order and ask
them to check the order ID.

CANCELLATION

You can explain whether an order is eligible for cancellation,
but you cannot actually cancel an order.

If an order is Processing, explain that it is eligible for
cancellation.

If an order is Shipped or Out for Delivery, explain that it
cannot be cancelled according to Aura's policy.

Do not claim that you cancelled, modified, refunded, or changed
an order.

GENERAL BEHAVIOR

Do not simply agree with the customer if their request conflicts
with Aura's policies.

If the customer's speech is unclear or the order ID is
mumbled, politely ask them to repeat it.

If the customer asks something outside your capabilities,
explain what you can help with and guide them appropriately.

Keep answers short because this is a voice conversation.
"""
        )

    # ========================================================
    # ORDER LOOKUP TOOL
    # ========================================================

    @function_tool()
    async def get_order(
        self,
        context: RunContext,
        order_id: str,
    ) -> dict:
        """
        Look up an Aura Skincare order using its order ID.

        Args:
            order_id: The Aura Skincare order ID, such as ORD-101.
        """

        order = get_order_details(order_id)

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
            }

        return {
            "found": True,
            "order": order,
        }


# ============================================================
# LIVEKIT AGENT SERVER
# ============================================================

server = AgentServer()


@server.rtc_session(agent_name="aura-ai")
async def entrypoint(ctx: agents.JobContext):
    """
    Entry point executed when LiveKit starts a session for Aura.
    """

    # --------------------------------------------------------
    # Configure the realtime conversation pipeline.
    # --------------------------------------------------------

    session = AgentSession(

        # ----------------------------------------------------
        # STT: Speech → Text
        # ----------------------------------------------------
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),

        # ----------------------------------------------------
        # LLM: Text → Reasoning / Response
        # ----------------------------------------------------
        llm=groq.LLM(
            model="openai/gpt-oss-120b",
        ),

        # ----------------------------------------------------
        # TTS: Text → Speech
        # ----------------------------------------------------
        tts=groq.TTS(
        model="canopylabs/orpheus-v1-english",
        voice="autumn"
        )
        
    )

    # --------------------------------------------------------
    # Start the session and attach Aura to the LiveKit room.
    # --------------------------------------------------------

    await session.start(
        room=ctx.room,
        agent=AuraVoiceAgent(),
    )

    # --------------------------------------------------------
    # Connect the agent job to the LiveKit room.
    # --------------------------------------------------------

    await ctx.connect()

    # --------------------------------------------------------
    # Make Aura speak first.
    # --------------------------------------------------------

    await session.generate_reply(
        instructions=(
            "Greet the customer warmly and ask how you can "
            "help with their Aura Skincare order."
        )
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    agents.cli.run_app(server)