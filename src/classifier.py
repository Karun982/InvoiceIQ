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
Classify this business document into exactly ONE category.

Allowed categories:
- SALES
- PURCHASE
- EXPENSE
- OTHER

Rules:

SALES:
A document where the business is selling goods or services.

PURCHASE:
A document where the business is buying goods or services from a supplier.

EXPENSE:
A business operating expense such as electricity, rent,
internet, travel, salary, office expenses, etc.

OTHER:
Use when the document cannot confidently be classified
as SALES, PURCHASE, or EXPENSE.

Return ONLY valid JSON in this exact format:

{{"document_type": "SALES"}}

Document:
{json.dumps(document_data, indent=2)}
"""

    with project.get_openai_client() as openai_client:

        response = openai_client.responses.create(
            model="gpt-5-mini",
            instructions=(
                "You are a strict business document classifier. "
                "Return only the requested JSON."
            ),
            input=prompt,
        )

    result = json.loads(response.output_text)

    document_type = result.get("document_type", "OTHER")

    allowed_types = {
        "SALES",
        "PURCHASE",
        "EXPENSE",
        "OTHER",
    }

    if document_type not in allowed_types:
        return "OTHER"

    return document_type