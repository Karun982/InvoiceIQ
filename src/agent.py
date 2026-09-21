import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.database import get_document_by_id


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# AZURE AI FOUNDRY
# =========================================================

FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY")

if not FOUNDRY_ENDPOINT:
    raise RuntimeError(
        "FOUNDRY_ENDPOINT is not set in the environment."
    )

if not FOUNDRY_API_KEY:
    raise RuntimeError(
        "FOUNDRY_API_KEY is not set in the environment."
    )


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI(
    api_key=FOUNDRY_API_KEY,
    base_url=(
        FOUNDRY_ENDPOINT.rstrip("/")
        + "/openai/v1/"
    ),
)


# =========================================================
# GET ONLY THE SELECTED INVOICE
# =========================================================

def get_invoice(document_id: int):

    document = get_document_by_id(document_id)

    if document is None:
        return None

    return {
        "id": document.id,
        "transaction_id": document.transaction_id,
        "document_type": document.document_type,
        "party_name": document.party_name,
        "transaction_date": document.transaction_date,
        "due_date": document.due_date,
        "subtotal": document.subtotal,
        "tax": document.tax,
        "total_amount": document.total_amount,
        "currency": document.currency,
        "payment_status": document.payment_status,
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
            }
            for item in document.items
        ],
    }


# =========================================================
# ASK BUSINESS AGENT ABOUT ONE INVOICE
# =========================================================

def ask_business_agent(
    question: str,
    document_id: int,
):

    invoice = get_invoice(document_id)

    if invoice is None:
        return "The selected invoice could not be found."

    invoice_json = json.dumps(
        invoice,
        indent=2,
        ensure_ascii=False,
    )

    instructions = """
You are InvoiceIQ's invoice assistant.

Your ONLY job is to answer questions about the specific
invoice provided in the conversation.

STRICT RULES:

1. Answer ONLY using information contained in the provided invoice.

2. Do NOT use information from any other invoice or document.

3. Do NOT answer general business questions.

4. Do NOT answer questions about the company's overall:
   - revenue
   - purchases
   - expenses
   - profit
   - financial performance

   unless that information is explicitly contained in the
   selected invoice.

5. Do NOT answer unrelated questions such as:
   - weather
   - programming
   - general knowledge
   - mathematics unrelated to the invoice
   - writing requests
   - personal questions
   - general business advice

6. If the question is unrelated to the selected invoice,
   respond exactly:

"I can only answer questions about the currently selected invoice."

7. Never invent information.

8. If the requested information is not present in the invoice,
   say:

"That information is not available in the selected invoice."

9. You may perform simple arithmetic using values explicitly
   present in the invoice when necessary to answer a question.

10. Keep answers concise and directly related to the invoice.

SELECTED INVOICE:

""" + invoice_json

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=instructions,
        input=question,
    )

    return response.output_text