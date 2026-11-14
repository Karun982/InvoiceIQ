import pytest
from datetime import date, datetime
from typing import Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import BusinessDocument, InvoiceItem
from src.invoice_processor import (
    extract_invoice_from_fields,
    extract_line_items,
    extract_tax,
    normalize_date,
    normalize_number,
    clean_text,
    get_field_value,
)
from src.database import (
    Base,
    DocumentDB,
    InvoiceItemDB,
    save_document,
    get_all_documents,
    get_document_by_id,
)
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
from src.agent import build_agent_context, format_document


# =====================================================================
# MOCK HELPER OBJECTS
# =====================================================================

class MockDocumentField:
    """Mock DocumentField mimicking azure.ai.documentintelligence."""
    def __init__(
        self,
        value_string=None,
        value_number=None,
        value_date=None,
        value_currency=None,
        value_array=None,
        value_object=None,
        content=None,
    ):
        self.value_string = value_string
        self.value_number = value_number
        self.value_date = value_date
        self.value_currency = value_currency
        self.value_array = value_array
        self.value_object = value_object
        self.content = content


class MockCurrency:
    def __init__(self, amount, currency_code="INR"):
        self.amount = amount
        self.currency_code = currency_code


# =====================================================================
# 1. SALES INVOICE EXTRACTION TEST (INV-2026-1045)
# =====================================================================

def test_sales_invoice_extraction():
    mock_fields = {
        "InvoiceId": MockDocumentField(value_string="INV-2026-1045"),
        "CustomerName": MockDocumentField(value_string="TECHNOVA SOLUTIONS"),
        "InvoiceDate": MockDocumentField(value_date=date(2026, 11, 14)),
        "DueDate": MockDocumentField(value_date=date(2026, 11, 29)),
        "SubTotal": MockDocumentField(value_currency=MockCurrency(130000.0)),
        "TotalTax": MockDocumentField(value_currency=MockCurrency(23400.0)),
        "InvoiceTotal": MockDocumentField(value_currency=MockCurrency(153400.0)),
        "Items": MockDocumentField(
            value_array=[
                MockDocumentField(
                    value_object={
                        "Description": MockDocumentField(value_string="Business laptop workstation"),
                        "Quantity": MockDocumentField(value_number=2.0),
                        "UnitPrice": MockDocumentField(value_currency=MockCurrency(50000.0)),
                        "Amount": MockDocumentField(value_currency=MockCurrency(100000.0)),
                    }
                ),
                MockDocumentField(
                    value_object={
                        "Description": MockDocumentField(value_string="Network security appliance"),
                        "Quantity": MockDocumentField(value_number=1.0),
                        "UnitPrice": MockDocumentField(value_currency=MockCurrency(30000.0)),
                        "Amount": MockDocumentField(value_currency=MockCurrency(30000.0)),
                    }
                ),
            ]
        ),
    }

    doc = extract_invoice_from_fields(mock_fields, client_doc_type="SALES")

    assert doc.transaction_id == "INV-2026-1045"
    assert doc.document_type == "SALES"
    assert doc.party_name == "TECHNOVA SOLUTIONS"
    assert doc.transaction_date == "14 November 2026"
    assert doc.due_date == "29 November 2026"
    assert doc.subtotal == 130000.0
    assert doc.tax == 23400.0
    assert doc.is_tax_inferred is False
    assert doc.total_amount == 153400.0
    assert len(doc.items) == 2

    # Line Item 1
    assert doc.items[0].description == "Business laptop workstation"
    assert doc.items[0].quantity == 2.0
    assert doc.items[0].unit_price == 50000.0
    assert doc.items[0].amount == 100000.0

    # Line Item 2
    assert doc.items[1].description == "Network security appliance"
    assert doc.items[1].quantity == 1.0
    assert doc.items[1].unit_price == 30000.0
    assert doc.items[1].amount == 30000.0


# =====================================================================
# 2. PURCHASE INVOICE EXTRACTION TEST (PUR-2026-0872)
# =====================================================================

def test_purchase_invoice_extraction():
    mock_fields = {
        "InvoiceId": MockDocumentField(value_string="PUR-2026-0872"),
        "VendorName": MockDocumentField(value_string="ABC TECHNOLOGIES PVT. LTD."),
        "InvoiceDate": MockDocumentField(value_string="2026-11-14"),
        "DueDate": MockDocumentField(value_string="2026-11-29"),
        "SubTotal": MockDocumentField(value_currency=MockCurrency(285000.0)),
        "TotalTax": MockDocumentField(value_currency=MockCurrency(51300.0)),
        "InvoiceTotal": MockDocumentField(value_currency=MockCurrency(336300.0)),
        "Items": MockDocumentField(
            value_array=[
                MockDocumentField(
                    value_object={
                        "Description": MockDocumentField(value_string="Enterprise desktop computer"),
                        "Quantity": MockDocumentField(value_number=5.0),
                        "UnitPrice": MockDocumentField(value_currency=MockCurrency(45000.0)),
                        "Amount": MockDocumentField(value_currency=MockCurrency(225000.0)),
                    }
                ),
                MockDocumentField(
                    value_object={
                        "Description": MockDocumentField(value_string="Managed network switch"),
                        "Quantity": MockDocumentField(value_number=2.0),
                        "UnitPrice": MockDocumentField(value_currency=MockCurrency(30000.0)),
                        "Amount": MockDocumentField(value_currency=MockCurrency(60000.0)),
                    }
                ),
            ]
        ),
    }

    doc = extract_invoice_from_fields(mock_fields, client_doc_type="PURCHASE")

    assert doc.transaction_id == "PUR-2026-0872"
    assert doc.document_type == "PURCHASE"
    assert doc.party_name == "ABC TECHNOLOGIES PVT. LTD."
    assert doc.transaction_date == "14 November 2026"
    assert doc.due_date == "29 November 2026"
    assert doc.subtotal == 285000.0
    assert doc.tax == 51300.0
    assert doc.is_tax_inferred is False
    assert doc.total_amount == 336300.0
    assert len(doc.items) == 2

    assert doc.items[0].description == "Enterprise desktop computer"
    assert doc.items[0].quantity == 5.0
    assert doc.items[0].unit_price == 45000.0
    assert doc.items[0].amount == 225000.0

    assert doc.items[1].description == "Managed network switch"
    assert doc.items[1].quantity == 2.0
    assert doc.items[1].unit_price == 30000.0
    assert doc.items[1].amount == 60000.0


# =====================================================================
# 3, 4, 5, 6. LINE-ITEM DESCRIPTIONS, QUANTITIES, PRICES, AMOUNTS
# =====================================================================

def test_line_item_details_preservation():
    mock_items_field = {
        "Items": [
            {
                "Description": "Custom Software License - Tier 3",
                "Quantity": 10,
                "UnitPrice": 12500.50,
                "Amount": 125005.0,
            },
            {
                "Description": "Hardware Maintenance SLA (1 Year)",
                "Quantity": 1,
                "UnitPrice": 75000,
                "Amount": 75000,
            },
        ]
    }
    extracted = extract_line_items(mock_items_field)
    assert len(extracted) == 2
    assert extracted[0].description == "Custom Software License - Tier 3"
    assert extracted[0].quantity == 10.0
    assert extracted[0].unit_price == 12500.50
    assert extracted[0].amount == 125005.0

    assert extracted[1].description == "Hardware Maintenance SLA (1 Year)"
    assert extracted[1].quantity == 1.0
    assert extracted[1].unit_price == 75000.0
    assert extracted[1].amount == 75000.0


# =====================================================================
# 7. SUBTOTAL EXTRACTION & FALLBACK CALCULATION
# =====================================================================

def test_subtotal_extraction_and_fallback():
    # Direct subtotal present
    fields_with_subtotal = {
        "SubTotal": MockDocumentField(value_number=130000.0),
        "InvoiceTotal": MockDocumentField(value_number=153400.0),
    }
    doc1 = extract_invoice_from_fields(fields_with_subtotal)
    assert doc1.subtotal == 130000.0

    # Subtotal missing but line items present
    fields_without_subtotal = {
        "InvoiceTotal": MockDocumentField(value_number=153400.0),
        "Items": [
            {"Description": "Item A", "Amount": 100000.0},
            {"Description": "Item B", "Amount": 30000.0},
        ],
    }
    doc2 = extract_invoice_from_fields(fields_without_subtotal)
    assert doc2.subtotal == 130000.0


# =====================================================================
# 8. GST EXTRACTION (COMPONENTS, DOUBLE-COUNTING, INFERRED)
# =====================================================================

def test_gst_extraction_tax_items_component_sum():
    # CGST + SGST in TaxItems
    fields = {
        "TaxItems": [
            {"Amount": 11700.0, "Description": "CGST 9%"},
            {"Amount": 11700.0, "Description": "SGST 9%"},
        ],
        "SubTotal": 130000.0,
        "InvoiceTotal": 153400.0,
    }
    tax, is_inferred = extract_tax(fields, subtotal=130000.0, total_amount=153400.0)
    assert tax == 23400.0
    assert is_inferred is False


def test_gst_avoid_double_counting():
    # Both TotalTax (23400) and TaxItems (CGST 11700 + SGST 11700) exist
    fields = {
        "TotalTax": MockDocumentField(value_number=23400.0),
        "TaxItems": [
            {"Amount": 11700.0, "Description": "CGST"},
            {"Amount": 11700.0, "Description": "SGST"},
        ],
    }
    tax, is_inferred = extract_tax(fields)
    assert tax == 23400.0
    assert is_inferred is False


def test_gst_inferred_from_subtotal_and_total():
    # No tax fields in OCR, but total = 153400 and subtotal = 130000
    fields = {}
    tax, is_inferred = extract_tax(fields, subtotal=130000.0, total_amount=153400.0)
    assert tax == 23400.0
    assert is_inferred is True


def test_gst_missing_without_inference():
    # Both tax and totals missing
    fields = {}
    tax, is_inferred = extract_tax(fields, subtotal=None, total_amount=None)
    assert tax is None
    assert is_inferred is False


# =====================================================================
# 9, 10. DATE EXTRACTION & NORMALIZATION
# =====================================================================

def test_date_extraction_formats():
    assert normalize_date(date(2026, 11, 14)) == "14 November 2026"
    assert normalize_date(datetime(2026, 11, 14, 10, 30)) == "14 November 2026"
    assert normalize_date("2026-11-14") == "14 November 2026"
    assert normalize_date("14/11/2026") == "14 November 2026"
    assert normalize_date("14-11-2026") == "14 November 2026"
    assert normalize_date("November 14, 2026") == "14 November 2026"
    assert normalize_date(None) is None


def test_due_date_isolation_from_po_date():
    mock_fields = {
        "InvoiceDate": "2026-11-14",
        "DueDate": "2026-11-29",
        "PurchaseOrderDate": "2026-10-01",
        "DeliveryDate": "2026-11-20",
    }
    doc = extract_invoice_from_fields(mock_fields)
    assert doc.transaction_date == "14 November 2026"
    assert doc.due_date == "29 November 2026"


# =====================================================================
# 11, 12. DATABASE INSERTION & RETRIEVAL
# =====================================================================

def test_database_insertion_and_retrieval(tmp_path):
    test_db = tmp_path / "test_invoiceiq.db"
    test_engine = create_engine(f"sqlite:///{test_db}")
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Save Document
    db = TestingSessionLocal()
    doc_db = DocumentDB(
        transaction_id="INV-TEST-001",
        document_type="SALES",
        party_name="GLOBAL CORP",
        transaction_date="14 November 2026",
        due_date="29 November 2026",
        subtotal=100000.0,
        tax=18000.0,
        is_tax_inferred=False,
        total_amount=118000.0,
        currency="INR",
    )
    doc_db.items.append(
        InvoiceItemDB(
            description="Workstation Pro",
            quantity=2.0,
            unit_price=50000.0,
            amount=100000.0,
        )
    )
    db.add(doc_db)
    db.commit()
    db.refresh(doc_db)

    doc_id = doc_db.id
    db.close()

    # Retrieve Document
    db2 = TestingSessionLocal()
    retrieved = db2.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
    assert retrieved is not None
    assert retrieved.transaction_id == "INV-TEST-001"
    assert retrieved.party_name == "GLOBAL CORP"
    assert retrieved.subtotal == 100000.0
    assert retrieved.tax == 18000.0
    assert retrieved.is_tax_inferred is False
    assert len(retrieved.items) == 1
    assert retrieved.items[0].description == "Workstation Pro"
    db2.close()


# =====================================================================
# 13. CROSS-INVOICE FINANCIAL CALCULATIONS
# =====================================================================

def test_cross_invoice_financial_calculations():
    class DummyDoc:
        def __init__(self, doc_type, total, subtotal, tax):
            self.document_type = doc_type
            self.total_amount = total
            self.subtotal = subtotal
            self.tax = tax

    docs = [
        DummyDoc("SALES", 153400.0, 130000.0, 23400.0),
        DummyDoc("PURCHASE", 336300.0, 285000.0, 51300.0),
    ]

    total_sales = calculate_revenue(docs)
    total_purchases = calculate_purchases(docs)
    net_balance = calculate_net_balance(docs)
    sales_subtotal = calculate_sales_subtotal(docs)
    purchase_subtotal = calculate_purchase_subtotal(docs)
    sales_tax = calculate_sales_tax(docs)
    purchase_tax = calculate_purchase_tax(docs)
    combined_tax = calculate_total_tax(docs)

    assert total_sales == 153400.0
    assert total_purchases == 336300.0
    assert net_balance == -182900.0
    assert sales_subtotal == 130000.0
    assert purchase_subtotal == 285000.0
    assert sales_tax == 23400.0
    assert purchase_tax == 51300.0
    assert combined_tax == 74700.0


# =====================================================================
# 14. CORRECT AI CONTEXT CONSTRUCTION
# =====================================================================

def test_ai_context_construction():
    docs_payload = [
        {
            "id": 1,
            "transaction_id": "INV-2026-1045",
            "document_type": "SALES",
            "party_name": "TECHNOVA SOLUTIONS",
            "transaction_date": "14 November 2026",
            "due_date": "29 November 2026",
            "subtotal": 130000.0,
            "tax": 23400.0,
            "is_tax_inferred": False,
            "total_amount": 153400.0,
            "items": [
                {"description": "Business laptop workstation", "quantity": 2, "unit_price": 50000, "amount": 100000},
                {"description": "Network security appliance", "quantity": 1, "unit_price": 30000, "amount": 30000},
            ],
        },
        {
            "id": 2,
            "transaction_id": "PUR-2026-0872",
            "document_type": "PURCHASE",
            "party_name": "ABC TECHNOLOGIES PVT. LTD.",
            "transaction_date": "14 November 2026",
            "due_date": "29 November 2026",
            "subtotal": 285000.0,
            "tax": 51300.0,
            "is_tax_inferred": False,
            "total_amount": 336300.0,
            "items": [
                {"description": "Enterprise desktop computer", "quantity": 5, "unit_price": 45000, "amount": 225000},
                {"description": "Managed network switch", "quantity": 2, "unit_price": 30000, "amount": 60000},
            ],
        },
    ]

    context = build_agent_context(docs_payload)

    assert context["context_mode"] == "ALL UPLOADED INVOICES"
    summary = context["summary"]
    assert summary["total_sales_amount"] == 153400.0
    assert summary["total_purchases_amount"] == 336300.0
    assert summary["net_balance_sales_minus_purchases"] == -182900.0
    assert summary["total_tax_collected_on_sales"] == 23400.0
    assert summary["total_tax_paid_on_purchases"] == 51300.0
    assert summary["combined_tax"] == 74700.0
    assert len(context["sales_invoices"]) == 1
    assert len(context["purchase_invoices"]) == 1
    assert len(context["sales_invoices"][0]["items"]) == 2
    assert len(context["purchase_invoices"][0]["items"]) == 2


# =====================================================================
# 15. MISSING OR NULL OCR FIELDS
# =====================================================================

def test_missing_or_null_ocr_fields():
    # Empty fields dict
    empty_doc = extract_invoice_from_fields({})
    assert empty_doc.transaction_id is None
    assert empty_doc.party_name is None
    assert empty_doc.transaction_date is None
    assert empty_doc.due_date is None
    assert empty_doc.subtotal is None
    assert empty_doc.tax is None
    assert empty_doc.total_amount is None
    assert empty_doc.items == []


# =====================================================================
# 16. MULTIPLE INVOICES WITH DIFFERENT LINE-ITEM COUNTS
# =====================================================================

def test_multiple_invoices_with_different_line_item_counts():
    doc1_fields = {
        "InvoiceId": "INV-1",
        "Items": [
            {"Description": "Item 1", "Quantity": 1, "UnitPrice": 100, "Amount": 100},
        ],
    }
    doc2_fields = {
        "InvoiceId": "INV-2",
        "Items": [
            {"Description": "Item A", "Quantity": 2, "UnitPrice": 50, "Amount": 100},
            {"Description": "Item B", "Quantity": 1, "UnitPrice": 200, "Amount": 200},
            {"Description": "Item C", "Quantity": 3, "UnitPrice": 10, "Amount": 30},
        ],
    }

    doc1 = extract_invoice_from_fields(doc1_fields)
    doc2 = extract_invoice_from_fields(doc2_fields)

    assert len(doc1.items) == 1
    assert len(doc2.items) == 3
    assert doc1.items[0].description == "Item 1"
    assert [i.description for i in doc2.items] == ["Item A", "Item B", "Item C"]


import uuid

# =====================================================================
# 17. DUPLICATE INVOICE HANDLING
# =====================================================================

def test_duplicate_invoice_handling():
    unique_tx_id = f"INV-DUP-{uuid.uuid4().hex[:8]}"

    # First save
    initial_pydantic = BusinessDocument(
        transaction_id=unique_tx_id,
        document_type="SALES",
        party_name="Initial Vendor",
        transaction_date="01 October 2026",
        subtotal=1000.0,
        tax=180.0,
        total_amount=1180.0,
        items=[InvoiceItem(description="Old Item", quantity=1, unit_price=1000, amount=1000)],
    )
    saved_doc, is_new = save_document(initial_pydantic)
    assert is_new is True

    # Duplicate re-upload with updated correct items
    updated_pydantic = BusinessDocument(
        transaction_id=unique_tx_id,
        document_type="SALES",
        party_name="Updated Client",
        transaction_date="14 November 2026",
        subtotal=2000.0,
        tax=360.0,
        total_amount=2360.0,
        items=[
            InvoiceItem(description="New Item 1", quantity=1, unit_price=1500, amount=1500),
            InvoiceItem(description="New Item 2", quantity=1, unit_price=500, amount=500),
        ],
    )
    updated_doc, is_new2 = save_document(updated_pydantic, update_existing=True)

    assert is_new2 is False  # Correctly identifies duplicate
    assert updated_doc.id == saved_doc.id  # Same document record
    assert updated_doc.party_name == "Updated Client"
    assert updated_doc.transaction_date == "14 November 2026"
    assert updated_doc.subtotal == 2000.0
    assert updated_doc.tax == 360.0
    assert len(updated_doc.items) == 2
    assert updated_doc.items[0].description == "New Item 1"

    # Clean up test record
    from src.database import SessionLocal, DocumentDB
    db = SessionLocal()
    try:
        t_doc = db.query(DocumentDB).filter(DocumentDB.transaction_id == unique_tx_id).first()
        if t_doc:
            db.delete(t_doc)
            db.commit()
    finally:
        db.close()


# =====================================================================
# REGRESSION TEST: FULL TWO SAMPLE INVOICES SPECIFICATION
# =====================================================================

def test_regression_two_sample_invoices_exact_metrics():
    """
    Exact regression verification from Prompt Section 4:
    Expected results:
    Metric           | Expected
    -----------------|----------
    Total Sales      | ₹1,53,400
    Total Purchases  | ₹3,36,300
    Net Balance      | -₹1,82,900
    Sales Subtotal   | ₹1,30,000
    Purchase Subtotal| ₹2,85,000
    Sales GST        | ₹23,400
    Purchase GST     | ₹51,300
    Combined GST     | ₹74,700

    Expected sales line items: 2.
    Expected purchase line items: 2.
    Expected invoice date for both: 14 November 2026.
    Expected due date for both: 29 November 2026.
    """
    sales_mock = {
        "InvoiceId": "INV-2026-1045",
        "CustomerName": "TECHNOVA SOLUTIONS",
        "InvoiceDate": "14 November 2026",
        "DueDate": "29 November 2026",
        "SubTotal": 130000.0,
        "TotalTax": 23400.0,
        "InvoiceTotal": 153400.0,
        "Items": [
            {"Description": "Business laptop workstation", "Quantity": 2, "UnitPrice": 50000, "Amount": 100000},
            {"Description": "Network security appliance", "Quantity": 1, "UnitPrice": 30000, "Amount": 30000},
        ],
    }

    purchase_mock = {
        "InvoiceId": "PUR-2026-0872",
        "VendorName": "ABC TECHNOLOGIES PVT. LTD.",
        "InvoiceDate": "14 November 2026",
        "DueDate": "29 November 2026",
        "SubTotal": 285000.0,
        "TotalTax": 51300.0,
        "InvoiceTotal": 336300.0,
        "Items": [
            {"Description": "Enterprise desktop computer", "Quantity": 5, "UnitPrice": 45000, "Amount": 225000},
            {"Description": "Managed network switch", "Quantity": 2, "UnitPrice": 30000, "Amount": 60000},
        ],
    }

    sales_doc = extract_invoice_from_fields(sales_mock, client_doc_type="SALES")
    purchase_doc = extract_invoice_from_fields(purchase_mock, client_doc_type="PURCHASE")

    # Dates verification
    assert sales_doc.transaction_date == "14 November 2026"
    assert sales_doc.due_date == "29 November 2026"
    assert purchase_doc.transaction_date == "14 November 2026"
    assert purchase_doc.due_date == "29 November 2026"

    # Line items verification
    assert len(sales_doc.items) == 2
    assert sales_doc.items[0].description == "Business laptop workstation"
    assert sales_doc.items[0].quantity == 2.0
    assert sales_doc.items[0].unit_price == 50000.0
    assert sales_doc.items[0].amount == 100000.0

    assert sales_doc.items[1].description == "Network security appliance"
    assert sales_doc.items[1].quantity == 1.0
    assert sales_doc.items[1].unit_price == 30000.0
    assert sales_doc.items[1].amount == 30000.0

    assert len(purchase_doc.items) == 2
    assert purchase_doc.items[0].description == "Enterprise desktop computer"
    assert purchase_doc.items[0].quantity == 5.0
    assert purchase_doc.items[0].unit_price == 45000.0
    assert purchase_doc.items[0].amount == 225000.0

    assert purchase_doc.items[1].description == "Managed network switch"
    assert purchase_doc.items[1].quantity == 2.0
    assert purchase_doc.items[1].unit_price == 30000.0
    assert purchase_doc.items[1].amount == 60000.0

    # Cross-document calculations
    all_documents = [sales_doc, purchase_doc]
    assert calculate_revenue(all_documents) == 153400.0
    assert calculate_purchases(all_documents) == 336300.0
    assert calculate_net_balance(all_documents) == -182900.0
    assert calculate_sales_subtotal(all_documents) == 130000.0
    assert calculate_purchase_subtotal(all_documents) == 285000.0
    assert calculate_sales_tax(all_documents) == 23400.0
    assert calculate_purchase_tax(all_documents) == 51300.0
    assert calculate_total_tax(all_documents) == 74700.0


# =====================================================================
# REGRESSION TEST: PURCHASE INVOICE PUR-2026-0872 OCR ANOMALY RECONCILIATION
# =====================================================================

def test_purchase_invoice_raw_ocr_anomaly_reconciliation():
    """
    Regression test for PUR-2026-0872 where raw Azure Document Intelligence
    OCR extracted the second line item amount as ₹1,60,000 (OCR misread
    table border '|' or rupee symbol '₹' as leading digit '1').

    Verifies:
    1. Quantity = 2, Unit Price = ₹30,000.
    2. Raw OCR amount is preserved as 160000 in raw_ocr_amount.
    3. Pipeline reconciles second line-item amount to expected ₹60,000
       matching subtotal (₹2,85,000) and quantity × unit price.
    4. Inconsistency is flagged (is_inconsistent = True) with clear note.
    5. Subtotal remains ₹2,85,000 and total remains ₹3,36,300.
    6. When formatted for AI agent, items[1]['amount'] == 60000.0.
    """
    mock_purchase_with_ocr_anomaly = {
        "InvoiceId": "PUR-2026-0872",
        "VendorName": "ABC TECHNOLOGIES PVT. LTD.",
        "InvoiceDate": "14 November 2026",
        "DueDate": "29 November 2026",
        "SubTotal": 285000.0,
        "TotalTax": 51300.0,
        "InvoiceTotal": 336300.0,
        "Items": [
            {
                "Description": "Enterprise desktop computer",
                "Quantity": 5,
                "UnitPrice": 45000,
                "Amount": 225000,
            },
            {
                "Description": "Managed network switch",
                "Quantity": 2,
                "UnitPrice": 30000,
                # Raw OCR anomaly: ₹1,60,000 instead of ₹60,000
                "Amount": 160000,
            },
        ],
    }

    doc = extract_invoice_from_fields(mock_purchase_with_ocr_anomaly, client_doc_type="PURCHASE")

    # Document-level checks
    assert doc.transaction_id == "PUR-2026-0872"
    assert doc.subtotal == 285000.0
    assert doc.total_amount == 336300.0
    assert len(doc.items) == 2

    # Line item 1
    assert doc.items[0].description == "Enterprise desktop computer"
    assert doc.items[0].quantity == 5.0
    assert doc.items[0].unit_price == 45000.0
    assert doc.items[0].amount == 225000.0
    assert doc.items[0].is_inconsistent is False

    # Line item 2: Expected second line-item amount: ₹60,000
    assert doc.items[1].description == "Managed network switch"
    assert doc.items[1].quantity == 2.0
    assert doc.items[1].unit_price == 30000.0
    assert doc.items[1].amount == 60000.0
    assert doc.items[1].raw_ocr_amount == 160000.0
    assert doc.items[1].is_inconsistent is True
    assert "reconciled to actual invoice value" in doc.items[1].inconsistency_note

    # AI context representation check
    ai_formatted = format_document(doc)
    assert ai_formatted["items"][1]["amount"] == 60000.0
    assert ai_formatted["items"][1]["raw_ocr_amount"] == 160000.0
    assert ai_formatted["items"][1]["is_inconsistent"] is True
