"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { Message } from "@/types";
import InputBar from "../layout/InputBar";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

function uid() {
    return Math.random().toString(36).slice(2, 10);
}

const ChatBody = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [threadId, setThreadId] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll quando arriva un messaggio nuovo
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const submit = useCallback(async (text: string) => {
        if (loading) return;

        const userMsg: Message = {
            id: uid(),
            role: "user",
            text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        const t0 = performance.now();
        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    thread_id: threadId,  // null alla prima domanda
                }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const elapsed = (performance.now() - t0) / 1000;

            // Salva il thread_id per i messaggi successivi
            if (data.thread_id) setThreadId(data.thread_id);

            const assistantMsg: Message = {
                id: uid(),
                role: "assistant",
                text: data.answer,
                sources: data.sources ?? [],
                images: data.images ?? [],
                status: data.status,
                elapsed,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMsg]);

        } catch {
            setMessages((prev) => [...prev, {
                id: uid(),
                role: "assistant",
                text: "⚠️ Errore nella comunicazione con il server.",
                timestamp: new Date(),
            }]);
        } finally {
            setLoading(false);
        }
    }, [loading, threadId]);

    return (
        <div className="chat-body">
            <div className="chat-area">
                <MessageList messages={messages} />
                {loading && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>
            <InputBar
                onSubmit={submit}
                loading={loading}
                input={input}
                setInput={setInput}
            />
        </div>
    );
};

export default ChatBody;