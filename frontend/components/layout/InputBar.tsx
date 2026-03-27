"use client";
import { Message } from "@/types";
import { useCallback, useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

const InputBar = () => {

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
	const inputRef = useRef<HTMLTextAreaElement>(null);
	const visibleMessages = messages;



	// ── Auto-scroll ───────────────────────────────────────────────────────────
	useEffect(() => {
		bottomRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages, loading]);

	// ── Auto-resize textarea ──────────────────────────────────────────────────
	useEffect(() => {
		const ta = inputRef.current;
		if (!ta) return;
		ta.style.height = "auto";
		ta.style.height = Math.min(ta.scrollHeight, 140) + "px";
	}, [input]);


    // ── Submit ────────────────────────────────────────────────────────────────
	const submit = useCallback(async () => {
		const q = input.trim();
		if (!q || loading) return;

		const userMsg: Message = { id: uid(), role: "user", text: q, timestamp: new Date() };
		setMessages((prev) => [...prev, userMsg]);
		setInput("");
		setLoading(true);

		const t0 = performance.now();
		try {
		const res = await fetch(`${API_BASE}/query`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ question: q }),
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const data = await res.json();
		const elapsed = (performance.now() - t0) / 1000;

		const assistantMsg: Message = {
			id: uid(),
			role: "assistant",
			text: data.answer,
			sources: data.sources ?? [],
			elapsed,
			timestamp: new Date(),
		};
		setMessages((prev) => [...prev, assistantMsg]);
		} catch (err) {
		const errMsg: Message = {
			id: uid(),
			role: "assistant",
			text: "⚠️ Errore nella comunicazione con il server. Verifica che il backend Python sia avviato.",
			timestamp: new Date(),
		};
		setMessages((prev) => [...prev, errMsg]);
		} finally {
		setLoading(false);
		inputRef.current?.focus();
		}
	}, [input, loading]);

	const handleKey = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && !e.shiftKey) {
		e.preventDefault();
		submit();
		}
	};



    return (
        <div className="input-bar">
			<div className="input-inner">
				<textarea
					ref={inputRef}
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={handleKey}
					placeholder="Scrivi la tua domanda…"
					rows={1}
					disabled={loading}
				/>
				<button
					className="send-btn"
					onClick={submit}
					disabled={loading || !input.trim()}
					aria-label="Invia"
				>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                        <line x1="22" y1="2" x2="11" y2="13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
				</button>
			</div>
			<p className="input-hint">Enter per inviare &nbsp;·&nbsp; Shift+Enter per andare a capo</p>
		</div>
    )
}

export default InputBar;