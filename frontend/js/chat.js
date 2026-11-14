const API_URL = "http://127.0.0.1:8000";
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");
const contextEl = document.getElementById("invoice-context");
const badgeEl = document.getElementById("chat-context-badge");

let allDocuments = [];

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function addMessage(text, type) {
  const el = document.createElement("div");
  el.className = `message ${type}`;

  if (type === "ai") {
    el.innerHTML = `<div class="message-avatar">IQ</div><div class="message-content"><span class="message-label">InvoiceIQ AI</span><p></p></div>`;
  } else {
    el.innerHTML = `<div class="message-content"><p></p></div>`;
  }

  el.querySelector("p").textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

// -------------------------------------------------------------
// LOAD UPLOADED INVOICES CONTEXT (ALL DOCUMENTS UNIFIED)
// -------------------------------------------------------------

async function loadLedgerContext() {
  try {
    const res = await fetch(`${API_URL}/api/documents`);
    if (!res.ok) {
      renderEmptyState();
      return;
    }

    const data = await res.json();
    allDocuments = Array.isArray(data) ? data : data.documents || [];

    if (allDocuments.length === 0) {
      renderEmptyState();
      return;
    }

    renderActiveContext();
  } catch (err) {
    console.warn("Could not load ledger context:", err);
    renderEmptyState();
  }
}

function renderActiveContext() {
  const salesInvoices = allDocuments.filter(
    d => (d.document_type || "").toUpperCase() === "SALES"
  );
  const purchaseInvoices = allDocuments.filter(
    d => (d.document_type || "").toUpperCase() === "PURCHASE"
  );
  const otherInvoices = allDocuments.filter(
    d => !["SALES", "PURCHASE"].includes((d.document_type || "").toUpperCase())
  );

  if (badgeEl) {
    badgeEl.className = "badge badge-sales";
    badgeEl.textContent = "● Live Context (All Invoices)";
  }

  if (contextEl) {
    let summaryText = "";

    if (salesInvoices.length > 0 && purchaseInvoices.length > 0) {
      const salesDetails = salesInvoices
        .map(d => `${d.party_name || d.transaction_id || ('#' + d.id)}`)
        .join(", ");
      const purchaseDetails = purchaseInvoices
        .map(d => `${d.party_name || d.transaction_id || ('#' + d.id)}`)
        .join(", ");

      summaryText = `
        <strong>${allDocuments.length} Invoices Loaded:</strong> 
        ${salesInvoices.length} Sales (${escapeHtml(salesDetails)}), 
        ${purchaseInvoices.length} Purchase (${escapeHtml(purchaseDetails)}) 
        · Chatbot analyzes and reconciles across both documents
      `;
    } else if (salesInvoices.length > 0) {
      summaryText = `
        <strong>${salesInvoices.length} Sales ${salesInvoices.length === 1 ? "Invoice" : "Invoices"} Active:</strong> 
        ${escapeHtml(salesInvoices.map(d => d.party_name || d.transaction_id).join(", "))}
      `;
    } else if (purchaseInvoices.length > 0) {
      summaryText = `
        <strong>${purchaseInvoices.length} Purchase ${purchaseInvoices.length === 1 ? "Invoice" : "Invoices"} Active:</strong> 
        ${escapeHtml(purchaseInvoices.map(d => d.party_name || d.transaction_id).join(", "))}
      `;
    } else {
      summaryText = `<strong>${allDocuments.length} Invoices Active:</strong> Answering across all uploaded documents`;
    }

    contextEl.innerHTML = `
      <span class="invoice-context-dot"></span>
      <span>${summaryText}</span>
    `;
  }
}

function renderEmptyState() {
  allDocuments = [];

  if (badgeEl) {
    badgeEl.className = "badge badge-neutral";
    badgeEl.textContent = "○ Standby";
  }

  if (contextEl) {
    contextEl.innerHTML = `
      <span>No invoices uploaded yet. <a href="upload.html" style="color:var(--terracotta);text-decoration:underline;font-weight:600;">Upload your sales & purchase documents</a> to begin.</span>
    `;
  }
}

// -------------------------------------------------------------
// SEND MESSAGE ACROSS ALL UPLOADED INVOICES
// -------------------------------------------------------------

async function sendMessage(q) {
  if (!q) return;

  addMessage(q, "user");

  if (allDocuments.length === 0) {
    addMessage(
      "No invoices have been uploaded yet. Please upload your sales and purchase documents in the Document Workspace so I can analyze totals, compare revenues vs. expenses, and audit your line items.",
      "ai"
    );
    return;
  }

  try {
    const res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: q
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "AI request failed"
      );
    }

    addMessage(data.answer || "No answer returned.", "ai");
  } catch (e) {
    addMessage(`Unable to connect to InvoiceIQ AI: ${e.message}`, "ai");
  }
}

window.useSuggestion = function (text) {
  if (input) {
    input.value = text;
  }
  sendMessage(text);
};

// -------------------------------------------------------------
// EVENT LISTENERS
// -------------------------------------------------------------

if (form) {
  form.addEventListener("submit", e => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    sendMessage(q);
  });
}

document.querySelectorAll(".suggestions button").forEach(b => {
  b.onclick = () => {
    const text = b.getAttribute("onclick")
      ? b.getAttribute("onclick").match(/'([^']+)'/)?.[1] || b.textContent.trim()
      : b.textContent.trim();
    sendMessage(text);
  };
});

document.addEventListener("DOMContentLoaded", loadLedgerContext);
if (document.readyState === "complete" || document.readyState === "interactive") {
  loadLedgerContext();
}