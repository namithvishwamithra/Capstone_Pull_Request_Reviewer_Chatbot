import { useRef, useState, type FormEvent } from "react";
import type { Review } from "../../lib/types";
import { streamChat } from "./chatApi";

interface Message {
  role: "user" | "assistant";
  text: string;
  incomplete?: boolean;
}

export function ChatPanel({ review }: { review: Review }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setQuestion("");
    setError("");
    setMessages((current) => [
      ...current,
      { role: "user", text },
      { role: "assistant", text: "" },
    ]);
    setBusy(true);
    const abortController = new AbortController();
    controller.current = abortController;
    try {
      await streamChat(
        review.id,
        text,
        (token) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === current.length - 1
                ? { ...message, text: message.text + token }
                : message,
            ),
          );
        },
        abortController.signal,
      );
    } catch (cause) {
      const message =
        cause instanceof Error
          ? cause.message
          : "The answer was interrupted. Please retry.";
      setError(message);
      setMessages((current) =>
        current.map((item, index) =>
          index === current.length - 1 ? { ...item, incomplete: true } : item,
        ),
      );
    } finally {
      setBusy(false);
      controller.current = null;
    }
  }

  return (
    <section className="chat-panel" aria-labelledby="chat-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">STAY IN CONTEXT</p>
          <h2 id="chat-heading">Ask about this review</h2>
        </div>
      </div>
      <div className="chat-messages" aria-live="polite">
        {messages.length === 0 && (
          <p className="chat-hint">
            Ask why a finding matters or explore the riskiest changes. Answers
            use this review's diff and findings.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`chat-message message-${message.role}`}
          >
            <span className="message-role">
              {message.role === "user" ? "You" : "Reviewer"}
            </span>
            <p>
              {message.text ||
                (busy && index === messages.length - 1 ? "Thinking…" : "")}
            </p>
            {message.incomplete && (
              <small>Incomplete response · retry your question</small>
            )}
          </div>
        ))}
      </div>
      {error && (
        <p className="inline-error" role="alert">
          {error}
        </p>
      )}
      <form className="chat-form" onSubmit={submit}>
        <label className="sr-only" htmlFor="chat-question">
          Ask a question about the review
        </label>
        <input
          id="chat-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a follow-up question…"
          maxLength={5000}
          disabled={busy}
        />
        {busy ? (
          <button
            type="button"
            className="secondary-button"
            onClick={() => controller.current?.abort()}
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            className="primary-button"
            disabled={!question.trim()}
          >
            Send
          </button>
        )}
      </form>
    </section>
  );
}
