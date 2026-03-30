"use client";
import { ConversationPreview } from "@/types";

interface Props {
	conversation: ConversationPreview;
	isActive: boolean;
	onSelect: (threadId: string) => void;
	onDelete: (threadId: string) => void;
}

function formatDate(isoString: string): string {
	try {
		const date = new Date(isoString);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - date.getTime()) / 86_400_000);
		if (diffDays === 0) return "oggi";
		if (diffDays === 1) return "ieri";
		if (diffDays < 7)  return `${diffDays}g fa`;
		return date.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
	} catch {
		return "";
	}
}

export default function ConversationItem({ conversation, isActive, onSelect, onDelete }: Props) {
	const handleDelete = (e: React.MouseEvent) => {
		e.stopPropagation();
		if (confirm("Eliminare questa conversazione?")) onDelete(conversation.thread_id);
	};

	return (
		<div
			className={`conv-item${isActive ? " active" : ""}`}
			onClick={() => onSelect(conversation.thread_id)}
			role="button"
			tabIndex={0}
			onKeyDown={(e) => e.key === "Enter" && onSelect(conversation.thread_id)}
		>
			<div className="conv-item-body">
				<span className="conv-item-title">{conversation.title}</span>
				<span className="conv-item-date">{formatDate(conversation.updated_at)}</span>
			</div>

			<button className="conv-item-del" onClick={handleDelete} title="Elimina">
				<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
					fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
					<polyline points="3 6 5 6 21 6"/>
					<path d="M19 6l-1 14H6L5 6"/>
					<path d="M10 11v6M14 11v6"/>
					<path d="M9 6V4h6v2"/>
				</svg>
			</button>
		</div>
	);
}