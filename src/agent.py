import json
import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from src.database import get_document_by_id, get_all_documents
from src.analytics import (
    calculate_revenue,
    calculate_purchases,
    calculate_net_balance,
    calculate_sales_subtotal,
    calculate_purchase_subtotal,
    calculate_sales_tax,
    calculate_purchase_tax,
    calculate_total_tax,
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# OPENAI / FOUNDRY CLIENT
# =========================================================

FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY")

_openai_client = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        endpoint = os.getenv("FOUNDRY_ENDPOINT")
        api_key = os.getenv("FOUNDRY_API_KEY")
        if not endpoint:
            raise RuntimeError("FOUNDRY_ENDPOINT is not set in the environment.")
        if not api_key:
            raise RuntimeError("FOUNDRY_API_KEY is not set in the environment.")
        _openai_client = OpenAI(
            api_key=api_key,
            base_url=endpoint.rstrip("/") + "/openai/v1/",
        )
    return _openai_client


# =========================================================
# DOCUMENT SERIALIZATION HELPERS
# =========================================================

def format_document(doc) -> Dict[str, Any]:
    tax_status = "unavailable"
    tax_val = getattr(doc, "tax", None)
    is_inferred = getattr(doc, "is_tax_inferred", False)

    if tax_val is not None:
        if is_inferred:
            tax_status = "inferred (calculated as total_amount - subtotal)"
        else:
            tax_status = "explicitly extracted from invoice"

    return {
        "id": getattr(doc, "id", None),
        "transaction_id": getattr(doc, "transaction_id", None),
        "document_type": (getattr(doc, "document_type", None) or "OTHER").upper(),
        "party_name": getattr(doc, "party_name", None) or "Unknown",
        "transaction_date": getattr(doc, "transaction_date", None) or "Unavailable",
        "due_date": getattr(doc, "due_date", None) or "Unavailable",
        "subtotal": doc.subtotal,
        "tax": tax_val,
        "tax_status": tax_status,
        "is_tax_inferred": is_inferred,
        "total_amount": doc.total_amount,
        "currency": getattr(doc, "currency", None) or "INR",
        "payment_status": getattr(doc, "payment_status", None) or "Unavailable",
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
                "raw_ocr_amount": getattr(item, "raw_ocr_amount", None),
                "is_inconsistent": getattr(item, "is_inconsistent", False),
                "inconsistency_note": getattr(item, "inconsistency_note", None),
            }
            for item in (getattr(doc, "items", None) or [])
        ],
    }


def get_invoice(document_id: int):
    document = get_document_by_id(document_id)
    if document is None:
        return None
    return format_document(document)


def get_all_invoices() -> List[Dict[str, Any]]:
    docs = get_all_documents()
    return [format_document(d) for d in docs]


# =========================================================
# CONTEXT BUILDER (FOR TESTING & AGENT REASONING)
# =========================================================

def build_agent_context(
    all_docs: List[Dict[str, Any]],
    context_mode: str = "ALL UPLOADED INVOICES",
) -> Dict[str, Any]:
    """
    Construct the complete structured context payload for the AI assistant.
    Calculates exact aggregate metrics across documents using actual SQLite data.
    """
    # Create simple wrapper objects for analytics calculation
    class DocWrapper:
        def __init__(self, d):
            self.document_type = d.get("document_type")
            self.total_amount = d.get("total_amount")
            self.subtotal = d.get("subtotal")
            self.tax = d.get("tax")

    wrappers = [DocWrapper(d) for d in all_docs]

    sales_docs = [d for d in all_docs if d.get("document_type") == "SALES"]
    purchase_docs = [d for d in all_docs if d.get("document_type") == "PURCHASE"]
    other_docs = [d for d in all_docs if d.get("document_type") not in ("SALES", "PURCHASE")]

    total_sales = calculate_revenue(wrappers)
    total_purchases = calculate_purchases(wrappers)
    net_balance = calculate_net_balance(wrappers)
    sales_subtotal = calculate_sales_subtotal(wrappers)
    purchase_subtotal = calculate_purchase_subtotal(wrappers)
    sales_tax = calculate_sales_tax(wrappers)
    purchase_tax = calculate_purchase_tax(wrappers)
    combined_tax = calculate_total_tax(wrappers)

    payload = {
        "context_mode": context_mode,
        "summary": {
            "total_documents_count": len(all_docs),
            "sales_count": len(sales_docs),
            "purchase_count": len(purchase_docs),
            "other_count": len(other_docs),
            "total_sales_amount": total_sales,
            "total_purchases_amount": total_purchases,
            "sales_subtotal": sales_subtotal,
            "purchase_subtotal": purchase_subtotal,
            "total_tax_collected_on_sales": sales_tax,
            "total_tax_paid_on_purchases": purchase_tax,
            "combined_tax": combined_tax,
            "net_balance_sales_minus_purchases": net_balance,
        },
        "sales_invoices": sales_docs,
        "purchase_invoices": purchase_docs,
    }
    if other_docs:
        payload["other_invoices"] = other_docs

    return payload


# =========================================================
# ASK BUSINESS AGENT (MULTI-INVOICE & SINGLE-INVOICE)
# =========================================================

def ask_agent(question: str, document_id: Optional[int] = None):
    return ask_business_agent(question, document_id)


def ask_business_agent(
    question: str,
    document_id: Optional[int] = None,
    client: Optional[OpenAI] = None,
) -> str:
    if document_id is not None:
        target_doc = get_invoice(document_id)
        if target_doc is None:
            return "The requested invoice could not be found."
        all_docs = [target_doc]
        context_mode = f"FOCUSED ON INVOICE #{target_doc.get('transaction_id') or target_doc.get('id')}"
    else:
        all_docs = get_all_invoices()
        context_mode = "ALL UPLOADED INVOICES"

    if not all_docs:
        return (
            "No invoices have been uploaded yet. Please upload your sales or purchase documents "
            "in the Document Workspace so I can analyze totals, compare revenues vs. expenses, and audit your line items."
        )

    payload = build_agent_context(all_docs, context_mode=context_mode)
    payload_json = json.dumps(payload, indent=2, ensure_ascii=False)

    instructions = f"""You are InvoiceIQ's AI Financial & Invoice Intelligence Assistant.

Your purpose is to answer financial and accounting questions strictly based on the user's uploaded invoices.

CORE ACCURACY REQUIREMENTS:
1. Strict Groundedness:
   - Base all answers ONLY on the actual extracted invoice data provided in the JSON payload below.
   - Do NOT invent, substitute, summarize, or hallucinate product names, vendor names, dates, quantities, or prices.
   - If asked for line items for an invoice, report EXACTLY the items listed in the database under that invoice, including original description, quantity, unit price, and amount.
   - If a field is unavailable or null in the database, clearly state that the field is unavailable rather than guessing.

2. Invoice Dates & Details:
   - Provide the exact transaction_date and due_date from the invoice data (e.g. "14 November 2026").
   - Do not replace missing or actual dates with arbitrary dates.

3. Taxes (GST, CGST, SGST, IGST):
   - Report the exact tax values from the data.
   - Clearly distinguish between explicitly extracted taxes and inferred taxes (e.g. calculated as total_amount - subtotal).
   - Never assume an arbitrary tax rate when the invoice does not specify it.

4. Multi-Invoice Ledger Reasoning:
   - When answering across all invoices:
     * Total Sales = sum of totals of SALES invoices.
     * Total Purchases = sum of totals of PURCHASE invoices.
     * Net Balance = Total Sales - Total Purchases.
     * Combined Tax = Sales Tax + Purchase Tax.
   - Maintain the strict distinction between SALES (revenue/income from customers) and PURCHASE (costs/expenses paid to vendors/suppliers).

5. Line-Item Verification & Inconsistency Reporting:
   - For each line item, report the actual verified invoice amount from the items list (e.g. ₹60,000 for Managed network switch on PUR-2026-0872).
   - If an item has is_inconsistent = True or has an inconsistency_note (e.g. raw OCR text showed ₹1,60,000, which was reconciled to the actual invoice value of ₹60,000 based on quantity 2 × unit price ₹30,000 and invoice subtotal ₹2,85,000), report the verified amount (₹60,000) and explicitly note the OCR inconsistency to the user instead of presenting the incorrect raw OCR reading as correct.

UPLOADED INVOICES CONTEXT:
{payload_json}
"""

    ai_client = client or get_openai_client()

    response = ai_client.responses.create(
        model="gpt-5-mini",
        instructions=instructions,
        input=question,
    )

    return response.output_text
