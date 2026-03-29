// frontend/chat.js
async function sendChat() {
  const input = document.getElementById("chatInput");
  const question = input.value.trim();
  if (!question || !globalData) return;

  input.value = "";

  // Hide suggested buttons after first use
  const suggested = document.getElementById("chatSuggested");
  if (suggested) suggested.style.display = "none";

  appendBubble(question, "user");
  const thinking = appendBubble("Thinking...", "ai");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, question }),
    });
    const data = await res.json();
    thinking.textContent = data.answer || "No answer returned.";
  } catch (e) {
    thinking.textContent = "Chat unavailable — check the server.";
  }

  const box = document.getElementById("chatMessages");
  box.scrollTop = box.scrollHeight;
}

function appendBubble(text, role) {
  const box = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `chat-bubble bubble-${role === "user" ? "user" : "ai"}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}