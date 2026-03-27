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
    sources?: string[];
    images?: ImageResult[];
    status?: "complete" | "partial" | "unknown" | "off_topic";
    elapsed?: number;
    timestamp: Date;
}