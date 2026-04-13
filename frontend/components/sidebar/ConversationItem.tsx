"use client";
import { Props } from "@/types";
import { useEffect, useState } from "react";
import ConfirmDialog from "./ConfirmDialog";
import SettingsDialog from "./SettingsDialog";

function formatDate(isoString: string): string {
	try {
		const date = new Date(isoString);
		const now = new Date();
		let diffDays = (now.getTime() - date.getTime()) / 86_400_000;
		if (diffDays < 0.7) return "oggi";
		if (diffDays < 1.2) return "ieri";
		diffDays = Math.round(diffDays);
		if (diffDays < 7)  return `${diffDays}gg fa`;
		return date.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
	} catch {
		return "";
	}
}

const getShowSourcesForThread = (threadId: string): boolean => {
	try {
		const stored = sessionStorage.getItem(`show-sources-${threadId}`);
		return stored === null ? true : stored === "true";
	} catch {
		return true;
	}
};

const setShowSourcesForThread = (threadId: string, value: boolean) => {
	try {
		sessionStorage.setItem(`show-sources-${threadId}`, String(value));
	} catch (e) {
		console.error("Error saving show-sources preference:", e);
	}
};

export default function ConversationItem({ conversation, isActive, onSelect, onDelete, onUpdateTitle }: Props) {
	const [isEditing, setIsEditing] = useState(false);
	const [editedTitle, setEditedTitle] = useState(conversation.title);
	const [showConfirm, setShowConfirm] = useState(false);
	const [showSettings, setShowSettings] = useState(false);
	const [isMenuOpen, setIsMenuOpen] = useState(false);
	const [showSources, setShowSources] = useState(
		getShowSourcesForThread(conversation.thread_id)
	);

	const handleDelete = () => setShowConfirm(true);

	const handleEdit = () => {
		setIsEditing(true);
		setIsMenuOpen(false);
	};

	const handleOpenSettings = () => {
		setShowSettings(true);
		setIsMenuOpen(false);
	};

	const handleCancel = () => {
		setEditedTitle(conversation.title);
		setIsEditing(false);
	};

	const handleSave = async () => {
		if (!editedTitle.trim()) {
			handleCancel();
			return;
		}

		onUpdateTitle(conversation.thread_id, editedTitle.trim());
		setIsEditing(false);
	};

	const handleToggleSources = () => {
		const newValue = !showSources;
		setShowSources(newValue);
		setShowSourcesForThread(conversation.thread_id, newValue);
		
		// Notifica ChatBody del cambio
		window.dispatchEvent(new CustomEvent("show-sources-changed", { 
			detail: { threadId: conversation.thread_id, showSources: newValue }
		}));
	};

	useEffect(() => {
		if (!isMenuOpen) return;

		const handleClickOutside = (e: MouseEvent) => {
			const target = e.target as HTMLElement;
			// Se clicchi fuori dal menu, chiudi
			if (!target.closest('.conv-item-actions')) {
				setIsMenuOpen(false);
			}
		};

		document.addEventListener('click', handleClickOutside);
		return () => document.removeEventListener('click', handleClickOutside);
	}, [isMenuOpen]);

	useEffect(() => {
		if (isActive) {
			setShowSources(getShowSourcesForThread(conversation.thread_id));
		}
	}, [isActive, conversation.thread_id]);

	return (
		<div
			className={`conv-item${isActive ? " active" : ""}`}
			onClick={() => !isEditing && onSelect(conversation.thread_id)}
			role="button"
			tabIndex={0}
			onKeyDown={(e) => e.key === "Enter" && !isEditing && onSelect(conversation.thread_id)}
		>
			<div className="conv-item-body">
				{isEditing ? (
					<input
						className="conv-item-input"
						value={editedTitle}
						onChange={(e) => setEditedTitle(e.target.value)}
						onBlur={handleSave}
						onKeyDown={(e) => {
							if (e.key === "Enter") handleSave();
							if (e.key === "Escape") handleCancel();
						}}
						autoFocus
					/>
				) : (
					<>
						<span className="conv-item-title">{conversation.title}</span>
						<span className="conv-item-date">
							{formatDate(conversation.updated_at)}
						</span>
					</>
				)}
			</div>

			<div className="conv-item-actions">
				{/* Menu a 3 punti */}
				<button
					className={`conv-item-menu${isMenuOpen ? " open" : ""}`}
					onClick={(e) => {
						e.stopPropagation();
						setIsMenuOpen(!isMenuOpen);
					}}
					title="Menu"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
						fill="currentColor">
						<circle cx="12" cy="5" r="2"/>
						<circle cx="12" cy="12" r="2"/>
						<circle cx="12" cy="19" r="2"/>
					</svg>
				</button>

				{/* Menu dropdown con azioni */}
				{isMenuOpen && (
					<div className="conv-item-menu-dropdown">
						{/* ✏️ EDIT */}
						<button
							className="conv-item-edit"
							onClick={(e) => {
								e.stopPropagation();
								handleEdit();
							}}
							title="Modifica titolo"
						>
							<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
								fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<path d="M12 20h9"/>
								<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/>
							</svg>
							<span>Modifica</span>
						</button>

						{/* ⚙️ SETTINGS */}
						<button
							className="conv-item-settings"
							onClick={(e) => {
								e.stopPropagation();
								handleOpenSettings();
							}}
							title="Impostazioni"
						>
							<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
								fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<circle cx="12" cy="12" r="3"/>
								<path d="M19.4 15a1.7 1.7 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-.4-1.1 1.7 1.7 0 0 0-1-.6 1.7 1.7 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H2.9a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.1-.4 1.7 1.7 0 0 0 .6-1A1.7 1.7 0 0 0 4.6 6l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6c.3-.4.6-.8.6-1.1V3a2 2 0 1 1 4 0v.1c0 .3.3.7.6 1.1.3.3.7.6 1 .6a1.7 1.7 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.4.3.8.6 1.1.6H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.1.4 1.7 1.7 0 0 0-.6 1z"/>	
							</svg>
							<span>Impostazioni</span>
						</button>

						{/* 👁️ SHOW/HIDE SOURCES - TOGGLE */}
						<button
							className={`conv-item-sources${showSources ? " active" : ""}`}
							onClick={(e) => {
								e.stopPropagation();
								handleToggleSources();
							}}
							title={showSources ? "Nascondi fonti" : "Mostra fonti"}
						>
							<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
								fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
								<circle cx="12" cy="12" r="3"/>
							</svg>
							<span>{showSources ? "Nascondi fonti" : "Mostra fonti"}</span>
						</button>

						{/* 🗑 DELETE */}
						<button
							className="conv-item-del"
							onClick={(e) => {
								e.stopPropagation();
								setIsMenuOpen(false);
								handleDelete();
							}}
							title="Elimina"
						>
							<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
								fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<polyline points="3 6 5 6 21 6"/>
								<path d="M19 6l-1 14H6L5 6"/>
								<path d="M10 11v6M14 11v6"/>
								<path d="M9 6V4h6v2"/>
							</svg>
							<span>Elimina</span>
						</button>
					</div>
				)}
			</div>

			{showConfirm && (
				<ConfirmDialog
					message="Eliminare questa conversazione? L'operazione non è reversibile."
					onConfirm={() => { setShowConfirm(false); onDelete(conversation.thread_id); }}
					onCancel={() => setShowConfirm(false)}
				/>
			)}

			{showSettings && (
				<SettingsDialog
					threadId={conversation.thread_id}
					onClose={() => setShowSettings(false)}
				/>
			)}
		</div>
	);
}