from typing import List
from src.models import BusinessDocument


def calculate_revenue(documents):
    return sum(
        doc.total_amount or 0
        for doc in documents
        if doc.document_type == "SALES"
    )


def calculate_purchases(documents):
    return sum(
        doc.total_amount or 0
        for doc in documents
        if doc.document_type == "PURCHASE"
    )


def calculate_expenses(documents):
    return sum(
        doc.total_amount or 0
        for doc in documents
        if doc.document_type == "EXPENSE"
    )


def calculate_estimated_profit(documents):

    revenue = calculate_revenue(documents)
    purchases = calculate_purchases(documents)
    expenses = calculate_expenses(documents)

    return revenue - purchases - expenses