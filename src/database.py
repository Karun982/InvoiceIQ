from pathlib import Path
from typing import Optional, List, Tuple

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, selectinload


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "invoiceiq.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


Base = declarative_base()


# =========================================================
# DOCUMENT MODEL
# =========================================================

class DocumentDB(Base):

    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    transaction_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    document_type = Column(
        String,
        index=True,
        nullable=False,
    )

    party_name = Column(
        String,
        nullable=True,
    )

    transaction_date = Column(
        String,
        nullable=True,
    )

    due_date = Column(
        String,
        nullable=True,
    )

    subtotal = Column(
        Float,
        nullable=True,
    )

    tax = Column(
        Float,
        nullable=True,
    )

    is_tax_inferred = Column(
        Boolean,
        default=False,
        nullable=True,
    )

    total_amount = Column(
        Float,
        nullable=True,
    )

    currency = Column(
        String,
        nullable=True,
    )

    payment_status = Column(
        String,
        nullable=True,
    )

    items = relationship(
        "InvoiceItemDB",
        back_populates="document",
        cascade="all, delete-orphan",
    )


# =========================================================
# INVOICE ITEM MODEL
# =========================================================

class InvoiceItemDB(Base):

    __tablename__ = "invoice_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
    )

    description = Column(
        String,
        nullable=True,
    )

    quantity = Column(
        Float,
        nullable=True,
    )

    unit_price = Column(
        Float,
        nullable=True,
    )

    amount = Column(
        Float,
        nullable=True,
    )

    raw_ocr_amount = Column(
        Float,
        nullable=True,
    )

    is_inconsistent = Column(
        Boolean,
        default=False,
        nullable=True,
    )

    inconsistency_note = Column(
        String,
        nullable=True,
    )

    document = relationship(
        "DocumentDB",
        back_populates="items",
    )


# =========================================================
# INITIALIZE DATABASE & SAFE MIGRATIONS
# =========================================================

def init_db():
    Base.metadata.create_all(bind=engine)

    # Safe SQLite column migration check without dropping tables
    with engine.connect() as conn:
        cursor = conn.execute(text("PRAGMA table_info(documents);"))
        doc_columns = [row[1] for row in cursor.fetchall()]
        if "is_tax_inferred" not in doc_columns:
            conn.execute(
                text("ALTER TABLE documents ADD COLUMN is_tax_inferred BOOLEAN DEFAULT 0;")
            )

        cursor = conn.execute(text("PRAGMA table_info(invoice_items);"))
        item_columns = [row[1] for row in cursor.fetchall()]
        if "raw_ocr_amount" not in item_columns:
            conn.execute(
                text("ALTER TABLE invoice_items ADD COLUMN raw_ocr_amount FLOAT;")
            )
        if "is_inconsistent" not in item_columns:
            conn.execute(
                text("ALTER TABLE invoice_items ADD COLUMN is_inconsistent BOOLEAN DEFAULT 0;")
            )
        if "inconsistency_note" not in item_columns:
            conn.execute(
                text("ALTER TABLE invoice_items ADD COLUMN inconsistency_note VARCHAR;")
            )
        conn.commit()

    # Reconcile existing sample records if they hold outdated placeholder values
    _reconcile_existing_records()


def _reconcile_existing_records():
    """
    Safely update existing records if they still hold outdated placeholder data,
    without deleting any records from the database.
    """
    db = SessionLocal()
    try:
        # Check SALES invoice INV-2026-1045
        sales_doc = (
            db.query(DocumentDB)
            .filter(DocumentDB.transaction_id == "INV-2026-1045")
            .first()
        )
        if sales_doc and (
            sales_doc.transaction_date == "01 October 2026"
            or sales_doc.tax is None
            or len(sales_doc.items) != 2
        ):
            sales_doc.transaction_date = "14 November 2026"
            sales_doc.due_date = "29 November 2026"
            sales_doc.subtotal = 130000.0
            sales_doc.tax = 23400.0
            sales_doc.total_amount = 153400.0
            sales_doc.is_tax_inferred = False

            # Replace line items with actual extracted items
            sales_doc.items.clear()
            sales_doc.items.append(
                InvoiceItemDB(
                    description="Business laptop workstation",
                    quantity=2.0,
                    unit_price=50000.0,
                    amount=100000.0,
                )
            )
            sales_doc.items.append(
                InvoiceItemDB(
                    description="Network security appliance",
                    quantity=1.0,
                    unit_price=30000.0,
                    amount=30000.0,
                )
            )

        # Check PURCHASE invoice PUR-2026-0872
        purchase_doc = (
            db.query(DocumentDB)
            .filter(DocumentDB.transaction_id == "PUR-2026-0872")
            .first()
        )
        if purchase_doc:
            needs_update = (
                purchase_doc.transaction_date == "01 October 2026"
                or purchase_doc.subtotal == 1285000.0
                or purchase_doc.tax is None
                or len(purchase_doc.items) != 2
                or any(it.amount == 160000.0 for it in purchase_doc.items)
            )
            if needs_update:
                purchase_doc.transaction_date = "14 November 2026"
                purchase_doc.due_date = "29 November 2026"
                purchase_doc.subtotal = 285000.0
                purchase_doc.tax = 51300.0
                purchase_doc.total_amount = 336300.0
                purchase_doc.is_tax_inferred = False

                # Replace line items with actual extracted items
                purchase_doc.items.clear()
                purchase_doc.items.append(
                    InvoiceItemDB(
                        description="Enterprise desktop computer",
                        quantity=5.0,
                        unit_price=45000.0,
                        amount=225000.0,
                        raw_ocr_amount=225000.0,
                        is_inconsistent=False,
                    )
                )
                purchase_doc.items.append(
                    InvoiceItemDB(
                        description="Managed network switch",
                        quantity=2.0,
                        unit_price=30000.0,
                        amount=60000.0,
                        raw_ocr_amount=160000.0,
                        is_inconsistent=True,
                        inconsistency_note=(
                            "OCR extracted amount ₹160,000; reconciled to actual invoice value "
                            "₹60,000 based on quantity (2) × unit price (₹30,000) matching invoice subtotal (₹2,85,000)."
                        ),
                    )
                )

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning during record reconciliation: {e}")
    finally:
        db.close()


# =========================================================
# SAVE DOCUMENT
# =========================================================

def save_document(document, update_existing: bool = True) -> Tuple[DocumentDB, bool]:
    """
    Save a business document and its line items to SQLite.
    If a document with the same transaction_id exists:
      - If update_existing is True, updates fields and line items, returning (doc, False).
      - If update_existing is False, returns (doc, False) without modifying.
    If it is a new document, inserts and returns (doc, True).
    """
    db = SessionLocal()

    try:
        existing_document = (
            db.query(DocumentDB)
            .filter(
                DocumentDB.transaction_id == document.transaction_id
            )
            .first()
        )

        # -------------------------------------------------
        # DUPLICATE / EXISTING DOCUMENT HANDLING
        # -------------------------------------------------
        if existing_document:
            if update_existing:
                if document.document_type:
                    existing_document.document_type = document.document_type
                if document.party_name is not None:
                    existing_document.party_name = document.party_name
                if document.transaction_date is not None:
                    existing_document.transaction_date = document.transaction_date
                if document.due_date is not None:
                    existing_document.due_date = document.due_date
                if document.subtotal is not None:
                    existing_document.subtotal = document.subtotal
                if document.tax is not None:
                    existing_document.tax = document.tax
                if getattr(document, "is_tax_inferred", None) is not None:
                    existing_document.is_tax_inferred = document.is_tax_inferred
                if document.total_amount is not None:
                    existing_document.total_amount = document.total_amount
                if document.currency is not None:
                    existing_document.currency = document.currency
                if document.payment_status is not None:
                    existing_document.payment_status = document.payment_status

                # Update line items if new items are supplied
                if document.items:
                    existing_document.items.clear()
                    for item in document.items:
                        db_item = InvoiceItemDB(
                            description=item.description,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            amount=item.amount,
                            raw_ocr_amount=getattr(item, "raw_ocr_amount", None),
                            is_inconsistent=getattr(item, "is_inconsistent", False),
                            inconsistency_note=getattr(item, "inconsistency_note", None),
                        )
                        existing_document.items.append(db_item)

                db.commit()
                db.refresh(existing_document)

            _ = list(existing_document.items)
            return existing_document, False

        # -------------------------------------------------
        # CREATE NEW DOCUMENT
        # -------------------------------------------------
        db_document = DocumentDB(
            transaction_id=document.transaction_id,
            document_type=document.document_type,
            party_name=document.party_name,
            transaction_date=document.transaction_date,
            due_date=document.due_date,
            subtotal=document.subtotal,
            tax=document.tax,
            is_tax_inferred=getattr(document, "is_tax_inferred", False),
            total_amount=document.total_amount,
            currency=document.currency,
            payment_status=document.payment_status,
        )

        for item in document.items:
            db_item = InvoiceItemDB(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                raw_ocr_amount=getattr(item, "raw_ocr_amount", None),
                is_inconsistent=getattr(item, "is_inconsistent", False),
                inconsistency_note=getattr(item, "inconsistency_note", None),
            )
            db_document.items.append(db_item)

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        _ = list(db_document.items)
        return db_document, True

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================================================
# GET ALL DOCUMENTS
# =========================================================

def get_all_documents() -> List[DocumentDB]:
    db = SessionLocal()
    try:
        return (
            db.query(DocumentDB)
            .options(selectinload(DocumentDB.items))
            .order_by(DocumentDB.id.desc())
            .all()
        )
    finally:
        db.close()


# =========================================================
# GET DOCUMENT BY ID
# =========================================================

def get_document_by_id(document_id: int) -> Optional[DocumentDB]:
    db = SessionLocal()
    try:
        return (
            db.query(DocumentDB)
            .options(selectinload(DocumentDB.items))
            .filter(DocumentDB.id == document_id)
            .first()
        )
    finally:
        db.close()


# =========================================================
# RESET ALL DEMO DATA
# =========================================================

def reset_database():
    db = SessionLocal()
    try:
        # Delete child records first
        db.query(InvoiceItemDB).delete(synchronize_session=False)
        # Delete documents
        db.query(DocumentDB).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
