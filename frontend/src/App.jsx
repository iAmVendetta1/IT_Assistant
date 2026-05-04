import {
  createConversation,
  fetchConversations,
  fetchConversation,
  sendMessage,
  askQuestion,
  deleteConversationAPI,
  renameConversationAPI
} from "./api";

import { useState, useRef, useEffect } from "react";

function generateTitleFromMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return null;

  let title = trimmed.length > 50 ? trimmed.slice(0, 50) + "…" : trimmed;
  title = title.charAt(0).toUpperCase() + title.slice(1);
  return title;
}

function ThinkingDots() {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 3 ? prev + "." : ""));
    }, 300);

    return () => clearInterval(interval);
  }, []);

  return <span>{dots}</span>;
}

function App() {
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState({});
  const [activeId, setActiveId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const chatRef = useRef(null);

  // ------------------------------------------------------------
  // Load conversation list from backend
  // ------------------------------------------------------------
  useEffect(() => {
    async function load() {
      const list = await fetchConversations();

      // Convert array → object keyed by ID
      const obj = {};
      for (const c of list) {
        obj[c.id] = {
          title: c.title,
          created_at: c.created_at,
          messages: [] // messages loaded later
        };
      }

      setConversations(obj);

      if (list.length > 0) {
        setActiveId(list[0].id);
      }
    }

    load();
  }, []);

  // ------------------------------------------------------------
  // Load messages when activeId changes
  // ------------------------------------------------------------
  useEffect(() => {
    async function load() {
      if (!activeId) return;

      try {
        const data = await fetchConversation(activeId);

        setConversations(prev => ({
          ...prev,
          [activeId]: {
            ...prev[activeId],
            messages: data.messages
          }
        }));
      } catch (err) {
        console.error("Failed to load conversation", err);
      }
    }

    load();
  }, [activeId]);

  // ------------------------------------------------------------
  // Auto-scroll chat
  // ------------------------------------------------------------
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [conversations, activeId, isLoading]);

  const messages = conversations[activeId]?.messages || [];

  // ------------------------------------------------------------
  // Create a new conversation
  // ------------------------------------------------------------
  async function newConversation() {
    const convo = await createConversation(); // { id, title }

    setConversations(prev => ({
      ...prev,
      [convo.id]: {
        title: convo.title,
        created_at: new Date().toISOString(),
        messages: []
      }
    }));

    setActiveId(convo.id);
  }

  // ------------------------------------------------------------
  // Delete a conversation
  // ------------------------------------------------------------
  async function deleteConversation(id) {
    await deleteConversationAPI(id);

    setConversations(prev => {
      const updated = { ...prev };
      delete updated[id];

      const remaining = Object.keys(updated);
      setActiveId(remaining.length > 0 ? remaining[0] : null);

      return updated;
    });
  }

  // ------------------------------------------------------------
  // Rename a conversation
  // ------------------------------------------------------------
  async function renameConversation(id, newTitle) {
  const updated = await renameConversationAPI(id, newTitle);

  setConversations(prev => ({
    ...prev,
    [id]: {
      ...prev[id],
      title: updated.title
    }
  }));
}

  // ------------------------------------------------------------
  // Handle asking a question
  // ------------------------------------------------------------
  async function handleAsk() {
    if (!question.trim()) return;

    let conversationId = activeId;

    // If no conversation exists, create one
    if (!conversationId) {
      const convo = await createConversation();
      conversationId = convo.id;

      setConversations(prev => ({
        ...prev,
        [conversationId]: {
          title: convo.title,
          created_at: new Date().toISOString(),
          messages: []
        }
      }));

      setActiveId(conversationId);
    }

    const userMessage = question;
    setQuestion("");

    // Add user message locally
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: [
          ...prev[conversationId].messages,
          { role: "user", content: userMessage }
        ]
      }
    }));

    // Save user message to backend
    await sendMessage(conversationId, "user", userMessage);

    setIsLoading(true);

    // Ask backend for assistant response
    const result = await askQuestion(conversationId, userMessage);

    setIsLoading(false);

    // Add assistant message locally
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: [
          ...prev[conversationId].messages,
          {
            role: "assistant",
            content: result.answer,
            meta: {
              collection: result.collection,
              sources: result.sources
            }
          }
        ]
      }
    }));

    // Save assistant message to backend
    await sendMessage(conversationId, "assistant", result.answer);
  }


  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        minHeight: "100vh",
        background: "#0f141f"
      }}
    >
      {/* SIDEBAR */}
      <div
        style={{
          width: "240px",
          background: "#0f141f",
          color: "white",
          borderRight: "1px solid rgba(255,255,255,0.2)",
          padding: "1rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem"
        }}
      >
        <button
          onClick={newConversation}
          style={{
            padding: "0.75rem",
            background: "#1b2335",
            color: "white",
            border: "1px solid rgba(255,255,255,0.2)",
            borderRadius: "8px",
            cursor: "pointer",
            textAlign: "left"
          }}
        >
          + New Conversation
        </button>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem"
          }}
        >
          {Object.entries(conversations).map(([id, convo]) => (
            <div
              key={id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0.75rem",
                borderRadius: "6px",
                cursor: "pointer",
                background: id === activeId ? "#1b2335" : "transparent",
                border: id === activeId ? "1px solid rgba(255,255,255,0.2)" : "none"
              }}
            >
              <div
                onClick={() => setActiveId(id)}
                onDoubleClick={() => {
                  const newTitle = prompt("Rename conversation:", convo.title);
                  if (newTitle && newTitle.trim()) {
                    renameConversation(id, newTitle.trim());
                  }
                }}
                style={{ flex: 1 }}
              >
                {convo.title}
              </div>

              <div
                onClick={(e) => {
                  e.stopPropagation(); // Prevent selecting the conversation
                  deleteConversation(id);
                }}
                style={{
                  marginLeft: "0.5rem",
                  color: "white",
                  cursor: "pointer",
                  opacity: 0.7
                }}
              >
                🗑️
              </div>
            </div>
          ))}

        </div>
      </div>

      {/* MAIN CHAT WINDOW */}
      <div
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          padding: "2rem"
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "700px",
            background: "#1b2335",
            borderRadius: "12px",
            padding: "2rem",
            display: "flex",
            flexDirection: "column",
            height: "80vh"
          }}
        >
          {/* Header */}
          <h1
            style={{
              color: "white",
              textAlign: "center",
              marginBottom: "2rem",
              fontFamily: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
              fontWeight: 600
            }}
          >
            DCC Assistant
          </h1>

          <hr
            style={{
              width: "100%",
              border: "none",
              borderBottom: "1px solid grey",
              marginBottom: "1rem"
            }}
          />

          {/* Chat Area */}
          <div
            ref={chatRef}
            style={{
              flex: 1,
              overflowY: "auto",
              paddingRight: "0.5rem",
              marginBottom: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "1rem"
            }}
          >
            {messages.map((msg, i) =>
              msg.role === "user" ? (
                <div key={i} style={{ display: "flex", justifyContent: "flex-end" }}>
                  <div
                    style={{
                      maxWidth: "80%",
                      background: "#0078ff",
                      color: "white",
                      padding: "0.75rem 1rem",
                      borderRadius: "16px",
                      borderBottomRightRadius: "4px",
                      fontSize: "0.95rem",
                      lineHeight: "1.4"
                    }}
                  >
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div key={i} style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div
                    style={{
                      maxWidth: "80%",
                      background: "#0f141f",
                      color: "#ffffff",
                      padding: "0.75rem 1rem",
                      borderRadius: "16px",
                      borderBottomLeftRadius: "4px",
                      fontSize: "0.95rem",
                      lineHeight: "1.5"
                    }}
                  >
                    <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>

                    {msg.meta && (
                      <div
                        style={{
                          marginTop: "0.75rem",
                          fontSize: "0.8rem",
                          color: "#7c7c7c"
                        }}
                      >
                        <div>
                          <strong>Collection:</strong> {msg.meta.collection}
                        </div>

                        <div style={{ marginTop: "0.25rem" }}>
                          <strong>Top 3 Sources:</strong>{" "}
                          {msg.meta.sources.slice(0, 3).join(", ")}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            )}

            {/* Thinking Indicator */}
            {isLoading && (
              <div style={{ display: "flex", justifyContent: "flex-start" }}>
                <div
                  style={{
                    maxWidth: "80%",
                    background: "#0f141f",
                    color: "#ffffff",
                    padding: "0.75rem 1rem",
                    borderRadius: "16px",
                    borderBottomLeftRadius: "4px",
                    fontSize: "0.95rem",
                    lineHeight: "1.5"
                  }}
                >
                  Thinking<ThinkingDots />
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div style={{ display: "flex" }}>
            <textarea
              style={{
                flex: 1,
                padding: "8px",
                fontSize: "1rem",
                borderRadius: "8px",
                border: "1px solid #696767",
                background: "#0f141f",
                color: "white",
                resize: "none",
                minHeight: "40px",
                maxHeight: "100px",
                overflowY: "auto",
                lineHeight: "1.4"
              }}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
              placeholder="Message DCC Assistant"
            />

            <button
              onClick={handleAsk}
              disabled={isLoading}
              style={{
                marginLeft: "1rem",
                padding: "12px 20px",
                fontSize: "1rem",
                borderRadius: "8px",
                border: "none",
                background: isLoading ? "#333" : "#0f141f",
                color: "white",
                cursor: isLoading ? "not-allowed" : "pointer"
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
