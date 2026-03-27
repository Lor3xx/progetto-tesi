import { Message } from "@/types";
import SourceCard from "./SourceCard";

function formatTime(d: Date) {
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

const MessageBubble = ({ msg }: { msg: Message }) => {
    const isUser = msg.role === "user";
    return (
        <div className={`message-row ${isUser ? "user" : "assistant"}`}>
            <div className="avatar">{isUser ? "U" : "AI"}</div>
            <div className="bubble-wrap">
                <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
                <p className="bubble-text">{msg.text}</p>
                {msg.sources && msg.sources.length > 0 && (
                    <div className="sources-section">
                    <p className="sources-label">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        </svg>
                        Fonti ({msg.sources.length})
                    </p>
                    <div className="sources-list">
                        {msg.sources.map((s, i) => (
                        <SourceCard key={i} doc={s} index={i} />
                        ))}
                    </div>
                    </div>
                )}
                </div>
                <span className="msg-meta">
                {formatTime(msg.timestamp)}
                {msg.elapsed !== undefined && ` · ${msg.elapsed.toFixed(2)}s`}
                </span>
            </div>
        </div>
    )
}

export default MessageBubble;