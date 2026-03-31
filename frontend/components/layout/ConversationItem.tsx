"use client";
import { ConversationPreview } from "@/types";
import { useState } from "react";

interface Props {
	conversation: ConversationPreview;
	isActive: boolean;
	onSelect: (threadId: string) => void;
	onDelete: (threadId: string) => void;
	onUpdateTitle: (threadId: string, title: string) => void;
}

function formatDate(isoString: string): string {
	try {
		const date = new Date(isoString);
		const now = new Date();
		var diffDays = (now.getTime() - date.getTime()) / 86_400_000;
		if (diffDays < 0.7) return "oggi";
		if (diffDays < 1.2) return "ieri";
		diffDays = Math.round(diffDays);
		if (diffDays < 7)  return `${diffDays}gg fa`;
		return date.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
	} catch {
		return "";
	}
}

export default function ConversationItem({ conversation, isActive, onSelect, onDelete, onUpdateTitle }: Props) {
	const [isEditing, setIsEditing] = useState(false);
	const [editedTitle, setEditedTitle] = useState(conversation.title);

	const handleDelete = () => {
		if (confirm("Eliminare questa conversazione?")) onDelete(conversation.thread_id);
	};

	const handleEdit = () => {
		setIsEditing(true);
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
				</button>

				{/* 🗑 DELETE */}
				<button
					className="conv-item-del"
					onClick={(e) => {
						e.stopPropagation();
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
				</button>
			</div>
		</div>
	);
}