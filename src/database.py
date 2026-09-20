from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
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


    document = relationship(
        "DocumentDB",
        back_populates="items",
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )


# =========================================================
# SAVE DOCUMENT
# =========================================================

def save_document(document):

    db = SessionLocal()

    try:

        existing_document = (
            db.query(DocumentDB)
            .filter(
                DocumentDB.transaction_id
                == document.transaction_id
            )
            .first()
        )


        # -------------------------------------------------
        # DUPLICATE DOCUMENT
        # -------------------------------------------------

        if existing_document:

            return existing_document, False


        # -------------------------------------------------
        # CREATE DOCUMENT
        # -------------------------------------------------

        db_document = DocumentDB(

            transaction_id=document.transaction_id,

            document_type=document.document_type,

            party_name=document.party_name,

            transaction_date=document.transaction_date,

            due_date=document.due_date,

            subtotal=document.subtotal,

            tax=document.tax,

            total_amount=document.total_amount,

            currency=document.currency,

            payment_status=document.payment_status,

        )


        # -------------------------------------------------
        # SAVE ITEMS
        # -------------------------------------------------

        for item in document.items:

            db_item = InvoiceItemDB(

                description=item.description,

                quantity=item.quantity,

                unit_price=item.unit_price,

                amount=item.amount,

            )

            db_document.items.append(
                db_item
            )


        db.add(
            db_document
        )

        db.commit()

        db.refresh(
            db_document
        )


        return db_document, True


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


# =========================================================
# GET ALL DOCUMENTS
# =========================================================

def get_all_documents():

    db = SessionLocal()

    try:

        return (
            db.query(DocumentDB)
            .order_by(
                DocumentDB.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# =========================================================
# GET DOCUMENT BY ID
# =========================================================

def get_document_by_id(document_id):
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

    db = SessionLocal()

    try:

        return (
            db.query(DocumentDB)
            .filter(
                DocumentDB.id
                == document_id
            )
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

        # Delete child records first.
        db.query(
            InvoiceItemDB
        ).delete(
            synchronize_session=False
        )


        # Delete documents.
        db.query(
            DocumentDB
        ).delete(
            synchronize_session=False
        )


        db.commit()


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()