from datetime import date, datetime
from typing import Optional
import os

from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from src.models import BusinessDocument, InvoiceItem


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# AZURE DOCUMENT INTELLIGENCE
# ============================================================

DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv(
    "DOCUMENT_INTELLIGENCE_ENDPOINT"
)

DOCUMENT_INTELLIGENCE_API_KEY = os.getenv(
    "DOCUMENT_INTELLIGENCE_API_KEY"
)

if not DOCUMENT_INTELLIGENCE_ENDPOINT:
    raise RuntimeError(
        "DOCUMENT_INTELLIGENCE_ENDPOINT is not set."
    )

if not DOCUMENT_INTELLIGENCE_API_KEY:
    raise RuntimeError(
        "DOCUMENT_INTELLIGENCE_API_KEY is not set."
    )


document_client = DocumentIntelligenceClient(
    endpoint=DOCUMENT_INTELLIGENCE_ENDPOINT,
    credential=AzureKeyCredential(
        DOCUMENT_INTELLIGENCE_API_KEY
    ),
)


# ============================================================
# FIELD HELPERS
# ============================================================

def get_field(fields, name):
    """Safely get a field from Azure Document Intelligence."""
    if not fields:
        return None

    return fields.get(name)


def get_field_value(field):
    """Extract the actual value from an Azure DI field."""

    if field is None:
        return None

    value_string = getattr(field, "value_string", None)
    if value_string is not None:
        return value_string

    value_number = getattr(field, "value_number", None)
    if value_number is not None:
        return value_number

    value_integer = getattr(field, "value_integer", None)
    if value_integer is not None:
        return value_integer

    value_date = getattr(field, "value_date", None)
    if value_date is not None:
        return value_date

    value_time = getattr(field, "value_time", None)
    if value_time is not None:
        return value_time

    value_currency = getattr(field, "value_currency", None)
    if value_currency is not None:
        return value_currency

    value_array = getattr(field, "value_array", None)
    if value_array is not None:
        return value_array

    value_object = getattr(field, "value_object", None)
    if value_object is not None:
        return value_object

    content = getattr(field, "content", None)
    if content is not None:
        return str(content).strip()

    return None


def clean_text(value):
    """Convert a value to clean text."""

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def normalize_number(value):
    """Convert numbers/currency values into float."""

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
        if "amount" in value:
            try:
                return float(value["amount"])
            except (TypeError, ValueError):
                pass

    # String number
    if isinstance(value, str):
        cleaned = (
            value
            .replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .strip()
        )

        try:
            return float(cleaned)
        except (TypeError, ValueError):
            return None

    return None


def normalize_date(value):
    """Convert Azure date values into readable strings."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%d %B %Y")

    if isinstance(value, date):
        return value.strftime("%d %B %Y")

    return str(value).strip()


# ============================================================
# MONEY EXTRACTION
# ============================================================

def extract_money_amount(fields, field_names):
    """Extract a monetary value from one of several possible fields."""

    for field_name in field_names:
        field = get_field(fields, field_name)

        if field is None:
            continue

        currency_value = getattr(
            field,
            "value_currency",
            None
        )

        if currency_value is not None:
            amount = getattr(
                currency_value,
                "amount",
                None
            )

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
# TRANSACTION ID
# ============================================================

def extract_transaction_id(fields):
    possible_fields = [
        "InvoiceId",
        "InvoiceNumber",
        "TransactionId",
        "DocumentNumber",
        "ReceiptNumber",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)

        value = get_field_value(field)

        value = clean_text(value)

        if value:
            return value

    return None


# ============================================================
# PARTY NAME
# ============================================================

def extract_party_name(fields):
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

        value = get_field_value(field)

        value = clean_text(value)

        if value:
            return value

    return None


# ============================================================
# TRANSACTION DATE
# ============================================================

def extract_transaction_date(fields):
    possible_fields = [
        "InvoiceDate",
        "TransactionDate",
        "Date",
        "ReceiptDate",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)

        value = get_field_value(field)

        value = normalize_date(value)

        if value:
            return value

    return None


# ============================================================
# DUE DATE
# ============================================================

def extract_due_date(fields):
    possible_fields = [
        "DueDate",
        "PaymentDueDate",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)

        value = get_field_value(field)

        value = normalize_date(value)

        if value:
            return value

    return None


# ============================================================
# PAYMENT STATUS
# ============================================================

def extract_payment_status(fields):
    possible_fields = [
        "PaymentStatus",
        "PaymentTerms",
    ]

    for field_name in possible_fields:
        field = get_field(fields, field_name)

        value = get_field_value(field)

        value = clean_text(value)

        if value:
            return value

    return None


# ============================================================
# CURRENCY
# ============================================================

def extract_currency_code(fields):
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

        currency = getattr(
            field,
            "value_currency",
            None
        )

        if currency is not None:
            code = getattr(
                currency,
                "currency_code",
                None
            )

            if code:
                return str(code)

        value = get_field_value(field)

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    return "INR"


# ============================================================
# LINE ITEM OBJECT HELPER
# ============================================================

def get_object_field(item_object, possible_names):
    """Get a field from one invoice line-item object."""

    if item_object is None:
        return None

    for name in possible_names:

        # Dictionary
        if isinstance(item_object, dict):
            if name in item_object:
                return item_object[name]

        # Azure SDK dictionary-like object
        try:
            value = item_object.get(name)

            if value is not None:
                return value
        except Exception:
            pass

    return None


# ============================================================
# LINE ITEM EXTRACTION
# ============================================================

def extract_line_items(fields):
    """
    Extract every invoice line independently.

    Important:
    We process each row as:

        Description
        Quantity
        UnitPrice
        Amount

    instead of mixing separate arrays.
    """

    items = []

    items_field = get_field(
        fields,
        "Items"
    )

    if items_field is None:
        print("No Items field found.")
        return items

    raw_items = getattr(
        items_field,
        "value_array",
        None
    )

    if raw_items is None:
        raw_items = get_field_value(
            items_field
        )

    if not raw_items:
        print("Items field is empty.")
        return items

    for raw_item in raw_items:

        try:
            # Azure DI item normally contains value_object
            item_object = getattr(
                raw_item,
                "value_object",
                None
            )

            # Fallback for dictionary
            if item_object is None:
                if isinstance(raw_item, dict):
                    item_object = raw_item

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
                ]
            )

            description = clean_text(
                get_field_value(
                    description_field
                )
            )

            # ------------------------------------------------
            # QUANTITY
            # ------------------------------------------------

            quantity_field = get_object_field(
                item_object,
                [
                    "Quantity",
                    "quantity",
                    "Qty",
                ]
            )

            quantity = normalize_number(
                get_field_value(
                    quantity_field
                )
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
                ]
            )

            unit_price = normalize_number(
                get_field_value(
                    unit_price_field
                )
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
                ]
            )

            amount = normalize_number(
                get_field_value(
                    amount_field
                )
            )

            # ------------------------------------------------
            # IMPORTANT FALLBACK
            # ------------------------------------------------

            if (
                quantity is not None
                and unit_price is not None
            ):
                calculated_amount = round(
                    quantity * unit_price,
                    2
                )

                # Always prefer Quantity × Unit Price.
                amount = calculated_amount

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
            )

            items.append(item)

        except Exception as error:
            print(
                f"Error extracting line item: {error}"
            )

    print(
        f"Extracted {len(items)} line items."
    )

    for index, item in enumerate(
        items,
        start=1
    ):
        print(
            f"Item {index}: {item.model_dump()}"
        )

    return items


# ============================================================
# MAIN FUNCTION
# ============================================================

def extract_invoice(file_path: str) -> BusinessDocument:
    """
    Extract structured invoice information
    using Azure Document Intelligence.
    """

    print(
        f"Processing document: {file_path}"
    )

    # --------------------------------------------------------
    # SEND DOCUMENT TO AZURE
    # --------------------------------------------------------

    with open(
        file_path,
        "rb"
    ) as file:

        poller = document_client.begin_analyze_document(
            "prebuilt-invoice",
            body=file,
        )

    # --------------------------------------------------------
    # GET RESULT
    # --------------------------------------------------------

    result = poller.result()

    if not result.documents:
        raise ValueError(
            "Document Intelligence did not detect an invoice."
        )

    analyzed_document = result.documents[0]

    fields = analyzed_document.fields

    # --------------------------------------------------------
    # EXTRACT BASIC INFORMATION
    # --------------------------------------------------------

    transaction_id = extract_transaction_id(
        fields
    )

    party_name = extract_party_name(
        fields
    )

    transaction_date = extract_transaction_date(
        fields
    )

    due_date = extract_due_date(
        fields
    )

    currency = extract_currency_code(
        fields
    )

    payment_status = extract_payment_status(
        fields
    )

    # --------------------------------------------------------
    # EXTRACT FINANCIAL INFORMATION
    # --------------------------------------------------------

    subtotal = extract_money_amount(
        fields,
        [
            "SubTotal",
            "Subtotal",
            "SubTotalAmount",
        ]
    )

    tax = extract_money_amount(
        fields,
        [
            "TotalTax",
            "Tax",
            "TaxAmount",
        ]
    )

    total_amount = extract_money_amount(
        fields,
        [
            "InvoiceTotal",
            "Total",
            "GrandTotal",
        ]
    )

    # --------------------------------------------------------
    # EXTRACT LINE ITEMS
    # --------------------------------------------------------

    items = extract_line_items(
        fields
    )

    # --------------------------------------------------------
    # BUILD BUSINESS DOCUMENT
    # --------------------------------------------------------

    document = BusinessDocument(
        transaction_id=transaction_id,
        document_type="OTHER",
        party_name=party_name,
        transaction_date=transaction_date,
        due_date=due_date,
        subtotal=subtotal,
        tax=tax,
        total_amount=total_amount,
        currency=currency,
        payment_status=payment_status,
        items=items,
    )

    # --------------------------------------------------------
    # DEBUG OUTPUT
    # --------------------------------------------------------

    print("\n========== EXTRACTED DOCUMENT ==========")
    print(document.model_dump())
    print("=========================================\n")

    return document