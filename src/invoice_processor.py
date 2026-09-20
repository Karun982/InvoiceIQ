from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from src.models import BusinessDocument, InvoiceItem


DOCUMENT_INTELLIGENCE_ENDPOINT = (
    "https://buisness-store.cognitiveservices.azure.com/"
)

credential = DefaultAzureCredential()

document_client = DocumentIntelligenceClient(
    endpoint=DOCUMENT_INTELLIGENCE_ENDPOINT,
    credential=credential,
)


def get_field(fields, name):
    field = fields.get(name)

    if field is None:
        return None

    return field.value_string or field.content


def get_number(fields, name):
    field = fields.get(name)

    if field is None:
        return None

    if field.value_currency:
        return field.value_currency.amount

    if field.value_number is not None:
        return field.value_number

    return None


def extract_invoice(file_path):
    with open(file_path, "rb") as f:
        poller = document_client.begin_analyze_document(
            "prebuilt-invoice",
            body=f,
        )

    result = poller.result()

    if not result.documents:
        raise ValueError("No invoice was detected.")

    document = result.documents[0]
    fields = document.fields

    items = []

    items_field = fields.get("Items")

    if items_field and items_field.value_array:
        for item in items_field.value_array:
            item_fields = item.value_object

            if not item_fields:
                continue

            description = get_field(item_fields, "Description")
            quantity = get_number(item_fields, "Quantity")
            unit_price = get_number(item_fields, "UnitPrice")
            amount = get_number(item_fields, "Amount")

            if description:
                items.append(
                    InvoiceItem(
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        amount=amount,
                    )
                )

    invoice = BusinessDocument(
        transaction_id=get_field(fields, "InvoiceId"),
        document_type="OTHER",
        party_name=get_field(fields, "VendorName"),
        transaction_date=get_field(fields, "InvoiceDate"),
        due_date=get_field(fields, "DueDate"),
        subtotal=get_number(fields, "SubTotal"),
        tax=get_number(fields, "TotalTax"),
        total_amount=get_number(fields, "InvoiceTotal"),
        currency="INR",
        payment_status=get_field(fields, "PaymentTerm"),
        items=items,
    )

    return invoice