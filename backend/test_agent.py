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


def run_agent(user_message: str):

    messages = [
        {
            "role": "user",
            "content": user_message
        }
    ]

    # First LLM call
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=[order_tool],
        tool_choice="auto"
    )

    message = response.choices[0].message

    # No tool needed
    if not message.tool_calls:
        return message.content

    # Add the assistant's tool-call message
    messages.append(message)

    # Execute requested tools
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

    # Second LLM call
    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=[order_tool]
    )

    return final_response.choices[0].message.content


if __name__ == "__main__":

    test_questions = [
        "Where is my order ORD-101?",
        "Can I cancel order ORD-103?",
        "Where is my order ORD-999?",
        "Where is my order?"
    ]

    for question in test_questions:

        print("\n" + "=" * 60)
        print("CUSTOMER:")
        print(question)

        answer = run_agent(question)

        print("\nAURA AI:")
        print(answer)