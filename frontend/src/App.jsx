import { useState, useRef, useEffect } from "react";
import { askQuestion } from "./api";

function generateTitleFromMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return null;

  // Limit to 50 chars
  let title = trimmed.length > 50 ? trimmed.slice(0, 50) + "…" : trimmed;

  // Capitalize first letter
  title = title.charAt(0).toUpperCase() + title.slice(1);

  return title;
}

// Animated dots component
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

  // Conversations stored as:
  // { id: { title: string, messages: [] } }
  const [conversations, setConversations] = useState({});
  const [activeId, setActiveId] = useState(null);

  const [isLoading, setIsLoading] = useState(false);

  const chatRef = useRef(null);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedRaw = localStorage.getItem("dcc_conversations");

    if (savedRaw) {
      try {
        const saved = JSON.parse(savedRaw);
        const convos = saved.conversations || {};
        const ids = Object.keys(convos);

        if (ids.length > 0) {
          setConversations(convos);
          setActiveId(saved.activeId && convos[saved.activeId] ? saved.activeId : ids[0]);
          return;
        }
      } catch (e) {
        console.warn("Failed to parse saved conversations, starting fresh.", e);
      }
    }

    // Fallback: no valid saved data → create a fresh conversation
    const id = crypto.randomUUID();
    const timestamp = new Date().toLocaleString();
    setConversations({
      [id]: {
        title: `Conversation – ${timestamp}`,
        timestamp,
        messages: []
      }
    });
    setActiveId(id);
  }, []);


  // Ensure an active conversation always exists
  useEffect(() => {
    if (!activeId && Object.keys(conversations).length > 0) {
      setActiveId(Object.keys(conversations)[0]);
    }
  }, [conversations, activeId]);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(
      "dcc_conversations",
      JSON.stringify({ conversations, activeId })
    );
  }, [conversations, activeId]);

  // Auto-scroll chat
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [conversations, activeId, isLoading]);

  const messages = conversations[activeId]?.messages || [];

  function newConversation() {
    const id = crypto.randomUUID();
    const timestamp = new Date().toLocaleString();

    setConversations((prev) => ({
      ...prev,
      [id]: {
  title: `Conversation – ${timestamp}`,
  timestamp,
  messages: []
    }
    }));

    setActiveId(id);
  }

  function deleteConversation(id) {
  setConversations((prev) => {
    const updated = { ...prev };
    delete updated[id];

    const remainingIds = Object.keys(updated);

    if (id === activeId) {
      if (remainingIds.length > 0) {
        setActiveId(remainingIds[0]);
      } else {
        const newId = crypto.randomUUID();
        const timestamp = new Date().toLocaleString();
        updated[newId] = {
          title: `Conversation – ${timestamp}`,
          timestamp,
          messages: []
        };
        setActiveId(newId);
      }
    }

    return updated;
  });
}


  async function handleAsk() {
    if (!question.trim()) return;

    // If somehow no active conversation, create one on the fly
    if (!activeId) {
      const id = crypto.randomUUID();
      const timestamp = new Date().toLocaleString();

      setConversations((prev) => ({
        ...prev,
        [id]: { title: `Conversation – ${timestamp}`, messages: [] }
      }));

      setActiveId(id);
      return;
    }


    const userMessage = question;
    setQuestion("");

    // Add user message
    setConversations((prev) => {
      const convo = prev[activeId];
      const isFirstMessage = convo.messages.length === 0;

      const newTitle = isFirstMessage
        ? `${generateTitleFromMessage(userMessage)} – ${convo.timestamp}`
        : convo.title;

      return {
        ...prev,
        [activeId]: {
          ...convo,
          title: newTitle || convo.title,
          messages: [...convo.messages, { role: "user", content: userMessage }]
        }
      };
    });


    setIsLoading(true);

    const result = await askQuestion([
      ...messages,
      { role: "user", content: userMessage }
    ]);

    setIsLoading(false);

    // Add assistant message
    setConversations((prev) => ({
      ...prev,
      [activeId]: {
        ...prev[activeId],
        messages: [
          ...prev[activeId].messages,
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
  }

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
              <div onClick={() => setActiveId(id)} style={{ flex: 1 }}>
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
