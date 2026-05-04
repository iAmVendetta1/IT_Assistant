const API_BASE = "http://localhost:8000";

// -----------------------------
// Create a conversation
// -----------------------------
export async function createConversation(title = null) {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: title ? JSON.stringify({ title }) : null
  });

  if (!res.ok) {
    throw new Error("Failed to create conversation");
  }

  return res.json(); // { id, title }
}

// -----------------------------
// Fetch all conversations (id + title only)
// -----------------------------
export async function fetchConversations() {
  const res = await fetch(`${API_BASE}/conversations`);
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

// -----------------------------
// Fetch a conversation + messages
// -----------------------------
export async function fetchConversation(conversationId) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}`);
  if (!res.ok) throw new Error("Failed to load conversation");
  return res.json(); // { id, title, messages: [...] }
}

// -----------------------------
// Add a message to a conversation
// -----------------------------
export async function sendMessage(conversationId, role, content) {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, content })
  });

  if (!res.ok) {
    throw new Error("Failed to send message");
  }

  return res.json(); // { id }
}

// -----------------------------
// Ask the assistant a question
// -----------------------------
export async function askQuestion(conversationId, message) {
  const res = await fetch(`${API_BASE}/ask/${conversationId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });

  if (!res.ok) {
    throw new Error("Request failed");
  }

  return res.json(); // { answer }
}

// -----------------------------
// Delete a conversation
// -----------------------------
export async function deleteConversationAPI(id) {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
  return res.json();
}

// -----------------------------
// Rename a conversation
// -----------------------------
export async function renameConversationAPI(id, title) {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title })
  });
  if (!res.ok) throw new Error("Failed to rename conversation");
  return res.json();
}
