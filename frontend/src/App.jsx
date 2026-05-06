import {
  createConversation,
  fetchConversations,
  fetchConversation,
  sendMessage,
  askQuestion,
  deleteConversationAPI,
  renameConversationAPI,
  askQuestionStream
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
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  
  const assistantIndexRef = useRef(null);

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

      // ✅ Allow React to commit the new conversation
      await new Promise(r => setTimeout(r, 0));
    }

    const userMessage = question;
    setQuestion("");

    // Add user message
    setConversations(prev => {
      const convo = prev[conversationId] || { messages: [] };
      if (!convo) return prev;

      return {
        ...prev,
        [conversationId]: {
          ...convo,
          messages: [
            ...(convo.messages || []),
            { role: "user", content: userMessage }
          ]
        }
      };
    });

    // Save user message to db
    await sendMessage(conversationId, "user", userMessage);

    // Rename AFTER message is confirmed
    setTimeout(() => {
      const newTitle = generateTitleFromMessage(userMessage);
      if (newTitle) {
        renameConversation(conversationId, newTitle);
      }
    }, 0);

    setIsLoading(true);

    let assistantText = "";
    assistantIndexRef.current = null;

    // Allows React to settle the state updates for the user message before we start streaming the assistant response
    await new Promise(r => setTimeout(r, 0));

    // Add placeholder assistant message
    setConversations(prev => {
      const convo = prev[conversationId];
      if (!convo) return prev;

      const newMessages = [
        ...convo.messages,
        { role: "assistant", content: "Thinking..." }
      ];

      // ✅ set index HERE (this is the key fix)
      assistantIndexRef.current = newMessages.length - 1;

      return {
        ...prev,
        [conversationId]: {
          ...convo,
          messages: newMessages
        }
      };
    });

    // Stream tokens from backend
    await askQuestionStream(conversationId, userMessage, (token) => {
      // If first token, replace "Thinking..." instead of appending
      if (assistantText === "") {
        assistantText = token;
      } else {
        assistantText += token;
      }

      setConversations(prev => {
        const convo = prev[conversationId];
        if (!convo) return prev;

        const msgs = [...convo.messages];
        const idx = assistantIndexRef.current;

        if (idx == null || idx >= msgs.length) return prev;

        msgs[idx] = {
          ...msgs[idx],
          content: assistantText
        };

        return {
          ...prev,
          [conversationId]: {
            ...convo,
            messages: msgs
          }
        };
      });
    });

    setIsLoading(false);

    // Save final assistant message (ONLY once)
    if (assistantText.trim()) {
      await sendMessage(conversationId, "assistant", assistantText);
    }
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

        {/* Conversations list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          {Object.entries(conversations).map(([id, convo]) => (
            <div
              key={id}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "0.5rem",
                cursor: "pointer",
                background: id === activeId ? "#1b2335" : "transparent",
                borderRadius: "6px"
              }}
            >
              {/* LEFT SIDE: title or input */}
              <div style={{ flex: 1 }}>
                {editingId === id ? (
                  <input
                    autoFocus
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={() => {
                      if (editingTitle.trim() && editingTitle !== convo.title) {
                        renameConversation(id, editingTitle.trim());
                      }
                      setEditingId(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        if (editingTitle.trim() && editingTitle !== convo.title) {
                          renameConversation(id, editingTitle.trim());
                        }
                        setEditingId(null);
                      }
                      if (e.key === "Escape") {
                        setEditingId(null);
                      }
                    }}
                    style={{
                      width: "100%",
                      background: "transparent",
                      border: "1px solid rgba(255,255,255,0.3)",
                      borderRadius: "4px",
                      color: "white",
                      padding: "2px 4px"
                    }}
                  />
                ) : (
                  <div
                    onClick={() => setActiveId(id)}
                    onDoubleClick={() => {
                      setEditingId(id);
                      setEditingTitle(convo.title);
                    }}
                  >
                    {convo.title}
                  </div>
                )}
              </div>

              {/* RIGHT SIDE: delete icon */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(id);
                }}
                style={{
                  marginLeft: "0.5rem",
                  color: "white",
                  cursor: "pointer",
                  opacity: 0.7,
                  pointerEvents: editingId === id ? "none" : "auto"
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
            {messages.map((msg, i) => {
              // ✅ Defensive guard
              if (!msg || !msg.role) return null;

              if (msg.role === "user") {
                return (
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
                );
              }

              return (
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
                    <div style={{ whiteSpace: "pre-wrap" }}>
                      {msg.content}
                    </div>

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
                          {(msg.meta?.sources || []).slice(0, 3).join(", ")}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
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
