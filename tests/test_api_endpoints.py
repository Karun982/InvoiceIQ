import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from src.models import BusinessDocument, InvoiceItem

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy", "service": "InvoiceIQ"}


def test_api_documents_list():
    res = client.get("/api/documents")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) >= 2


def test_api_single_document():
    # Fetch first document from list
    res_list = client.get("/api/documents")
    docs = res_list.json()["documents"]
    doc_id = docs[0]["id"]

    res_single = client.get(f"/api/documents/{doc_id}")
    assert res_single.status_code == 200
    data = res_single.json()
    assert data["id"] == doc_id
    assert "items" in data
    assert isinstance(data["items"], list)


def test_api_analytics_summary():
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "revenue" in data
    assert "purchases" in data
    assert "net_balance" in data
    assert "sales_tax" in data
    assert "purchase_tax" in data
    assert "total_tax" in data
    assert data["revenue"] == 153400.0
    assert data["purchases"] == 336300.0
    assert data["net_balance"] == -182900.0
    assert data["sales_tax"] == 23400.0
    assert data["purchase_tax"] == 51300.0
    assert data["total_tax"] == 74700.0


def test_api_chat_endpoint_mocked():
    with patch("backend.main.ask_business_agent") as mock_ask:
        mock_ask.return_value = "Total sales are ₹1,53,400 with ₹23,400 in GST collected."

        res = client.post("/api/chat", json={"message": "What is my total sales?"})
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "₹1,53,400" in res.json()["answer"]


def test_api_upload_document_mocked(tmp_path):
    mock_doc = BusinessDocument(
        transaction_id="INV-API-TEST-99",
        document_type="SALES",
        party_name="API TEST CLIENT",
        transaction_date="14 November 2026",
        due_date="29 November 2026",
        subtotal=50000.0,
        tax=9000.0,
        is_tax_inferred=False,
        total_amount=59000.0,
        items=[
            InvoiceItem(description="Test Cloud Server", quantity=1, unit_price=50000, amount=50000)
        ],
    )

    with patch("backend.main.extract_invoice", return_value=mock_doc):
        dummy_file = ("test_invoice.pdf", b"%PDF-1.4 mock pdf content", "application/pdf")
        res = client.post(
            "/api/documents/upload",
            files={"file": dummy_file},
            data={"document_type": "SALES"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["document"]["transaction_id"] == "INV-API-TEST-99"
        assert data["document"]["total_amount"] == 59000.0

    # Clean up test upload so analytics tests remain pure
    from src.database import SessionLocal, DocumentDB
    db = SessionLocal()
    try:
        t_doc = db.query(DocumentDB).filter(DocumentDB.transaction_id == "INV-API-TEST-99").first()
        if t_doc:
            db.delete(t_doc)
            db.commit()
    finally:
        db.close()
