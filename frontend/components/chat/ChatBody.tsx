"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { ImageResult, Message, SourceDocument } from "@/types";
import InputBar from "./InputBar";
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
    const [threadId, setThreadId] = useState<string | null>(() => {
        if (typeof window !== "undefined") {
            return localStorage.getItem("chat_thread_id");
        }
        return null;
    });
    const bottomRef = useRef<HTMLDivElement>(null);
    const [apiStatus, setApiStatus] = useState<"unknown" | "ready" | "error">("unknown");
        
    // ── Health check ──────────────────────────────────────────────────────────
    useEffect(() => {
        fetch(`${API_BASE}/health`)
        .then((r) => r.json())
        .then((d) => setApiStatus(d.status === "ready" ? "ready" : "error"))
        .catch(() => setApiStatus("error"));
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    // ── Funzione riutilizzabile per caricare la history di un thread ──────────
    const fetchHistory = useCallback(async (id: string) => {
        try {
            const r = await fetch(`${API_BASE}/chat/history/${id}`);
            if (!r.ok) {
                // Thread non trovato o scaduto: pulizia locale
                localStorage.removeItem("chat_thread_id");
                setThreadId(null);
                setMessages([]);
                return;
            }
            const data = await r.json();
            console.log("[fetchHistory] raw messages:", data.messages);
            const loaded: Message[] = data.messages.map(
                (m: { role: string; content: string; timestamp: string; sources: SourceDocument[]; images: ImageResult[] }) => ({
                    id: uid(),
                    role: m.role as "user" | "assistant",
                    text: m.content,
                    sources: m.sources ?? [],
                    images: m.images ?? [],
                    timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
                })
            );
            console.log("[fetchHistory] loaded messages:", loaded);
            setMessages(loaded);
        } catch {
            localStorage.removeItem("chat_thread_id");
            setThreadId(null);
            setMessages([]);
        }
    }, []);

    // ── Al mount: ripristina la sessione salvata in localStorage ──────────────
    useEffect(() => {
        const saved = localStorage.getItem("chat_thread_id");
        if (saved) fetchHistory(saved);
    }, [fetchHistory]);

    // ── Evento dalla Sidebar: cambio thread o nuova chat ─────────────────────
    useEffect(() => {
        const handler = (e: Event) => {
            const selectedId = (e as CustomEvent<string | null>).detail;
            setThreadId(selectedId);
            if (selectedId) {
                localStorage.setItem("chat_thread_id", selectedId);
                fetchHistory(selectedId);
            } else {
                localStorage.removeItem("chat_thread_id");
                setMessages([]);
            }
        };
        window.addEventListener("thread-selected", handler);
        return () => window.removeEventListener("thread-selected", handler);
    }, [fetchHistory]);

    // ── Invio messaggio ───────────────────────────────────────────────────────
    const submit = useCallback(async (text: string) => {
        if (loading || apiStatus !== "ready") return;

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
                    thread_id: threadId,
                }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const elapsed = (performance.now() - t0) / 1000;

            console.log("Sources", data.sources);

            if (data.thread_id) {
                setThreadId(data.thread_id);
                localStorage.setItem("chat_thread_id", data.thread_id);
                // Notifica la Sidebar: aggiorna lista e segna questo thread come attivo
                window.dispatchEvent(
                    new CustomEvent("thread-updated", { detail: data.thread_id })
                );
            }

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

        } catch (e) {
            console.log("Errore nel caricamento:", e);
            setMessages((prev) => [...prev, {
                id: uid(),
                role: "assistant",
                text: "⚠️ Errore nella comunicazione con il server.",
                timestamp: new Date(),
            }]);
        } finally {
            setLoading(false);
        }
    }, [loading, threadId, apiStatus]);

    return (
        <div className="chat-body">
            <div className="chat-area">
                {apiStatus !== "ready" ? (
                    <div className="offline-state">
                        <div className="offline-bubble">
                            <svg className="offline-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M20 17.5a4.5 4.5 0 0 0-1-8.9 6 6 0 0 0-11.5 1.5A4 4 0 0 0 6 18h14z"/>
                                <path d="M4 4l16 16"/>
                            </svg>
                            <span>Backend non disponibile</span>
                        </div>
                    </div>
                ) : messages.length === 0 ? (
                    <div className="empty-chat">
                        <div className="empty-chat-content">
                            <h1>Ciao 👋, come posso aiutarti?</h1>
                            <p>Chiedimi qualcosa sulla cybersecurity</p>
                        </div>
                    </div>
                ) : (
                    <>
                        <MessageList messages={messages} threadId={threadId} />
                        {loading && <TypingIndicator />}
                        <div ref={bottomRef} />
                    </>
                )}
            </div>

            <InputBar
                onSubmit={submit}
                loading={loading}
                input={input}
                setInput={setInput}
                online={apiStatus === "ready"}
            />
        </div>
    );
};

export default ChatBody;