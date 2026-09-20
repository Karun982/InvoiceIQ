from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError


DATABASE_URL = "sqlite:///./invoiceiq.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(String, unique=True, index=True)
    document_type = Column(String, index=True)
    party_name = Column(String)

    transaction_date = Column(String)
    due_date = Column(String)

    subtotal = Column(Float)
    tax = Column(Float)
    total_amount = Column(Float)

    currency = Column(String)
    payment_status = Column(String)

    items = relationship(
        "InvoiceItemDB",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class InvoiceItemDB(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
    )

    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    amount = Column(Float)

    document = relationship(
        "DocumentDB",
        back_populates="items",
    )


def init_db():
    Base.metadata.create_all(bind=engine)


def get_all_documents():
    db = SessionLocal()

    try:
        return (
            db.query(DocumentDB)
            .order_by(DocumentDB.id.desc())
            .all()
        )
    finally:
        db.close()


def get_document_by_id(document_id):
    db = SessionLocal()

    try:
        return (
            db.query(DocumentDB)
            .filter(DocumentDB.id == document_id)
            .first()
        )
    finally:
        db.close()


def save_document(document):

    db = SessionLocal()

    try:

        # Check whether document already exists
        existing_document = (
            db.query(DocumentDB)
            .filter(
                DocumentDB.transaction_id == document.transaction_id
            )
            .first()
        )

        if existing_document:
            return existing_document, False


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


        for item in document.items:

            db_item = InvoiceItemDB(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
            )

            db_document.items.append(db_item)


        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return db_document, True


    except Exception:

        db.rollback()
        raise


    finally:

        db.close()

def get_all_documents():
    db = SessionLocal()

    try:
        return (
            db.query(DocumentDB)
            .order_by(DocumentDB.id.desc())
            .all()
        )
    finally:
        db.close()


def get_document_by_id(document_id):
    db = SessionLocal()

    try:
        return (
            db.query(DocumentDB)
            .filter(DocumentDB.id == document_id)
            .first()
        )
    finally:
        db.close()