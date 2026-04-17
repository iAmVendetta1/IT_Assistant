// frontend/src/api.js
export async function askQuestion(messages) {
  const res = await fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!res.ok) {
    throw new Error("Request failed");
  }

  return res.json();
}
