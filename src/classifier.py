import json

from src.models import BusinessDocument
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


PROJECT_ENDPOINT = (
    "https://buisnessagent.services.ai.azure.com/"
    "api/projects/proj-default"
)


credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)


def classify_document(document: BusinessDocument) -> str:

    document_data = document.model_dump()

    prompt = f"""
You are classifying a business document for an accounting
and business analytics system.

Classify the document into EXACTLY ONE of these categories:

SALES
PURCHASE
EXPENSE
OTHER


=========================================================
SALES
=========================================================

Choose SALES when the document represents money that the
business earns by selling goods or services to a customer.

Typical examples:

- Sales invoice
- Customer invoice
- Invoice issued by the business
- Product sale
- Service sale
- Consulting invoice issued to a customer
- Software/service subscription sold to a customer

Strong indicators:

- The business is the seller/service provider.
- Another party is the customer/buyer.
- The document represents revenue for the business.


=========================================================
PURCHASE
=========================================================

Choose PURCHASE when the business is buying goods or
services from a supplier/vendor, especially when the
purchase is related to inventory, equipment, raw materials,
technology, or other acquired goods/services.

Typical examples:

- Supplier invoice
- Vendor invoice
- Inventory purchase
- Raw material purchase
- Server/hardware purchase
- Computer/equipment purchase
- Software purchased from a supplier
- Goods purchased for resale

Strong indicators:

- Another company is the seller/supplier.
- The business is the buyer/customer.
- The document represents a business acquisition/purchase.


=========================================================
EXPENSE
=========================================================

Choose EXPENSE when the document represents an ordinary
operating cost of running the business rather than revenue.

Examples include:

- Electricity bill
- Water bill
- Internet bill
- Telephone bill
- Office rent
- Office maintenance
- Office supplies
- Travel expense
- Hotel expense for business travel
- Taxi/transport expense
- Advertising expense
- Marketing expense
- Professional/service charges
- Bank charges
- Insurance expense
- Salary/payroll expense
- Utility bills
- Recurring subscriptions used to operate the business
- Cleaning services
- Repairs and maintenance
- Courier/postage charges

IMPORTANT:

A document does NOT need to literally be called an
"expense invoice" to be classified as EXPENSE.

Classify it as EXPENSE based on WHAT the business is paying
for.

For example:

"Electricity consumption charges"
=> EXPENSE

"Office rent for September"
=> EXPENSE

"Internet service charges"
=> EXPENSE

"Business travel hotel bill"
=> EXPENSE


=========================================================
PURCHASE vs EXPENSE
=========================================================

Do NOT automatically classify every supplier invoice as
EXPENSE.

Use PURCHASE when the document represents acquisition of
goods, inventory, raw materials, equipment, or a normal
business purchase.

Use EXPENSE when the document represents an operating cost
such as utilities, rent, travel, salaries, advertising,
maintenance, bank charges, etc.

If the document is clearly a supplier purchase of goods or
equipment, choose PURCHASE.

If it is clearly an operating cost, choose EXPENSE.


=========================================================
OTHER
=========================================================

Choose OTHER when the document is not confidently a:

- SALES document
- PURCHASE document
- EXPENSE document

Examples:

- Bank deposit receipt
- Bank transfer confirmation
- Loan document
- Tax/government document without a clear transaction
- Legal document
- Identity document
- Generic receipt with insufficient business context
- Non-financial document


=========================================================
IMPORTANT CLASSIFICATION RULES
=========================================================

1. Look at the entire document data.

2. Consider:
   - party_name
   - transaction_id
   - transaction_date
   - subtotal
   - tax
   - total_amount
   - payment_status
   - line items
   - item descriptions
   - quantities
   - prices

3. Use the nature of the transaction, not just keywords.

4. Do not classify a document as EXPENSE merely because
   money was paid.

5. Do not classify a document as PURCHASE merely because
   another company issued it.

6. If the line items clearly describe utilities, rent,
   travel, salary, maintenance, advertising, office costs,
   bank charges, or similar operating costs, classify it
   as EXPENSE.

7. If the document clearly represents goods/equipment/
   inventory being purchased, classify it as PURCHASE.

8. If the business is the seller and the other party is the
   customer, classify it as SALES.

9. If there is insufficient information, choose OTHER.


=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Do not add explanations.

Exact format:

{{"document_type": "SALES"}}

or

{{"document_type": "PURCHASE"}}

or

{{"document_type": "EXPENSE"}}

or

{{"document_type": "OTHER"}}


DOCUMENT DATA:

{json.dumps(document_data, indent=2)}
"""

    with project.get_openai_client() as openai_client:

        response = openai_client.responses.create(
            model="gpt-5-mini",
            instructions=(
                "You are a strict business document "
                "classifier. "
                "Return ONLY valid JSON with one "
                "document_type value."
            ),
            input=prompt,
        )

    try:

        result = json.loads(
            response.output_text.strip()
        )

    except json.JSONDecodeError:

        return "OTHER"


    document_type = (
        str(
            result.get(
                "document_type",
                "OTHER"
            )
        )
        .strip()
        .upper()
    )


    allowed_types = {
        "SALES",
        "PURCHASE",
        "EXPENSE",
        "OTHER",
    }


    if document_type not in allowed_types:

        return "OTHER"


    return document_type