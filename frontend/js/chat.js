
const API_URL = "http://127.0.0.1:8000";
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("messages");

function addMessage(text,type) {
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
  addMessage(q,"user");
  try {
    const res = await fetch(`${API_URL}/api/chat`, {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:q})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "AI request failed");
    addMessage(data.answer || "No answer returned.","ai");
  } catch(e) { addMessage(`Unable to connect to InvoiceIQ AI: ${e.message}`,"ai"); }
}
form.addEventListener("submit", e => { e.preventDefault(); const q=input.value.trim(); if(!q)return; input.value=""; sendMessage(q); });
document.querySelectorAll(".suggestions button").forEach(b => b.onclick=()=>sendMessage(b.textContent.trim()));
