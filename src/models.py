from pydantic import BaseModel
from typing import Optional, List


class InvoiceItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class BusinessDocument(BaseModel):
    transaction_id: Optional[str] = None
    document_type: str
    party_name: Optional[str] = None
    transaction_date: Optional[str] = None
    due_date: Optional[str] = None

    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None

    currency: Optional[str] = None
    payment_status: Optional[str] = None

    items: List[InvoiceItem] = []