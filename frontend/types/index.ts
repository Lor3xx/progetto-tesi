export type SourceDocument = {
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