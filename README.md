# InvoiceIQ — AI-Powered Invoice Processing & Financial Assistant

InvoiceIQ is an end-to-end invoice extraction, structured storage, and AI-driven document intelligence system. It combines **Azure AI Document Intelligence** for high-precision OCR and invoice parsing, a **FastAPI** backend with **SQLite/SQLAlchemy** for data persistence, and an **LLM-powered conversational agent** (via Azure AI Foundry / OpenAI) to answer natural-language questions about uploaded invoices.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Directory Structure](#project-directory-structure)
- [Prerequisites](#prerequisites)
- [Local Setup & Installation](#local-setup--installation)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Create and Activate Virtual Environment](#2-create-and-activate-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
- [Running the Application](#running-the-application)
  - [Start Backend Server](#start-backend-server)
  - [Serve the Frontend](#serve-the-frontend)
- [API Documentation & Endpoints](#api-documentation--endpoints)
- [Database Schema](#database-schema)
- [AI Invoice Assistant Workflow](#ai-invoice-assistant-workflow)
- [Troubleshooting & Common Issues](#troubleshooting--common-issues)
- [License](#license)

---

## System Architecture

```text
                               ┌────────────────────────┐
                               │     User / Browser     │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
                    ▼                                             ▼
        [ Document Upload Page ]                      [ AI Assistant Chat ]
         frontend/upload.html                          frontend/chat.html
                    │                                             │
                    │ POST /api/documents/upload                  │ POST /api/chat
                    ▼                                             ▼
       ┌──────────────────────────────────────────────────────────────────┐
       │                       FastAPI Application                        │
       │                        (backend/main.py)                         │
       └────────────┬─────────────────────────────┬───────────────────────┘
                    │                             │
                    ▼                             ▼
        [ Azure Document Intelligence ]    [ Azure AI Foundry / OpenAI ]
            src/invoice_processor.py                 src/agent.py
                    │                                     │
                    ▼                                     │
        [ Document Extraction & Items ]                   │
                    │                                     │
                    ▼                                     │
          [ SQLite Database ] ◄───────────────────────────┘
             src/database.py
           (invoiceiq.db)
```

---

## Key Features

1. **Multi-Format Document Upload**:
   - Supports single or batch upload for `.pdf`, `.png`, `.jpg`, and `.jpeg` invoices.
   - Drag-and-drop zone with real-time file validation and queue management.

2. **Explicit Invoice Categorization**:
   - Users choose the invoice type before or during upload:
     - ↗ **Sales Invoice**: Money earned from customers / sales revenue.
     - ↓ **Purchase Invoice**: Goods, materials, or services bought from suppliers/vendors.
   - Provides per-file classification overrides for mixed-batch uploads.

3. **Automated Data Extraction**:
   - Uses Azure AI Document Intelligence's `prebuilt-invoice` model.
   - Extracts vendor name, invoice/transaction ID, invoice date, due date, subtotal, tax, total amount, currency, and line items (descriptions, quantities, unit prices, amounts).

4. **Relational Data Persistence**:
   - Automatically stores documents and nested line items in a local SQLite database (`invoiceiq.db`) using SQLAlchemy ORM.
   - Handles deduplication by transaction ID with dynamic type updates.

5. **Context-Aware AI Invoice Assistant**:
   - Users can chat directly with an AI assistant focused strictly on the selected invoice.
   - System prompts constrain the model to the active document's contents and respect whether the invoice was marked as a Sales or Purchase transaction.

6. **Responsive UI with Dark/Light Mode**:
   - Clean, lightweight vanilla HTML/CSS/JS frontend without heavyweight framework dependencies.
   - Theme toggle persisted via `localStorage`.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Database & ORM** | SQLite, SQLAlchemy 2.0 |
| **Document Intelligence** | Azure AI Document Intelligence SDK (`azure-ai-documentintelligence`) |
| **AI / LLM** | OpenAI Python SDK connected to Azure AI Foundry (`gpt-5-mini` model) |
| **Frontend** | Semantic HTML5, Modern CSS3 (Variables, Flexbox, Grid), Vanilla JavaScript (ES6+) |

---

## Project Directory Structure

```text
InvoiceIQ/
├── backend/
│   ├── __init__.py
│   └── main.py                 # FastAPI API routes, CORS, and server startup
├── frontend/
│   ├── css/
│   │   └── style.css           # Global stylesheet (themes, layout, upload UI)
│   ├── js/
│   │   ├── chat.js             # AI chat interface client logic
│   │   ├── theme.js            # Dark/light theme switcher
│   │   └── upload.js           # Multi-file upload, type selection, API caller
│   ├── chat.html               # AI Invoice Assistant chat page
│   ├── index.html              # Marketing / landing page
│   └── upload.html             # Document upload & invoice classification page
├── src/
│   ├── __init__.py
│   ├── agent.py                # AI conversational agent configuration & prompts
│   ├── analytics.py            # Revenue, purchase, and profit calculation helpers
│   ├── classifier.py           # Fallback automated document classifier
│   ├── database.py             # SQLAlchemy models, SQLite session, and DB queries
│   ├── invoice_processor.py    # Azure AI Document Intelligence integration
│   └── models.py               # Pydantic data schemas
├── data/
│   └── invoices/               # Sample invoices for local testing
├── tests/
│   ├── test_classifier.py      # Classifier unit tests
│   └── test_document_intelligence.py
├── .env.example                # Template for required environment variables
├── invoiceiq.db                # SQLite database (auto-generated on first run)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## Prerequisites

Before running the project, ensure you have:

1. **Python 3.10 or higher** installed (`python3 --version`).
2. An active **Azure Account** with:
   - **Azure AI Document Intelligence** resource (Endpoint URL and API Key).
   - **Azure AI Foundry / OpenAI** resource with a deployed model (Endpoint URL and API Key).
3. A local static web server or the **VS Code Live Server** extension to serve the frontend.

---

## Local Setup & Installation

### 1. Clone Repository

```bash
git clone https://github.com/Karun982/InvoiceIQ.git
cd InvoiceIQ
```

### 2. Create and Activate Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the provided `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Open `.env` in your editor and enter your credentials:

```ini
# Azure AI Document Intelligence
DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/"
DOCUMENT_INTELLIGENCE_API_KEY="your_azure_document_intelligence_api_key"

# Azure AI Foundry / OpenAI Endpoint
FOUNDRY_ENDPOINT="https://<your-foundry-resource>.services.ai.azure.com/"
FOUNDRY_API_KEY="your_azure_foundry_api_key"
```

---

## Running the Application

### Start Backend Server

From the project root directory (with `.venv` activated):

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- Backend API will be live at: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Alternative ReDoc documentation: `http://127.0.0.1:8000/redoc`

> **Note:** The SQLite database `invoiceiq.db` is initialized automatically when the backend boots up.

### Serve the Frontend

The frontend communicates with the backend via CORS configured for `http://127.0.0.1:5500` and `http://localhost:5500`.

**Option A — Python's Built-in HTTP Server (Recommended):**
In a separate terminal tab, run:
```bash
python3 -m http.server 5500
```
Then navigate to:
- Landing Page: `http://127.0.0.1:5500/frontend/index.html`
- Documents Page: `http://127.0.0.1:5500/frontend/upload.html`
- AI Assistant Chat: `http://127.0.0.1:5500/frontend/chat.html`

**Option B — VS Code Live Server:**
1. Open the project in VS Code.
2. Right-click `frontend/index.html` and choose **"Open with Live Server"** (runs on port `5500` by default).

---

## API Documentation & Endpoints

| Method | Endpoint | Description | Request Body / Params |
|---|---|---|---|
| `GET` | `/api/health` | Healthcheck and service status | None |
| `POST` | `/api/documents/upload` | Upload & extract invoice file | `file` (Multipart), `document_type` (`SALES` or `PURCHASE`) |
| `GET` | `/api/documents` | Retrieve all processed documents | None |
| `GET` | `/api/documents/{id}` | Retrieve document details with line items | `id` (int, path parameter) |
| `POST` | `/api/chat` | Query the AI assistant about an invoice | JSON: `{"message": "...", "document_id": 1}` |
| `POST` | `/api/reset` | Purge all documents and line items | None |

### Example: Uploading an Invoice via `curl`

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/upload" \
  -F "file=@data/invoices/test-invoice.pdf" \
  -F "document_type=SALES"
```

### Example: Chatting with the AI Assistant via `curl`

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1, "message": "Is this a sales or purchase invoice, and what is the total?"}'
```

---

## Database Schema

The SQLite database (`invoiceiq.db`) is structured using SQLAlchemy:

```text
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│             documents                │       │            invoice_items             │
├──────────────────────────────────────┤       ├──────────────────────────────────────┤
│ id (PK, Integer)                     │◄──┐   │ id (PK, Integer)                     │
│ transaction_id (String, Unique)      │   └───│ document_id (FK -> documents.id)     │
│ document_type (String)               │       │ description (String)                 │
│ party_name (String)                  │       │ quantity (Float)                     │
│ transaction_date (String)            │       │ unit_price (Float)                   │
│ due_date (String)                    │       │ amount (Float)                       │
│ subtotal (Float)                     │       └──────────────────────────────────────┘
│ tax (Float)                          │
│ total_amount (Float)                 │
│ currency (String)                    │
│ payment_status (String)              │
└──────────────────────────────────────┘
```

---

## AI Invoice Assistant Workflow

1. **Upload & Selection**:
   - The user selects whether the uploaded document is a **Sales Invoice** (revenue) or **Purchase Invoice** (procurement).
2. **Extraction & Classification**:
   - The file is uploaded to the backend and parsed through Azure AI Document Intelligence.
   - The parsed document is tagged with the user-selected classification and stored in SQLite.
3. **Conversational Assistant Context**:
   - When the user transitions to the chat page (`chat.html`), the active invoice is loaded into `localStorage`.
   - Each prompt sent to `/api/chat` attaches the document ID.
   - `src/agent.py` retrieves the full structured invoice and injects it into a constrained prompt using `gpt-5-mini`.
   - The assistant answers queries (e.g. line items, dates, vendor details, sales vs. purchase context) strictly based on the selected invoice.

---

## Troubleshooting & Common Issues

### 1. `RuntimeError: DOCUMENT_INTELLIGENCE_ENDPOINT is not set.`
- **Cause**: The backend was started without a valid `.env` file or environment variables.
- **Solution**: Ensure `.env` exists in the root directory and contains both `DOCUMENT_INTELLIGENCE_ENDPOINT` and `DOCUMENT_INTELLIGENCE_API_KEY`.

### 2. CORS Blocked on Frontend
- **Cause**: The frontend is served on a port or origin not listed in `backend/main.py`.
- **Solution**: Serve the frontend at `http://127.0.0.1:5500` or add your custom origin to `allow_origins` in `backend/main.py`.

### 3. `Failed to resolve 'buisness-store.cognitiveservices.azure.com'`
- **Cause**: No network connectivity, or the Azure endpoint domain in `.env` is invalid or unreachable.
- **Solution**: Verify your internet connection and check the endpoint URL in your Azure portal.

### 4. Database Reset
- To reset the local database from scratch, you can either call `POST /api/reset` via Swagger/cURL, or simply delete the `invoiceiq.db` file in the root folder; the application will recreate it automatically on startup.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.