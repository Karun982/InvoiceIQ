# InvoiceIQ

InvoiceIQ is an AI-powered invoice processing and business analytics application that extracts information from business documents, classifies them, stores structured data, and provides AI-powered financial insights.

## Features

- Upload PDF and image-based business documents
- Automatic invoice data extraction using Azure AI Document Intelligence
- AI-powered document classification using GPT-5-mini
- Document categories:
  - Sales
  - Purchase
  - Expense
  - Other
- SQLite database for structured document storage
- Automatic business analytics
- Revenue, purchase, expense and estimated profit calculations
- AI Business Agent for natural-language financial queries
- Interactive dashboard
- AI chat interface
- FastAPI backend
- HTML, CSS and JavaScript frontend

## Architecture

```text
User
 │
 ▼
InvoiceIQ Web App
 │
 ├── Upload Document
 │       │
 │       ▼
 │   Azure AI Document Intelligence
 │       │
 │       ▼
 │   Structured Invoice Data
 │       │
 │       ▼
 │   GPT-5-mini Classification
 │       │
 │       ▼
 │   SQLite Database
 │
 ├── Dashboard
 │       │
 │       ▼
 │   Business Analytics
 │
 └── AI Chat
         │
         ▼
     GPT-5-mini
         │
         ▼
     Business Tools
         │
         ▼
     SQLite Data