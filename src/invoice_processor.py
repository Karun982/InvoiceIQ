import os
import re
from datetime import date, datetime
from typing import Optional, List, Tuple, Any

from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from src.models import BusinessDocument, InvoiceItem


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# AZURE DOCUMENT INTELLIGENCE CLIENT
# ============================================================

DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_API_KEY = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")

_document_client = None


def get_document_client() -> DocumentIntelligenceClient:
    """Lazily initialize and return the DocumentIntelligenceClient."""
    global _document_client
    if _document_client is None:
        endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
        api_key = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")
        if not endpoint:
            raise RuntimeError("DOCUMENT_INTELLIGENCE_ENDPOINT is not set.")
        if not api_key:
            raise RuntimeError("DOCUMENT_INTELLIGENCE_API_KEY is not set.")
        _document_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
    return _document_client


# For backwards-compatibility with direct imports
if DOCUMENT_INTELLIGENCE_ENDPOINT and DOCUMENT_INTELLIGENCE_API_KEY:
    try:
        document_client = get_document_client()
    except Exception:
        document_client = None
else:
    document_client = None


# ============================================================
# FIELD HELPERS
# ============================================================

def get_field(fields: Any, name: str) -> Any:
    """Safely get a field from Azure Document Intelligence or a dict."""
    if not fields:
        return None

    if isinstance(fields, dict):
        if name in fields:
            return fields[name]
        for key, value in fields.items():
            if key.lower() == name.lower():
                return value
        return None

    # Object with attributes
    val = getattr(fields, name, None)
    if val is not None:
        return val

    # Case-insensitive attribute lookup
    name_lower = name.lower()
    for attr in dir(fields):
        if attr.lower() == name_lower:
            return getattr(fields, attr, None)

    return None


def get_field_value(field: Any) -> Any:
    """Extract the actual value from an Azure DI field, dict, or primitive."""
    if field is None:
        return None

    # If it is already a list or tuple, return directly
    if isinstance(field, (list, tuple)):
        return field

    # If it is already a primitive or datetime/date, return directly
    if isinstance(field, (int, float, bool, date, datetime)):
        return field

    if isinstance(field, str):
        return field.strip()

    # If it is an Azure SDK DocumentField or similar model
    for attr in (
        "value_string",
        "value_number",
        "value_integer",
        "value_date",
        "value_time",
        "value_currency",
        "value_array",
        "value_object",
        "content",
    ):
        val = getattr(field, attr, None)
        if val is not None:
            return val

    # If it is a dictionary
    if isinstance(field, dict):
        for key in (
            "value_string", "valueString",
            "value_number", "valueNumber",
            "value_integer", "valueInteger",
            "value_date", "valueDate",
            "value_currency", "valueCurrency",
            "value_array", "valueArray",
            "value_object", "valueObject",
            "amount",
            "content",
            "value",
        ):
            if key in field and field[key] is not None:
                return field[key]

    return None


def clean_text(value: Any) -> Optional[str]:
    """Convert a value to clean text."""
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def normalize_number(value: Any) -> Optional[float]:
    """Convert numbers, currency values, or strings into float."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    # Azure currency object
    amount = getattr(value, "amount", None)
    if amount is not None:
        try:
            return float(amount)
        except (TypeError, ValueError):
            pass

    # Dictionary currency object
    if isinstance(value, dict):
        for key in ("amount", "value", "value_number", "valueNumber"):
            if key in value and value[key] is not None:
                try:
                    return float(value[key])
                except (TypeError, ValueError):
                    pass

    # String number
    if isinstance(value, str):
        cleaned = value.strip()
        # Remove common currency codes/symbols
        cleaned = re.sub(r"(?i)\b(inr|rs\.?|usd|eur|gbp)\b", "", cleaned)
        cleaned = re.sub(r"[₹$€£¥/\\-]", " ", cleaned)
        cleaned = cleaned.replace(",", "").strip()

        # Handle accounting negative format: (100.00)
        is_negative = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            is_negative = True
            cleaned = cleaned[1:-1].strip()

        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                num = float(match.group(0))
                return -num if is_negative else num
            except (TypeError, ValueError):
                return None

    return None


def normalize_date(value: Any) -> Optional[str]:
    """Convert Azure date values into readable strings (e.g. '14 November 2026')."""
    if value is None:
        return None

    # Handle datetime and date objects
    if isinstance(value, (datetime, date)):
        return value.strftime("%d %B %Y").lstrip("0")

    # Handle dictionary representation
    if isinstance(value, dict):
        for k in ("value_date", "valueDate", "content", "value"):
            if k in value and value[k] is not None:
                return normalize_date(value[k])

    # Handle string representation
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        # Clean trailing ISO time (e.g. 2026-11-14T00:00:00)
        if "T" in text:
            text = text.split("T")[0].strip()

        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d.%m.%Y",
            "%Y.%m.%d",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%Y%m%d",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.strftime("%d %B %Y").lstrip("0")
            except ValueError:
                continue

        # If it doesn't match standard patterns, preserve the cleaned text
        return text

    return str(value).strip()


# ============================================================
# MONEY EXTRACTION
# ============================================================

def extract_money_amount(fields: Any, field_names: List[str]) -> Optional[float]:
    """Extract a monetary value from one of several possible fields."""
    for field_name in field_names:
        field = get_field(fields, field_name)
        if field is None:
            continue

        currency_value = getattr(field, "value_currency", None)
        if currency_value is not None:
            amount = getattr(currency_value, "amount", None)
            if amount is not None:
                try:
                    return float(amount)
                except (TypeError, ValueError):
                    pass

        raw_value = get_field_value(field)
        amount = normalize_number(raw_value)
        if amount is not None:
            return amount

    return None


# ============================================================
# TAX EXTRACTION (SUPPORTING GST, CGST, SGST, IGST & INFERRED)
# ============================================================

def extract_tax(
    fields: Any,
    subtotal: Optional[float] = None,
    total_amount: Optional[float] = None,
    items: Optional[List[InvoiceItem]] = None,
) -> Tuple[Optional[float], bool]:
    """
    Extract GST / Tax values.
    Returns: (tax_amount, is_inferred)

    Steps:
    1. Check TotalTax field.
    2. Check TaxItems array (e.g. CGST, SGST, IGST components).
    3. Check specific tax fields (CGST, SGST, IGST, GST, SalesTax).
    4. Check line-item tax sum.
    5. Fallback: if tax is missing from OCR but total_amount and subtotal exist,
       infer tax = total_amount - subtotal and mark is_inferred = True.
    """
    # 1. TotalTax field
    total_tax = extract_money_amount(
        fields,
        [
            "TotalTax",
            "TotalTaxAmount",
            "TaxTotal",
            "Tax",
            "TaxAmount",
        ],
    )

    # 2. TaxItems array
    tax_items_sum = 0.0
    tax_items_found = False
    tax_items_field = get_field(fields, "TaxItems") or get_field(fields, "tax_items")
    if tax_items_field:
        raw_tax_items = getattr(tax_items_field, "value_array", None)
        if raw_tax_items is None:
            if isinstance(tax_items_field, (list, tuple)):
                raw_tax_items = tax_items_field
            else:
                raw_tax_items = get_field_value(tax_items_field)
        if isinstance(raw_tax_items, list):
            for t_item in raw_tax_items:
                t_obj = getattr(t_item, "value_object", None)
                if t_obj is None and isinstance(t_item, dict):
                    t_obj = t_item.get("value_object") or t_item
                if t_obj:
                    amount_field = get_object_field(
                        t_obj,
                        ["Amount", "amount", "TaxAmount", "tax_amount"],
                    )
                    amt = normalize_number(get_field_value(amount_field))
                    if amt is not None and amt > 0:
                        tax_items_sum += amt
                        tax_items_found = True

    # 3. Component fields (CGST, SGST, IGST)
    component_sum = 0.0
    component_found = False
    for comp_name in ["CGST", "SGST", "IGST", "GST"]:
        comp_field = get_field(fields, comp_name)
        if comp_field is not None:
            amt = normalize_number(get_field_value(comp_field))
            if amt is not None and amt > 0:
                component_sum += amt
                component_found = True

    # Check explicit tax resolution (avoiding double-counting)
    if total_tax is not None and total_tax > 0:
        return round(total_tax, 2), False

    if tax_items_found and tax_items_sum > 0:
        return round(tax_items_sum, 2), False

    if component_found and component_sum > 0:
        return round(component_sum, 2), False

    # 4. Infer tax from total_amount - subtotal if both are present
    if total_amount is not None and subtotal is not None:
        diff = round(total_amount - subtotal, 2)
        if diff > 0:
            return diff, True

    return None, False


# ============================================================
# TRANSACTION ID
# ============================================================

def extract_transaction_id(fields: Any) -> Optional[str]:
    possible_fields = [
        "InvoiceId",
        "InvoiceNumber",
        "TransactionId",
        "DocumentNumber",
        "ReceiptNumber",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        value = clean_text(get_field_value(field))
        if value:
            return value

    return None


# ============================================================
# PARTY NAME
# ============================================================

def extract_party_name(fields: Any) -> Optional[str]:
    possible_fields = [
        "VendorName",
        "CustomerName",
        "MerchantName",
        "SupplierName",
        "BillingAddressRecipient",
        "ShippingAddressRecipient",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        value = clean_text(get_field_value(field))
        if value:
            return value

    return None


# ============================================================
# TRANSACTION DATE
# ============================================================

def extract_transaction_date(fields: Any) -> Optional[str]:
    possible_fields = [
        "InvoiceDate",
        "TransactionDate",
        "Date",
        "ReceiptDate",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        raw_val = get_field_value(field)
        value = normalize_date(raw_val)
        if value:
            return value

    return None


# ============================================================
# DUE DATE
# ============================================================

def extract_due_date(fields: Any) -> Optional[str]:
    possible_fields = [
        "DueDate",
        "PaymentDueDate",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        raw_val = get_field_value(field)
        value = normalize_date(raw_val)
        if value:
            return value

    return None


# ============================================================
# PAYMENT STATUS
# ============================================================

def extract_payment_status(fields: Any) -> Optional[str]:
    possible_fields = [
        "PaymentStatus",
        "PaymentTerms",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        value = clean_text(get_field_value(field))
        if value:
            return value

    return None


# ============================================================
# CURRENCY
# ============================================================

def extract_currency_code(fields: Any) -> str:
    possible_fields = [
        "InvoiceTotal",
        "CurrencyCode",
        "Currency",
        "InvoiceCurrency",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)
        if field is None:
            continue

        currency = getattr(field, "value_currency", None)
        if currency is not None:
            code = getattr(currency, "currency_code", None)
            if code:
                return str(code)

        if isinstance(field, dict) and "currency_code" in field:
            return str(field["currency_code"])

        value = get_field_value(field)
        if isinstance(value, str):
            val_clean = value.strip()
            if val_clean in ("INR", "USD", "EUR", "GBP"):
                return val_clean

    return "INR"


# ============================================================
# LINE ITEM OBJECT HELPER
# ============================================================

def get_object_field(item_object: Any, possible_names: List[str]) -> Any:
    """Get a field from one invoice line-item object or dictionary."""
    if item_object is None:
        return None

    for name in possible_names:
        if isinstance(item_object, dict):
            if name in item_object:
                return item_object[name]
            for k, v in item_object.items():
                if k.lower() == name.lower():
                    return v

        try:
            val = getattr(item_object, name, None)
            if val is not None:
                return val
        except Exception:
            pass

    return None


# ============================================================
# LINE ITEM EXTRACTION
# ============================================================

def extract_line_items(fields: Any) -> List[InvoiceItem]:
    """
    Extract every invoice line independently directly from Azure Document Intelligence.
    Preserves original descriptions, quantities, unit prices, and amounts.
    Never invents, substitutes, or hallucinates products.
    """
    items = []

    items_field = get_field(fields, "Items")
    if items_field is None:
        items_field = get_field(fields, "items") or get_field(fields, "InvoiceItems")

    if items_field is None:
        return items

    raw_items = getattr(items_field, "value_array", None)
    if raw_items is None:
        if isinstance(items_field, (list, tuple)):
            raw_items = items_field
        else:
            raw_items = get_field_value(items_field)

    if not raw_items or not isinstance(raw_items, list):
        return items

    for raw_item in raw_items:
        try:
            item_object = getattr(raw_item, "value_object", None)
            if item_object is None and isinstance(raw_item, dict):
                item_object = (
                    raw_item.get("value_object")
                    or raw_item.get("valueObject")
                    or raw_item
                )

            if not item_object:
                continue

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------
            description_field = get_object_field(
                item_object,
                [
                    "Description",
                    "description",
                    "ProductDescription",
                    "ItemDescription",
                    "Name",
                    "Title",
                    "Item",
                ],
            )
            raw_desc = get_field_value(description_field)
            if raw_desc is None and isinstance(description_field, str):
                raw_desc = description_field
            description = clean_text(raw_desc)

            # ------------------------------------------------
            # QUANTITY
            # ------------------------------------------------
            quantity_field = get_object_field(
                item_object,
                [
                    "Quantity",
                    "quantity",
                    "Qty",
                    "qty",
                    "Units",
                    "Count",
                ],
            )
            raw_qty = get_field_value(quantity_field)
            quantity = normalize_number(
                raw_qty if raw_qty is not None else quantity_field
            )

            # ------------------------------------------------
            # UNIT PRICE
            # ------------------------------------------------
            unit_price_field = get_object_field(
                item_object,
                [
                    "UnitPrice",
                    "unit_price",
                    "Unit Price",
                    "Price",
                    "Rate",
                    "unitPrice",
                ],
            )
            raw_price = get_field_value(unit_price_field)
            unit_price = normalize_number(
                raw_price if raw_price is not None else unit_price_field
            )

            # ------------------------------------------------
            # AMOUNT
            # ------------------------------------------------
            amount_field = get_object_field(
                item_object,
                [
                    "Amount",
                    "amount",
                    "LineTotal",
                    "LineAmount",
                    "Total",
                    "lineTotal",
                    "lineAmount",
                ],
            )
            raw_amt = get_field_value(amount_field)
            amount = normalize_number(
                raw_amt if raw_amt is not None else amount_field
            )

            # ------------------------------------------------
            # MATHEMATICAL RECONCILIATION FALLBACK
            # ------------------------------------------------
            if amount is None and quantity is not None and unit_price is not None:
                amount = round(quantity * unit_price, 2)
            elif unit_price is None and amount is not None and quantity is not None and quantity > 0:
                unit_price = round(amount / quantity, 2)

            # ------------------------------------------------
            # IGNORE COMPLETELY EMPTY ROWS
            # ------------------------------------------------
            if (
                description is None
                and quantity is None
                and unit_price is None
                and amount is None
            ):
                continue

            item = InvoiceItem(
                description=description or "Unnamed item",
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                raw_ocr_amount=amount,
                is_inconsistent=False,
            )
            items.append(item)

        except Exception as error:
            print(f"Error extracting line item: {error}")

    return items


# ============================================================
# LINE ITEM RECONCILIATION
# ============================================================

def reconcile_line_items(
    items: List[InvoiceItem],
    subtotal: Optional[float] = None,
) -> List[InvoiceItem]:
    """
    Reconciles each line item's amount with unit pricing, quantity, and invoice subtotal.
    Detects and corrects OCR anomalies (e.g. OCR misreading currency symbols or column
    borders as leading digits, such as 160,000 instead of 60,000).
    Flags any discrepancies so inconsistent values are never silently presented as correct.
    """
    if not items:
        return items

    for i, item in enumerate(items):
        raw_amt = item.amount
        item.raw_ocr_amount = raw_amt
        qty = item.quantity
        price = item.unit_price

        calc_amt = (
            round(qty * price, 2)
            if (qty is not None and price is not None)
            else None
        )

        if raw_amt is None:
            if calc_amt is not None:
                item.amount = calc_amt
            continue

        if calc_amt is not None:
            if abs(raw_amt - calc_amt) < 0.01:
                # Internally consistent
                item.is_inconsistent = False
            else:
                # Discrepancy between raw OCR amount and quantity * unit_price
                if subtotal is not None:
                    # Calculate sum of other items
                    sum_others = round(
                        sum(
                            (
                                other.amount
                                if other.amount is not None
                                else (
                                    round(other.quantity * other.unit_price, 2)
                                    if other.quantity and other.unit_price
                                    else 0.0
                                )
                            )
                            for j, other in enumerate(items)
                            if j != i
                        ),
                        2,
                    )

                    remainder = round(subtotal - sum_others, 2)

                    if abs(remainder - calc_amt) < 0.01:
                        # Quantity * price exactly matches the remaining invoice subtotal.
                        # The raw OCR amount contains an anomaly (e.g. leading digit 1 from | or ₹).
                        item.amount = calc_amt
                        item.is_inconsistent = True
                        item.inconsistency_note = (
                            f"OCR extracted amount ₹{raw_amt:,.2f}; reconciled to actual invoice value "
                            f"₹{calc_amt:,.2f} based on quantity ({qty:g}) × unit price (₹{price:,.2f}) "
                            f"matching invoice subtotal (₹{subtotal:,.2f})."
                        )
                    elif abs(remainder - raw_amt) < 0.01:
                        # The raw amount matches subtotal, but differs from qty * price (e.g. discount)
                        item.amount = raw_amt
                        item.is_inconsistent = True
                        diff = round(calc_amt - raw_amt, 2)
                        item.inconsistency_note = (
                            f"Line item amount ₹{raw_amt:,.2f} matches subtotal, but differs from "
                            f"quantity ({qty:g}) × unit price (₹{price:,.2f}) by ₹{diff:,.2f} (item discount or adjustment)."
                        )
                    else:
                        item.is_inconsistent = True
                        item.inconsistency_note = (
                            f"Line item amount ₹{raw_amt:,.2f} is inconsistent with quantity ({qty:g}) × "
                            f"unit price (₹{price:,.2f}) = ₹{calc_amt:,.2f} and subtotal remainder ₹{remainder:,.2f}."
                        )
                        if abs(subtotal - (sum_others + calc_amt)) < abs(subtotal - (sum_others + raw_amt)):
                            item.amount = calc_amt
                else:
                    item.is_inconsistent = True
                    item.inconsistency_note = (
                        f"Line item amount ₹{raw_amt:,.2f} differs from quantity ({qty:g}) × "
                        f"unit price (₹{price:,.2f}) = ₹{calc_amt:,.2f}."
                    )

    return items


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_invoice_from_fields(fields: Any, client_doc_type: str = "OTHER") -> BusinessDocument:
    """Build a BusinessDocument model directly from Azure DI fields."""
    transaction_id = extract_transaction_id(fields)
    party_name = extract_party_name(fields)
    transaction_date = extract_transaction_date(fields)
    due_date = extract_due_date(fields)
    currency = extract_currency_code(fields)
    payment_status = extract_payment_status(fields)

    # Line items (raw extracted)
    items = extract_line_items(fields)

    # Subtotal
    subtotal = extract_money_amount(
        fields,
        [
            "SubTotal",
            "Subtotal",
            "SubTotalAmount",
            "NetTotal",
        ],
    )

    # Reconcile line items with unit pricing and subtotal
    items = reconcile_line_items(items, subtotal=subtotal)

    if subtotal is None and items:
        valid_amounts = [it.amount for it in items if it.amount is not None]
        if valid_amounts:
            subtotal = round(sum(valid_amounts), 2)

    # Total Amount
    total_amount = extract_money_amount(
        fields,
        [
            "InvoiceTotal",
            "Total",
            "GrandTotal",
            "GrossAmount",
        ],
    )

    # Tax & Inferred Flag
    tax, is_tax_inferred = extract_tax(
        fields=fields,
        subtotal=subtotal,
        total_amount=total_amount,
        items=items,
    )

    # If total_amount is missing but subtotal and tax are known:
    if total_amount is None and subtotal is not None:
        total_amount = round(subtotal + (tax or 0.0), 2)

    return BusinessDocument(
        transaction_id=transaction_id,
        document_type=client_doc_type,
        party_name=party_name,
        transaction_date=transaction_date,
        due_date=due_date,
        subtotal=subtotal,
        tax=tax,
        is_tax_inferred=is_tax_inferred,
        total_amount=total_amount,
        currency=currency,
        payment_status=payment_status,
        items=items,
    )


def extract_invoice(file_path: str) -> BusinessDocument:
    """
    Extract structured invoice information using Azure Document Intelligence.
    """
    client = get_document_client()

    with open(file_path, "rb") as file:
        poller = client.begin_analyze_document(
            "prebuilt-invoice",
            body=file,
        )

    result = poller.result()
    if not result.documents:
        raise ValueError("Document Intelligence did not detect an invoice.")

    analyzed_document = result.documents[0]
    fields = analyzed_document.fields

    return extract_invoice_from_fields(fields)
