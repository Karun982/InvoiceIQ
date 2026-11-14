# InvoiceIQ — AI-Powered Invoice Processing & Financial Assistant

InvoiceIQ is an end-to-end invoice extraction, structured storage, and AI-driven document intelligence system. It combines **Azure AI Document Intelligence** for high-precision OCR and invoice parsing, a **FastAPI** backend with **SQLite/SQLAlchemy** for relational persistence, and an **LLM-powered conversational agent** (via Azure AI Foundry / OpenAI `gpt-5-mini`) to answer natural-language questions, audit line items, reconcile taxes, and calculate cross-ledger balances across all uploaded invoices simultaneously.

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
- [Automated Testing](#automated-testing)
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

2. **Dual-Ledger Categorization (Sales vs. Purchase)**:
   - Categorizes business documents directly at intake:
     - ↗ **Sales Invoice**: Revenue/income earned from selling goods or services to customers.
     - ↓ **Purchase Invoice**: Expenses/procurement incurred by purchasing equipment, materials, or services from suppliers/vendors.
   - Mixed-batch uploads support per-file invoice type toggles.

3. **High-Precision Data Extraction & OCR Field Normalization**:
   - Uses Azure AI Document Intelligence's `prebuilt-invoice` model.
   - Robustly extracts vendor/customer names, invoice IDs, standardized dates (`%d %B %Y`), subtotals, totals, currencies, and line items.
   - Normalizes complex Indian currency string formats (`₹`, `Rs.`, `INR`, `/-`, commas, accounting parentheses).

4. **Comprehensive GST & Tax Component Extraction**:
   - Supports explicit `TotalTax`, itemized `TaxItems` component arrays (`CGST`, `SGST`, `IGST`), and root tax fields.
   - Avoids double-counting between aggregate taxes and component items.
   - Distinguishes explicitly extracted taxes from inferred taxes (`total_amount - subtotal`) via an `is_tax_inferred` flag.

5. **Line-Item Mathematical Reconciliation & Anomaly Detection**:
   - Reconciles individual line items against unit pricing (`quantity × unit_price`), explicit discounts, and invoice subtotals.
   - Detects and resolves OCR digit anomalies (e.g., table borders `|` or currency symbols `₹` scanned as leading digit `1`).
   - Flags discrepancies (`is_inconsistent = True`) with descriptive notes instead of silently presenting erroneous OCR readings.

6. **Relational Data Persistence with Deduplication**:
   - Persists documents and line items in local SQLite (`invoiceiq.db`) using SQLAlchemy 2.0 ORM.
   - Smart deduplication by transaction ID updates existing records with the latest extracted items without breaking database integrity.

7. **Unified Multi-Invoice AI Financial Intelligence**:
   - By default, the conversational AI (`gpt-5-mini`) reasons across **all uploaded sales and purchase invoices simultaneously**.
   - Answers cross-ledger queries (net balance `Sales − Purchases`, total tax collected vs. paid, vendor item audits) or deep-dives into any individual invoice.

8. **Tenthnode Design System UI**:
   - Lightweight, responsive HTML5/CSS3/Vanilla JS interface.
   - Light mode canvas in warm linen with forest green and terracotta accents.
   - Pure neutral obsidian/zinc dark mode (zero green tint) persisted in `localStorage`.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Database & ORM** | SQLite, SQLAlchemy 2.0 (with safe non-destructive schema migrations) |
| **OCR & Document Extraction** | Azure AI Document Intelligence SDK (`azure-ai-documentintelligence`) |
| **Conversational AI / LLM** | OpenAI Python SDK connected to Azure AI Foundry (`gpt-5-mini` model) |
| **Automated Testing** | Pytest 9+, FastAPI TestClient, unittest.mock |
| **Frontend** | Semantic HTML5, Modern CSS3 (Variables, Flexbox, Grid), Vanilla JavaScript (ES6+) |

---

## Project Directory Structure

```text
InvoiceIQ/
├── backend/
│   ├── __init__.py
│   └── main.py                 # FastAPI API routes, CORS, upload handling, chat
├── frontend/
│   ├── css/
│   │   └── style.css           # Global Tenthnode design system stylesheet
│   ├── js/
│   │   ├── chat.js             # Conversational AI client, ledger context loader
│   │   ├── theme.js            # Dark/light mode switcher
│   │   └── upload.js           # Multi-file intake, type classification, upload queue
│   ├── chat.html               # Financial intelligence assistant chat interface
│   ├── index.html              # Marketing / landing page
│   └── upload.html             # Document intake workspace
├── src/
│   ├── __init__.py
│   ├── agent.py                # Multi-invoice reasoning agent, context builder & prompts
│   ├── analytics.py            # Revenue, purchases, taxes, and net balance aggregators
│   ├── classifier.py           # Fallback automated document classifier
│   ├── database.py             # SQLAlchemy models, SQLite persistence, safe migrations
│   ├── invoice_processor.py    # Azure Document Intelligence OCR, tax & line reconciliation
│   └── models.py               # Pydantic data schemas
├── tests/
│   ├── test_invoice_iq.py      # Core unit & regression test suite (17 tests)
│   └── test_api_endpoints.py   # FastAPI endpoint integration tests (7 tests)
├── data/
│   └── invoices/               # Sample invoice documents
├── .env.example                # Template for required environment variables
├── invoiceiq.db                # SQLite relational database
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## Prerequisites

Before running the project, ensure you have:

1. **Python 3.10 or higher** installed (`python3 --version`).
2. An active **Azure Account** with:
   - **Azure AI Document Intelligence** resource (Endpoint URL and API Key).
   - **Azure AI Foundry / OpenAI** resource with a deployed `gpt-5-mini` model (Endpoint URL and API Key).
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
pip install pytest
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and enter your credentials:

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

- Backend API: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Alternative ReDoc documentation: `http://127.0.0.1:8000/redoc`

> **Note:** The SQLite database `invoiceiq.db` is initialized automatically when the backend boots up, including safe schema migrations and column checks.

### Serve the Frontend

The frontend communicates with the backend via CORS configured for `http://127.0.0.1:5500` and `http://localhost:5500`.

**Option A — Python's Built-in HTTP Server (Recommended):**
In a separate terminal tab, run:
```bash
python3 -m http.server 5500
```
Then navigate to:
- Landing Page: `http://127.0.0.1:5500/frontend/index.html`
- Documents Intake: `http://127.0.0.1:5500/frontend/upload.html`
- AI Assistant Chat: `http://127.0.0.1:5500/frontend/chat.html`

**Option B — VS Code Live Server:**
Open the project in VS Code, right-click `frontend/index.html`, and choose **"Open with Live Server"** (runs on port `5500` by default).

---

## Automated Testing

InvoiceIQ includes a comprehensive test suite (24 automated tests) with mocked Azure responses, requiring no live Azure network calls to run.

To execute the full test suite:

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

### Test Coverage Highlights
- Sales and purchase invoice extraction (`INV-2026-1045` and `PUR-2026-0872`).
- Line-item preservation (descriptions, quantities, unit prices, amounts).
- Line-item mathematical anomaly reconciliation (resolving OCR errors such as stray leading digits).
- GST extraction: `TotalTax`, component arrays (`CGST` + `SGST`), avoidance of double-counting, and inferred tax.
- Date extraction and normalization across ISO, European, US, and date object formats.
- SQLite foreign key integrity, cascade deletion, and duplicate update behavior.
- Multi-invoice financial metrics (Total Sales, Total Purchases, Net Balance, Combined Tax).
- AI structured context construction.
- FastAPI REST endpoint contracts (`/api/health`, `/api/documents`, `/api/analytics/summary`, `/api/chat`, `/api/documents/upload`).

---

## API Documentation & Endpoints

| Method | Endpoint | Description | Request Body / Params |
|---|---|---|---|
| `GET` | `/api/health` | Healthcheck and service status | None |
| `POST` | `/api/documents/upload` | Upload & extract invoice file | `file` (Multipart), `document_type` (`SALES` or `PURCHASE`) |
| `GET` | `/api/documents` | Retrieve all processed documents | None |
| `GET` | `/api/documents/{id}` | Retrieve document details with line items | `id` (int, path parameter) |
| `GET` | `/api/analytics/summary` | Aggregate ledger metrics (revenue, purchases, taxes, net balance) | None |
| `POST` | `/api/chat` | Conversational query across all invoices (or scoped via `document_id`) | JSON: `{"message": str, "document_id": Optional[int]}` |
| `POST` | `/api/reset` | Purge all documents and line items | None |

### Example: Fetching Analytics Summary via `curl`

```bash
curl -X GET "http://127.0.0.1:8000/api/analytics/summary"
```

Response:
```json
{
  "success": true,
  "revenue": 153400.0,
  "purchases": 336300.0,
  "expenses": 0.0,
  "net_balance": -182900.0,
  "estimated_profit": -182900.0,
  "sales_subtotal": 130000.0,
  "purchase_subtotal": 285000.0,
  "sales_tax": 23400.0,
  "purchase_tax": 51300.0,
  "total_tax": 74700.0,
  "document_count": 2
}
```

### Example: Chatting Across All Invoices via `curl`

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my total sales vs total purchases and net balance?"}'
```

---

## Database Schema

The SQLite database (`invoiceiq.db`) is managed via SQLAlchemy 2.0:

```text
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│             documents                │       │            invoice_items             │
├──────────────────────────────────────┤       ├──────────────────────────────────────┤
│ id (PK, Integer)                     │◄──┐   │ id (PK, Integer)                     │
│ transaction_id (String, Unique)      │   └───│ document_id (FK -> documents.id)     │
│ document_type (String, Indexed)      │       │ description (String)                 │
│ party_name (String)                  │       │ quantity (Float)                     │
│ transaction_date (String)            │       │ unit_price (Float)                   │
│ due_date (String)                    │       │ amount (Float)                       │
│ subtotal (Float)                     │       │ raw_ocr_amount (Float)               │
│ tax (Float)                          │       │ is_inconsistent (Boolean)            │
│ is_tax_inferred (Boolean)            │       │ inconsistency_note (String)          │
│ total_amount (Float)                 │       └──────────────────────────────────────┘
│ currency (String)                    │
│ payment_status (String)              │
└──────────────────────────────────────┘
```

---

## AI Invoice Assistant Workflow

1. **Intake & Classification**:
   - The user selects whether the uploaded document is a **Sales Invoice** (revenue) or **Purchase Invoice** (procurement).
2. **Extraction & Reconciliation**:
   - The file is processed with Azure AI Document Intelligence.
   - Line items are mathematically cross-checked against unit pricing, explicit discounts, and invoice subtotals.
   - Taxes are extracted or safely inferred (`total_amount - subtotal`) with source tracking.
3. **Database Insertion & Deduplication**:
   - Extracted invoices and itemized lines are committed to SQLite. Re-uploads update existing records.
4. **Conversational Multi-Invoice Intelligence**:
   - When the user asks questions on `chat.html`, `backend/main.py` queries `src/agent.py`.
   - The assistant receives a unified context payload of all active sales and purchase invoices, along with pre-calculated ledger totals.
   - The assistant answers cross-invoice queries (e.g., *"Compare sales vs. purchases"*, *"How much GST was collected vs. paid?"*, *"Reconcile line items from ABC Technologies"*) with strict factual grounding on SQLite records.

---

## Troubleshooting & Common Issues

### 1. `RuntimeError: DOCUMENT_INTELLIGENCE_ENDPOINT is not set.`
- **Cause**: Backend started without a valid `.env` file or environment variables.
- **Solution**: Ensure `.env` exists in the root directory and contains `DOCUMENT_INTELLIGENCE_ENDPOINT` and `DOCUMENT_INTELLIGENCE_API_KEY`.

### 2. CORS Blocked on Frontend
- **Cause**: Frontend served from an unapproved origin.
- **Solution**: Serve the frontend at `http://127.0.0.1:5500` or add your custom origin to `allow_origins` in `backend/main.py`.

### 3. Missing `pytest` Dependency
- **Cause**: Running tests without `pytest` installed in the virtual environment.
- **Solution**: Run `pip install pytest` inside `.venv`, then execute `PYTHONPATH=. .venv/bin/pytest tests/ -v`.

### 4. Database Reset
- **Solution**: Call `POST /api/reset` via Swagger/cURL to clear documents and items, or remove `invoiceiq.db`; the backend will recreate clean tables on startup.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
