import { Message } from "@/types";
import SourceCard from "./SourceCard";
import ImageCard from "./ImageCard";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

function formatTime(d: Date) {
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

const getShowSourcesForThread = (threadId?: string | null): boolean => {
	if (!threadId) return true;
	try {
		const stored = sessionStorage.getItem(`show-sources-${threadId}`);
		return stored === null ? true : stored === "true";
	} catch {
		return true;
	}
};

const MessageBubble = ({ msg, threadId }: { msg: Message, threadId: string | null }) => {
    const isUser = msg.role === "user";
    const [showSources, setShowSources] = useState(
        getShowSourcesForThread(threadId)
    );

    // Leggi lo stato quando il thread cambia
    useEffect(() => {
        setShowSources(getShowSourcesForThread(threadId));
    }, [threadId]);

    // Ascolta i cambi di visibilità delle fonti dal menu
    useEffect(() => {
        const handler = (e: Event) => {
            const event = e as CustomEvent;
            if (!threadId || event.detail.threadId === threadId) {
                setShowSources(event.detail.showSources);
            }
        };
        window.addEventListener("show-sources-changed", handler);
        return () => window.removeEventListener("show-sources-changed", handler);
    }, [threadId]);
    
    return (
        <div className={`message-row ${isUser ? "user" : "assistant"}`}>
            <div className="avatar">{isUser ? "U" : "AI"}</div>
            <div className="bubble-wrap">
                <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
                <div className="bubble-text">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
                    {showSources  && msg.sources && msg.sources.length > 0 && (
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

                    {msg.images && msg.images.length > 0 && (
                        <div className="sources-section">
                            <p className="sources-label">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
                                    <polyline points="21 15 16 10 5 21"/>
                                </svg>
                                Immagini ({msg.images.length})
                            </p>
                            <div className="sources-list">
                                {msg.images.map((img, i) => (
                                    <ImageCard key={i} img={img} index={i} />
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