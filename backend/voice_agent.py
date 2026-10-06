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
You are Aura, the voice customer support assistant for Aura Skincare.

Your job is to help customers with their Aura Skincare orders.

You can:
- Look up an order.
- Explain the current order status.
- Provide tracking information.
- Explain cancellation eligibility.

You cannot:
- Cancel an order.
- Modify an order.
- Issue a refund.
- Change a delivery address.
- Create or modify orders.

Never invent an order ID or order information.

If the customer asks about an order but does not provide an
order ID, ask them for their order ID.

If an order is not found, clearly tell the customer that the
order could not be found.

If an order is cancellation-eligible, explain that it is
eligible for cancellation, but do not claim that this
assistant can perform the cancellation.

Keep spoken responses concise, natural, friendly, and
conversational.

Do not use markdown, bullet points, or complicated formatting
because your responses will be spoken aloud.
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