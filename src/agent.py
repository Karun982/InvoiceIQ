import json

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from src.database import documents
from src.analytics import (
    calculate_revenue,
    calculate_purchases,
    calculate_expenses,
    calculate_estimated_profit,
)


PROJECT_ENDPOINT = (
    "https://buisnessagent.services.ai.azure.com/"
    "api/projects/proj-default"
)

credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)


# -----------------------------
# Business functions
# -----------------------------

def get_revenue():
    return calculate_revenue(documents)


def get_purchases():
    return calculate_purchases(documents)


def get_expenses():
    return calculate_expenses(documents)


def get_estimated_profit():
    return calculate_estimated_profit(documents)


def get_business_summary():
    return {
        "revenue": get_revenue(),
        "purchases": get_purchases(),
        "expenses": get_expenses(),
        "estimated_profit": get_estimated_profit(),
    }


# -----------------------------
# Tool definitions for GPT
# -----------------------------

tools = [
    {
        "type": "function",
        "name": "get_revenue",
        "description": "Calculate the total sales revenue from the business data.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_purchases",
        "description": "Calculate the total amount spent on purchases.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_expenses",
        "description": "Calculate the total business expenses.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_estimated_profit",
        "description": (
            "Calculate estimated business profit as "
            "revenue minus purchases minus expenses."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_business_summary",
        "description": (
            "Return revenue, purchases, expenses, "
            "and estimated profit."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


# -----------------------------
# Execute requested tool
# -----------------------------

def execute_tool(name):
    if name == "get_revenue":
        return get_revenue()

    if name == "get_purchases":
        return get_purchases()

    if name == "get_expenses":
        return get_expenses()

    if name == "get_estimated_profit":
        return get_estimated_profit()

    if name == "get_business_summary":
        return get_business_summary()

    return {"error": f"Unknown tool: {name}"}


# -----------------------------
# Ask BuisnessAgent
# -----------------------------

def ask_agent(question):

    with project.get_openai_client() as openai_client:

        response = openai_client.responses.create(
            model="gpt-5-mini",

            instructions="""
You are BuisnessAgent, an AI-powered business
analytics agent.

You have access to tools containing the company's
financial data.

Rules:

1. Use the available tools whenever the user asks
   for financial numbers.

2. Never invent financial data.

3. Never calculate financial totals yourself when
   a tool can provide the result.

4. Clearly distinguish:
   - revenue
   - purchases
   - expenses
   - estimated profit

5. Estimated profit is:
   revenue - purchases - expenses

6. Give concise business-focused answers.
""",

            input=question,

            tools=tools,
        )

        # Tool-calling loop
        while True:

            tool_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not tool_calls:
                break

            tool_outputs = []

            for tool_call in tool_calls:

                result = execute_tool(tool_call.name)

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(result),
                    }
                )

            response = openai_client.responses.create(
                model="gpt-5-mini",

                instructions="""
You are BuisnessAgent.

Use the tool results to answer the user's question.
Do not invent numbers.
""",

                previous_response_id=response.id,

                input=tool_outputs,

                tools=tools,
            )

        return response.output_text