"use client";
import { useEffect, useState, useCallback } from "react";
import { ConversationPreview } from "@/types";
import ConversationItem from "./ConversationItem";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

export default function Sidebar() {
	const [conversations, setConversations] = useState<ConversationPreview[]>([]);
	const [activeId, setActiveId]           = useState<string | null>(null);
	const [isLoading, setIsLoading]         = useState(true);
	const [status, setStatus]               = useState<"unknown" | "ready" | "error">("unknown");
	const [isOpen, setIsOpen] = useState(false);

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
	},);

	useEffect(() => {
		const handler = () => setIsOpen(o => !o);
		window.addEventListener("toggle-sidebar", handler);
		return () => window.removeEventListener("toggle-sidebar", handler);
	}, []);

	const fetchConversations = useCallback(async () => {
		try {
			setStatus("unknown");
			setIsLoading(true);

			const res = await fetch(`${API_BASE}/conversations?limit=100`);

			// 🔴 backend non raggiungibile o offline
			if (!res.ok) {
				setConversations([]);
				setStatus("error");
				return;
			}

			const data = await res.json();
			setConversations(data?.conversations ?? []);
			setStatus("ready");

		} catch {
			// 🟡 backend spento → NON è errore UI
			setStatus("error");

			setConversations([]); // 👈 sidebar vuota

		} finally {
			setIsLoading(false);
		}
	}, []);

	useEffect(() => { fetchConversations(); }, [fetchConversations]);

	const handleSelect = (threadId: string) => {
		setActiveId(threadId);
		setIsOpen(false);
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

	const handleUpdateTitle = async (threadId: string, title: string) => {
		try {
			const res = await fetch(`${API_BASE}/conversations/${threadId}/title`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ new_title: title })
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);

			setConversations((prev) =>
				prev.map((c) =>
					c.thread_id === threadId
						? { ...c, title }
						: c
				)
			);

		} catch (err) {
			console.error("[Sidebar] update title error:", err);
			alert("Errore durante l'aggiornamento del titolo.");
		}
	}

	return (
		<aside className={`sidebar${isOpen ? " open" : ""}`}>
			<div className="sidebar-header">
				<span className="sidebar-title">Cronologia</span>
				<button 
					className="sidebar-new-btn" 
					onClick={handleNewChat} 
					title="Nuova chat"
					disabled={status === "error"} 
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
						fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
					<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>
					<path d="M12 8v6"/>
					<path d="M9 11h6"/>
					</svg>
				</button>
			</div>

			<div className="sidebar-list">
				{isLoading && <p className="sidebar-status">Caricamento…</p>}
				{!isLoading && status === "error" && (
					<p className="sidebar-status">Offline</p>
				)}
				{!isLoading && status === "ready" && conversations.length === 0 && (
					<p className="sidebar-status">Nessuna chat salvata.</p>
				)}
				{!isLoading && conversations.map((conv) => (
					<ConversationItem
						key={conv.thread_id}
						conversation={conv}
						isActive={conv.thread_id === activeId}
						onSelect={handleSelect}
						onDelete={handleDelete}
						onUpdateTitle={handleUpdateTitle}
					/>
				))}
			</div>
		</aside>
	);
}