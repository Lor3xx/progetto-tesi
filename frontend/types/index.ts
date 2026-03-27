export type SourceDocument = {
    content: string;
    metadata: Record<string, string>;
}

export type Message = {
    id: string;
    role: "user" | "assistant";
    text: string;
    sources?: SourceDocument[];
    elapsed?: number;
    timestamp: Date;
}