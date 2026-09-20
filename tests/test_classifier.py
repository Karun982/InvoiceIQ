from src.invoice_processor import extract_invoice
from src.classifier import classify_document


file_path = "data/invoices/test-invoice.pdf"

document = extract_invoice(file_path)

print("Before classification:")
print(document.model_dump())

document.document_type = classify_document(document)

print("\nAfter classification:")
print(document.model_dump())