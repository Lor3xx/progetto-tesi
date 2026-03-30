"use client";
import { useEffect, useState, useCallback } from "react";
import { ConversationPreview } from "@/types";
import ConversationItem from "./ConversationItem";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

export default function Sidebar() {
	const [conversations, setConversations] = useState<ConversationPreview[]>([]);
	const [activeId, setActiveId]           = useState<string | null>(null);
	const [isLoading, setIsLoading]         = useState(true);
	const [error, setError]                 = useState<string | null>(null);

	// Leggi il thread attivo da localStorage al mount
	useEffect(() => {
		setActiveId(localStorage.getItem("chat_thread_id"));
	}, []);

	// Sincronizza quando ChatBody aggiorna il thread (evento custom)
	useEffect(() => {
		const handler = (e: Event) => {
			const threadId = (e as CustomEvent<string>).detail;
			setActiveId(threadId);
			// Dopo un nuovo messaggio, aggiorna la lista per mostrare il titolo
			fetchConversations();
		};
		window.addEventListener("thread-updated", handler);
		return () => window.removeEventListener("thread-updated", handler);
	}, []);

	const fetchConversations = useCallback(async () => {
		try {
			setError(null);
			const res = await fetch(`${API_BASE}/conversations?limit=100`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			setConversations(data.conversations);
		} catch (err) {
			setError("Errore caricamento.");
			console.error("[Sidebar]", err);
		} finally {
			setIsLoading(false);
		}
	}, []);

	useEffect(() => { fetchConversations(); }, [fetchConversations]);

	const handleSelect = (threadId: string) => {
		setActiveId(threadId);
		localStorage.setItem("chat_thread_id", threadId);
		// Notifica ChatBody di caricare la history di questo thread
		window.dispatchEvent(new CustomEvent("thread-selected", { detail: threadId }));
	};

	const handleNewChat = () => {
		setActiveId(null);
		localStorage.removeItem("chat_thread_id");
		window.dispatchEvent(new CustomEvent("thread-selected", { detail: null }));
	};

	const handleDelete = async (threadId: string) => {
		try {
			const res = await fetch(`${API_BASE}/conversations/${threadId}`, { method: "DELETE" });
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			setConversations((prev) => prev.filter((c) => c.thread_id !== threadId));
			if (threadId === activeId) handleNewChat();
		} catch (err) {
			console.error("[Sidebar] delete error:", err);
			alert("Errore durante l'eliminazione.");
		}
	};

	return (
		<aside className="sidebar">
			<div className="sidebar-header">
				<span className="sidebar-title">Cronologia</span>
				<button className="sidebar-new-btn" onClick={handleNewChat} title="Nuova chat">
					<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
						fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
						<path d="M12 20h9"/>
						<path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/>
					</svg>
				</button>
			</div>

			<div className="sidebar-list">
				{isLoading && <p className="sidebar-status">Caricamento…</p>}
				{!isLoading && error && <p className="sidebar-status sidebar-status--error">{error}</p>}
				{!isLoading && !error && conversations.length === 0 && (
					<p className="sidebar-status">Nessuna chat salvata.</p>
				)}
				{!isLoading && !error && conversations.map((conv) => (
					<ConversationItem
						key={conv.thread_id}
						conversation={conv}
						isActive={conv.thread_id === activeId}
						onSelect={handleSelect}
						onDelete={handleDelete}
					/>
				))}
			</div>
		</aside>
	);
}