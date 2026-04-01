"use client";

import { ImageResult } from "@/types";
import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

const ImageCard = ({ img, index }: { img: ImageResult; index: number }) => {
    const [open, setOpen] = useState(false);

    const label = `${img.source} — p. ${img.page}`;
    const shortLabel = label.length > 55 ? label.slice(0, 52) + "…" : label;

    // Il backend serve i file statici da data/images — adatta il path al tuo endpoint
    const imageUrl = `${API_BASE}/images/${encodeURIComponent(
        img.image_path.replace(/\\/g, "/").replace(/^data\/images\//, "")
    )}`;

    return (
        <div className="source-card" onClick={() => setOpen((o) => !o)}>
            <div className="source-header">
                <span className="source-index" style={{ background: "var(--accent2)" }}>
                    {index + 1}
                </span>
                <span className="source-url" title={label}>
                    🖼 {shortLabel}
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
            {open && (
                <div className="image-card-body">
                    <img
                        src={imageUrl}
                        alt={img.description}
                        className="image-card-img"
                        onError={(e) => {
                            const el = e.currentTarget;
                            el.style.display = "none";
                            el.nextElementSibling?.classList.remove("image-card-desc--hidden");
                        }}
                    />
                    <p className="image-card-desc image-card-desc--hidden">
                        {img.description}
                    </p>
                </div>
            )}
        </div>
    );
};

export default ImageCard;