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


messages = [
    {
        "role": "user",
        "content": "Where is my order ORD-101?"
    }
]


# --------------------------------------------------
# Step 1: Ask the model whether a tool is needed
# --------------------------------------------------

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=[order_tool],
    tool_choice="auto"
)


message = response.choices[0].message

print("MODEL REQUEST:")
print(messages[0]["content"])


# --------------------------------------------------
# Step 2: Check whether the model requested a tool
# --------------------------------------------------

if message.tool_calls:

    print("\nTOOL CALL DETECTED")

    # Add the assistant's tool-call message
    messages.append(message)

    for tool_call in message.tool_calls:

        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"Function: {function_name}")
        print(f"Arguments: {arguments}")

        # --------------------------------------------------
        # Step 3: Execute our actual Python function
        # --------------------------------------------------

        if function_name == "get_order_details":

            order_id = arguments["order_id"]

            result = get_order_details(order_id)

            print("\nTOOL RESULT:")
            print(result)

            # --------------------------------------------------
            # Step 4: Send the tool result back to the model
            # --------------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                }
            )


    # --------------------------------------------------
    # Step 5: Ask the model for the final answer
    # --------------------------------------------------

    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=[order_tool]
    )

    final_message = final_response.choices[0].message

    print("\nFINAL AI RESPONSE:")
    print(final_message.content)

else:

    print("\nFINAL AI RESPONSE:")
    print(message.content)