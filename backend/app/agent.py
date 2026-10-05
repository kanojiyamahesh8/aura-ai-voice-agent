import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.orders import get_order_details


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY was not found.")


client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)


order_tool = {
    "type": "function",
    "function": {
        "name": "get_order_details",
        "description": (
            "Retrieve the current information for an Aura Skincare order. "
            "Use this tool when the customer asks about a specific order, "
            "including delivery status, tracking information, cancellation "
            "eligibility, or other order-specific details. "
            "The order ID must be provided by the customer. "
            "Do not invent an order ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": (
                        "The Aura Skincare order ID, such as ORD-101."
                    )
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        }
    }
}


def run_agent(user_message: str) -> str:

    messages = [
    {
        "role": "system",
        "content": (
            "You are Aura, the customer support assistant for Aura Skincare.\n\n"

            "AVAILABLE CAPABILITY:\n"
            "You have exactly ONE tool: get_order_details.\n"
            "This tool can only READ order information.\n\n"

            "You can:\n"
            "- Look up an order.\n"
            "- Explain order status.\n"
            "- Provide tracking information.\n"
            "- Explain cancellation eligibility.\n\n"

            "You CANNOT:\n"
            "- Cancel an order.\n"
            "- Modify an order.\n"
            "- Issue a refund.\n"
            "- Change a delivery address.\n"
            "- Create or modify orders.\n"
            "- Provide cancellation links.\n"
            "- Refer to a Cancel Order button or webpage.\n"
            "- Claim that any action has been completed.\n\n"

            "IMPORTANT:\n"
            "If an order is cancellation-eligible and the customer asks "
            "whether it can be cancelled, ONLY explain that it is eligible "
            "for cancellation. Do not provide instructions for cancelling "
            "it and do not claim that cancellation can be performed through "
            "this assistant.\n\n"

            "If the customer asks you to cancel an order, explain that the "
            "order is eligible for cancellation if the tool says so, but "
            "that this assistant cannot perform the cancellation.\n\n"

            "Never invent application features, buttons, webpages, URLs, "
            "links, APIs, or actions that are not provided by a tool.\n\n"

            "Never invent an order ID or order information.\n"
            "If an order is not found, clearly tell the customer."
        )
    },
    {
        "role": "user",
        "content": user_message
    }
]

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=[order_tool],
        tool_choice="auto"
    )

    message = response.choices[0].message

    if not message.tool_calls:
        return message.content

    messages.append(message)

    for tool_call in message.tool_calls:

        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_order_details":

            order_id = arguments["order_id"]

            result = get_order_details(order_id)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                }
            )

    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=[order_tool]
    )

    return final_response.choices[0].message.content