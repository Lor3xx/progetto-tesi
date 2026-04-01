"use client";
import { SourceDocument } from "@/types";
import { useState } from "react";

const SourceCard = ({ doc, index }: { doc: SourceDocument; index: number }) => {
    const [open, setOpen] = useState(false);
    const source =
        doc.metadata?.source ?? doc.metadata?.url ?? doc.metadata?.title ?? `Fonte ${index + 1}`;
    const shortSource = source.length > 55 ? source.slice(0, 52) + "…" : source;

    return (
        <div className="source-card" onClick={() => setOpen((o) => !o)}>
            <div className="source-header">
                <span className="source-index">{index + 1}</span>
                <span className="source-url" title={source}>
                {shortSource}
                </span>
                <svg
                className={`source-chevron ${open ? "open" : ""}`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                >
                <polyline points="6 9 12 15 18 9" />
                </svg>
            </div>
            {open && <p className="source-body">{doc.content}</p>}
        </div>
    );
}

export default SourceCard;