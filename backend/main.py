import os
import shutil
import tempfile

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from src.agent import ask_business_agent

from src.invoice_processor import extract_invoice

from src.classifier import classify_document

from src.database import (
    init_db,
    save_document,
    get_all_documents,
    get_document_by_id,
    reset_database,
)

from src.analytics import (
    calculate_revenue,
    calculate_purchases,
    calculate_expenses,
    calculate_estimated_profit,
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="InvoiceIQ API",
    description=(
        "AI-powered invoice processing "
        "and business analytics API"
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():
    init_db()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "InvoiceIQ API is running",
        "status": "online",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "InvoiceIQ",
    }


# =========================================================
# DOCUMENT UPLOAD
# =========================================================

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    allowed_extensions = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
    }

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF, PNG, JPG, "
                "and JPEG files are supported."
            ),
        )

    temp_path = None

    try:

        # -------------------------------------------------
        # CREATE TEMPORARY FILE
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            shutil.copyfileobj(
                file.file,
                temp_file
            )

            temp_path = temp_file.name

        # -------------------------------------------------
        # STEP 1
        # AZURE DOCUMENT INTELLIGENCE
        # -------------------------------------------------

        document = extract_invoice(
            temp_path
        )

        # -------------------------------------------------
        # STEP 2
        # GPT-5-MINI CLASSIFICATION
        # -------------------------------------------------

        document.document_type = (
            classify_document(document)
        )

        # -------------------------------------------------
        # STEP 3
        # SAVE TO SQLITE
        # -------------------------------------------------

        saved_document, is_new = (
            save_document(document)
        )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return {
            "success": True,

            "message": (
                "Document processed "
                "and saved successfully."
                if is_new
                else
                "Document already exists "
                "in the database."
            ),

            "duplicate": not is_new,

            "document": {
                "id": saved_document.id,
                "transaction_id":
                    saved_document.transaction_id,
                "document_type":
                    saved_document.document_type,
                "party_name":
                    saved_document.party_name,
                "transaction_date":
                    saved_document.transaction_date,
                "due_date":
                    saved_document.due_date,
                "subtotal":
                    saved_document.subtotal,
                "tax":
                    saved_document.tax,
                "total_amount":
                    saved_document.total_amount,
                "currency":
                    saved_document.currency,
                "payment_status":
                    saved_document.payment_status,
            },
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document processing failed: {str(e)}"
            ),
        )

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):
            os.remove(temp_path)


# =========================================================
# GET ALL DOCUMENTS
# =========================================================

@app.get("/api/documents")
def get_documents():

    documents = get_all_documents()

    return {
        "success": True,

        "documents": [
            {
                "id": doc.id,
                "transaction_id":
                    doc.transaction_id,
                "document_type":
                    doc.document_type,
                "party_name":
                    doc.party_name,
                "transaction_date":
                    doc.transaction_date,
                "due_date":
                    doc.due_date,
                "subtotal":
                    doc.subtotal,
                "tax":
                    doc.tax,
                "total_amount":
                    doc.total_amount,
                "currency":
                    doc.currency,
                "payment_status":
                    doc.payment_status,
            }
            for doc in documents
        ],
    }


# =========================================================
# GET SINGLE DOCUMENT
# =========================================================

@app.get("/api/documents/{document_id}")
def get_document_details(document_id: int):

    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "id": document.id,
        "transaction_id": document.transaction_id,
        "document_type": document.document_type,
        "party_name": document.party_name,
        "transaction_date": document.transaction_date,
        "due_date": document.due_date,
        "subtotal": document.subtotal,
        "tax": document.tax,
        "total_amount": document.total_amount,
        "currency": document.currency,
        "payment_status": document.payment_status,

        "items": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
            }
            for item in document.items
        ],
    }


# =========================================================
# ANALYTICS
# =========================================================

@app.get("/api/analytics/summary")
def analytics_summary():

    documents = get_all_documents()

    return {
        "success": True,

        "revenue":
            calculate_revenue(
                documents
            ),

        "purchases":
            calculate_purchases(
                documents
            ),

        "expenses":
            calculate_expenses(
                documents
            ),

        "estimated_profit":
            calculate_estimated_profit(
                documents
            ),

        "document_count":
            len(documents),
    }


# =========================================================
# RESET DEMO DATA
# =========================================================

@app.post("/api/reset")
def reset_demo_data():

    try:

        reset_database()

        return {
            "success": True,
            "message":
                "All demo data has been reset successfully.",
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}",
        )


# =========================================================
# AI INVOICE CHAT
# =========================================================

class ChatRequest(BaseModel):

    message: str

    document_id: int


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        document = get_document_by_id(request.document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Selected invoice not found.",
            )

        answer = ask_business_agent(
            request.message,
            request.document_id,
        )

        return {
            "success": True,
            "answer": answer,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}",
        )