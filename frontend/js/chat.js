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

// -------------------------------------------------------------
// STRUCTURED MARKDOWN & FINANCIAL TEXT FORMATTER
// -------------------------------------------------------------

function formatMarkdown(raw) {
  if (!raw) return "";

  // 1. Normalize line breaks and escape HTML for security
  let text = escapeHtml(String(raw).replace(/\r\n/g, "\n"));

  // 2. Headings
  text = text.replace(/^### (.*$)/gim, '<h4 class="chat-heading">$1</h4>');
  text = text.replace(/^## (.*$)/gim, '<h3 class="chat-heading">$1</h3>');
  text = text.replace(/^# (.*$)/gim, '<h3 class="chat-heading">$1</h3>');

  // 3. Bold & Italic
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
  text = text.replace(/(^|[^\*])\*([^\*]+)\*([^\*]|$)/g, '$1<em>$2</em>$3');

  // 4. Inline code
  text = text.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');

  // 5. Arrow transforms
  text = text.replace(/\s*->\s*/g, ' → ');

  // 6. Line by line parsing for lists, headers and paragraphs
  const lines = text.split("\n");
  let out = [];
  let inUl = false;
  let inOl = false;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }
      continue;
    }

    const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    const olMatch = trimmed.match(/^(\d+)[\.\)]\s+(.*)$/);

    if (ulMatch) {
      if (inOl) { out.push("</ol>"); inOl = false; }
      if (!inUl) { out.push('<ul class="chat-list">'); inUl = true; }
      out.push(`<li>${ulMatch[1]}</li>`);
    } else if (olMatch) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (!inOl) { out.push('<ol class="chat-list">'); inOl = true; }
      out.push(`<li>${olMatch[2]}</li>`);
    } else if (trimmed.startsWith("<h3") || trimmed.startsWith("<h4")) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }
      out.push(trimmed);
    } else {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }

      // Emphasize financial labels if not already bold
      let formatted = trimmed.replace(
        /^(Invoice|Party|Transaction date|Due date|Currency|Subtotal|GST|Tax|Total|Net Balance|Status|Discrepancies|Verification|Line items|Summation and comparison):/i,
        '<strong>$1:</strong>'
      );

      out.push(`<p class="chat-p">${formatted}</p>`);
    }
  }

  if (inUl) out.push("</ul>");
  if (inOl) out.push("</ol>");

  return out.join("");
}

// -------------------------------------------------------------
// CHAT MESSAGE RENDERING & INTELLIGENT SCROLLING
// -------------------------------------------------------------

function addMessage(text, type) {
  const el = document.createElement("div");
  el.className = `message ${type}`;

  if (type === "ai") {
    el.innerHTML = `
      <div class="message-meta">
        <span class="message-badge">IQ</span>
        <span class="message-label">InvoiceIQ AI</span>
      </div>
      <div class="message-content">
        <div class="message-body">${formatMarkdown(text)}</div>
      </div>
    `;
  } else {
    el.innerHTML = `
      <div class="message-content">
        <div class="message-body">${formatMarkdown(text)}</div>
      </div>
    `;
  }

  messages.appendChild(el);

  // Strictly container-internal smooth scroll (never touches window scroll offset)
  requestAnimationFrame(() => {
    if (type === "user") {
      messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
    } else {
      const containerHeight = messages.clientHeight;
      const elHeight = el.clientHeight;
      if (elHeight > containerHeight * 0.6) {
        // Long response: show the top so the user can read from line 1
        const targetTop = el.offsetTop - messages.offsetTop - 12;
        messages.scrollTo({
          top: targetTop > 0 ? targetTop : 0,
          behavior: "smooth"
        });
      } else {
        // Short response: scroll to show the complete response
        messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
      }
    }
  });
}

function showTypingIndicator() {
  removeTypingIndicator();
  const el = document.createElement("div");
  el.className = "message ai typing-indicator";
  el.id = "chat-typing-indicator";
  el.innerHTML = `
    <div class="message-meta">
      <span class="message-badge">IQ</span>
      <span class="message-label">InvoiceIQ AI</span>
    </div>
    <div class="message-content">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messages.appendChild(el);
  requestAnimationFrame(() => {
    messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
  });
}

function removeTypingIndicator() {
  const el = document.getElementById("chat-typing-indicator");
  if (el) el.remove();
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

  showTypingIndicator();

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
    removeTypingIndicator();

    if (!res.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "AI request failed"
      );
    }

    addMessage(data.answer || "No answer returned.", "ai");
  } catch (e) {
    removeTypingIndicator();
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

// Prevent outer window scrolling on dedicated chat console
window.addEventListener("scroll", () => {
  if (window.scrollY !== 0 || window.scrollX !== 0) {
    window.scrollTo(0, 0);
  }
}, { passive: true });

document.addEventListener("DOMContentLoaded", () => {
  window.scrollTo(0, 0);
  loadLedgerContext();
});
if (document.readyState === "complete" || document.readyState === "interactive") {
  window.scrollTo(0, 0);
  loadLedgerContext();
}
