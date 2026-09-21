const API_URL = "http://127.0.0.1:8000";
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");

const params = new URLSearchParams(window.location.search);

let documentId =
  params.get("document_id") ||
  localStorage.getItem("selectedDocumentId");

async function getSelectedDocumentId() {
  // 1. Use document_id from URL if available
  if (documentId && !isNaN(Number(documentId)) && Number(documentId) > 0) {
    return Number(documentId);
  }

  // 2. Use the invoice saved by upload.js
  const savedId = localStorage.getItem("selectedDocumentId");

  if (savedId && !isNaN(Number(savedId)) && Number(savedId) > 0) {
    documentId = savedId;
    return Number(savedId);
  }

  // 3. If nothing is saved, get the latest uploaded document
  try {
    const response = await fetch(`${API_URL}/api/documents`);

    if (!response.ok) {
      throw new Error("Could not load documents.");
    }

    const data = await response.json();

    const documents = Array.isArray(data)
      ? data
      : data.documents || [];

    if (documents.length === 0) {
      return null;
    }

    // The backend returns documents with IDs.
    // Use the highest ID as the most recently uploaded document.
    const latestDocument = documents.reduce((latest, current) => {
      return Number(current.id) > Number(latest.id)
        ? current
        : latest;
    });

    if (!latestDocument.id) {
      return null;
    }

    documentId = String(latestDocument.id);

    localStorage.setItem(
      "selectedDocumentId",
      documentId
    );

    console.log(
      "Selected invoice for AI chat:",
      documentId
    );

    return Number(documentId);

  } catch (error) {
    console.error(
      "Unable to determine selected invoice:",
      error
    );

    return null;
  }
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

async function sendMessage(q) {
  addMessage(q, "user");

  try {
    const selectedId = await getSelectedDocumentId();

    if (!selectedId) {
      throw new Error("No invoice selected.");
    }

    console.log(
      "Sending chat request for invoice:",
      selectedId
    );

    const res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: q,
        document_id: selectedId
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

    addMessage(
      data.answer || "No answer returned.",
      "ai"
    );

  } catch (e) {
    addMessage(
      `Unable to connect to InvoiceIQ AI: ${e.message}`,
      "ai"
    );
  }
}

form.addEventListener("submit", e => {
  e.preventDefault();

  const q = input.value.trim();

  if (!q) {
    return;
  }

  input.value = "";
  sendMessage(q);
});

document.querySelectorAll(".suggestions button")
  .forEach(
    b => b.onclick = () => sendMessage(b.textContent.trim())
  );