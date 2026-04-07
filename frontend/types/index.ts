export interface SourceDocument {
    content: string;
    metadata: Record<string, string>;
}

export interface ImageResult {
    source: string;
    image_path: string;
    page: number;
    description: string;
}

export interface Message {
    id: string;
    role: "user" | "assistant";
    text: string;
    sources?: SourceDocument[];
    images?: ImageResult[];
    status?: "complete" | "partial" | "unknown" | "off_topic";
    elapsed?: number;
    timestamp: Date;
}

export interface ConversationPreview {
	thread_id: string;
	title: string;
	created_at: string;   // ISO-8601 UTC
	updated_at: string;   // ISO-8601 UTC
	message_count: number;
}
 
export interface ConversationListResponse {
	conversations: ConversationPreview[];
	total: number;
}

export interface UploadResponse {
	filename: string;
	saved_as: string;
	size_bytes: number;
	status: string;
	message: string;
}

export interface Props {
	conversation: ConversationPreview;
	isActive: boolean;
	onSelect: (threadId: string) => void;
	onDelete: (threadId: string) => void;
	onUpdateTitle: (threadId: string, title: string) => void;
}

export interface ConfirmDialogProps {
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
}

export interface InputBarProps {
	onSubmit: (text: string) => void;
	loading: boolean;
	input: string;
	setInput: (value: string) => void;
  	online: boolean;
}

export interface Document {
  filename: string;
  size_bytes: number;
  source: "user" | "system";
}