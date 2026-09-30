const API_URL = "http://127.0.0.1:8000";
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");
const contextEl = document.getElementById("invoice-context");
const badgeEl = document.getElementById("chat-context-badge");
const selectorEl = document.getElementById("invoice-selector");

const urlParams = new URLSearchParams(window.location.search);
let activeDocumentId = urlParams.get("document_id") || null;

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
// SELECT OR CLEAR ACTIVE DOCUMENT
// -------------------------------------------------------------

async function selectDocument(id) {
  if (!id) {
    clearSelectedDocument();
    return;
  }

  activeDocumentId = String(id);

  // Update browser URL query param cleanly without reload
  const newUrl = new URL(window.location.href);
  newUrl.searchParams.set("document_id", activeDocumentId);
  window.history.replaceState({}, "", newUrl.toString());

  if (selectorEl && selectorEl.value !== activeDocumentId) {
    selectorEl.value = activeDocumentId;
  }

  try {
    const res = await fetch(`${API_URL}/api/documents/${activeDocumentId}`);
    if (!res.ok) {
      throw new Error("Could not load invoice data.");
    }

    const doc = await res.json();
    const typeClass = (doc.document_type || "sales").toLowerCase();

    // Update Live Context Pill Badge
    if (badgeEl) {
      badgeEl.className = `badge badge-${typeClass}`;
      badgeEl.textContent = "● Live Context";
    }

    // Update Context Details Strip
    if (contextEl) {
      contextEl.innerHTML = `
        <span class="invoice-context-dot"></span>
        <span>
          <strong>Invoice #${escapeHtml(doc.transaction_id || doc.id)}</strong>
          <span class="result-type-badge badge-${typeClass}">${escapeHtml(doc.document_type || "INVOICE")}</span>
          ${doc.party_name ? ` · ${escapeHtml(doc.party_name)}` : ""}
          <button type="button" class="btn-clear-doc" onclick="clearSelectedDocument()" title="Deselect invoice">✕ Deselect</button>
        </span>
      `;
    }
  } catch (err) {
    console.warn("Could not display invoice context:", err);
    if (contextEl) {
      contextEl.innerHTML = `<span>Selected Invoice #${activeDocumentId} <button type="button" class="btn-clear-doc" onclick="clearSelectedDocument()">✕ Deselect</button></span>`;
    }
  }
}

function clearSelectedDocument() {
  activeDocumentId = null;

  // Clean up URL query parameters
  const newUrl = new URL(window.location.href);
  newUrl.searchParams.delete("document_id");
  window.history.replaceState({}, "", newUrl.pathname);

  // Clean up any stale localStorage from previous auto-assignment
  localStorage.removeItem("selectedDocumentId");
  sessionStorage.removeItem("selectedDocumentId");

  if (selectorEl) {
    selectorEl.value = "";
  }

  // Set badge to Standby
  if (badgeEl) {
    badgeEl.className = "badge badge-neutral";
    badgeEl.textContent = "○ Standby";
  }

  // Set context description to clear empty state
  if (contextEl) {
    contextEl.innerHTML = `
      <span>No document selected. Pick an invoice above or <a href="upload.html" style="color:var(--terracotta);text-decoration:underline;">upload a document</a> to audit line items.</span>
    `;
  }
}

// Make clearSelectedDocument globally accessible for inline onclick
window.clearSelectedDocument = clearSelectedDocument;

// -------------------------------------------------------------
// LOAD INVOICE SELECTOR DROPDOWN (DO NOT AUTO-SELECT)
// -------------------------------------------------------------

async function populateInvoiceSelector() {
  if (!selectorEl) return;

  try {
    const res = await fetch(`${API_URL}/api/documents`);
    if (!res.ok) return;

    const data = await res.json();
    const documents = Array.isArray(data) ? data : data.documents || [];

    selectorEl.innerHTML = "";

    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "— No document selected (Standby) —";
    selectorEl.appendChild(defaultOpt);

    documents.forEach(doc => {
      const opt = document.createElement("option");
      opt.value = String(doc.id);
      const docType = doc.document_type || "INVOICE";
      const party = doc.party_name ? ` · ${doc.party_name}` : "";
      const invNum = doc.transaction_id || `Invoice #${doc.id}`;
      opt.textContent = `${invNum} [${docType}]${party}`;
      selectorEl.appendChild(opt);
    });

    // If an explicit document was requested in URL, activate it
    if (activeDocumentId && documents.some(d => String(d.id) === String(activeDocumentId))) {
      selectorEl.value = String(activeDocumentId);
      await selectDocument(activeDocumentId);
    } else {
      // Otherwise stay strictly in Standby mode with no document selected
      clearSelectedDocument();
    }
  } catch (err) {
    console.warn("Could not populate invoice selector:", err);
  }
}

if (selectorEl) {
  selectorEl.addEventListener("change", function () {
    const chosen = this.value;
    if (chosen) {
      selectDocument(chosen);
    } else {
      clearSelectedDocument();
    }
  });
}

// -------------------------------------------------------------
// SEND MESSAGE
// -------------------------------------------------------------

async function sendMessage(q) {
  if (!q) return;

  addMessage(q, "user");

  // If user hasn't selected any document, give a clear helpful response
  if (!activeDocumentId) {
    addMessage(
      "No invoice is currently selected. Please choose an invoice from the dropdown selector above or upload a document to enable line-item audits, tax verification, and ledger queries.",
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
        message: q,
        document_id: Number(activeDocumentId)
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

document.addEventListener("DOMContentLoaded", populateInvoiceSelector);
if (document.readyState === "complete" || document.readyState === "interactive") {
  populateInvoiceSelector();
}