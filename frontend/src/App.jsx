import { useState, useRef, useEffect } from "react";
import { askQuestion } from "./api";

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
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  async function handleAsk() {
    if (!question.trim()) return;

    const userMessage = question;
    setQuestion("");

    // Add user message
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage }
    ]);

    setIsLoading(true);

    const result = await askQuestion([
      ...messages,
      { role: "user", content: userMessage }
    ]);

    setIsLoading(false);

    // Add assistant message
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: result.answer,
        meta: {
          collection: result.collection,
          sources: result.sources
        }
      }
    ]);
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        minHeight: "100vh",
        background: "#0f141f",
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
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
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
            margin: "0 0 2rem 0",
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
              if (e.key === "Enter") {
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
  );
}

export default App;
