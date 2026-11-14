from typing import List, Any, Optional


def calculate_revenue(documents: List[Any]) -> float:
    """Sum of total_amount for all SALES invoices."""
    return round(
        sum(
            (doc.total_amount or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "SALES"
        ),
        2,
    )


def calculate_purchases(documents: List[Any]) -> float:
    """Sum of total_amount for all PURCHASE invoices."""
    return round(
        sum(
            (doc.total_amount or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "PURCHASE"
        ),
        2,
    )


def calculate_expenses(documents: List[Any]) -> float:
    """Sum of total_amount for all EXPENSE invoices."""
    return round(
        sum(
            (doc.total_amount or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "EXPENSE"
        ),
        2,
    )


def calculate_sales_subtotal(documents: List[Any]) -> float:
    """Sum of subtotal for all SALES invoices."""
    return round(
        sum(
            (doc.subtotal or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "SALES"
        ),
        2,
    )


def calculate_purchase_subtotal(documents: List[Any]) -> float:
    """Sum of subtotal for all PURCHASE invoices."""
    return round(
        sum(
            (doc.subtotal or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "PURCHASE"
        ),
        2,
    )


def calculate_net_balance(documents: List[Any]) -> float:
    """Net Balance = Total Sales - Total Purchases."""
    revenue = calculate_revenue(documents)
    purchases = calculate_purchases(documents)
    return round(revenue - purchases, 2)


def calculate_estimated_profit(documents: List[Any]) -> float:
    """Estimated Profit = Revenue - Purchases - Expenses."""
    revenue = calculate_revenue(documents)
    purchases = calculate_purchases(documents)
    expenses = calculate_expenses(documents)
    return round(revenue - purchases - expenses, 2)


def calculate_sales_tax(documents: List[Any]) -> float:
    """Total Sales Tax = Sum of SALES tax values."""
    return round(
        sum(
            (doc.tax or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "SALES"
            and getattr(doc, "tax", None) is not None
        ),
        2,
    )


def calculate_purchase_tax(documents: List[Any]) -> float:
    """Total Purchase Tax = Sum of PURCHASE tax values."""
    return round(
        sum(
            (doc.tax or 0.0)
            for doc in documents
            if (getattr(doc, "document_type", None) or "").upper() == "PURCHASE"
            and getattr(doc, "tax", None) is not None
        ),
        2,
    )


def calculate_total_tax(documents: List[Any]) -> float:
    """Combined GST = Sales Tax + Purchase Tax."""
    sales_tax = calculate_sales_tax(documents)
    purchase_tax = calculate_purchase_tax(documents)
    return round(sales_tax + purchase_tax, 2)
