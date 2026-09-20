from src.invoice_processor import extract_invoice


file_path = "data/invoices/test-invoice.pdf"

invoice = extract_invoice(file_path)

print("\nStructured BusinessDocument:")
print(invoice.model_dump())