"use client";
import { useRef, useState } from "react";
import { UploadResponse } from "@/types";
import { UploadIcon } from "./UploadIcon";
import { SpinnerIcon } from "./SpinnerIcon";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

type UploadStatus = "idle" | "uploading" | "success" | "duplicate" | "error";

export default function UploadButton({ apiStatus }: { apiStatus: "unknown" | "ready" | "error" }) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [status, setStatus] = useState<UploadStatus>("idle");
    const [message, setMessage] = useState("");

    const autoClear = () => {
        setTimeout(() => {
        setStatus("idle");
        setMessage("");
        }, 4000);
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (fileInputRef.current) fileInputRef.current.value = "";
        if (!file) return;

        if (file.type !== "application/pdf") {
        setStatus("error");
        setMessage("Solo file PDF sono supportati.");
        autoClear();
        return;
        }

        setStatus("uploading");
        setMessage("");

        try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/documents/upload`, {
            method: "POST",
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Errore sconosciuto." }));
            throw new Error(err.detail ?? "Upload fallito.");
        }

        const data: UploadResponse = await res.json();
        setStatus(data.status === "duplicate" ? "duplicate" : "success");
        setMessage(data.message);
        } catch (err: unknown) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Errore durante l'upload.");
        }

        autoClear();
    };

    const isUploading = status === "uploading";

    return (
        <div className="upload-wrapper">
            {/* Feedback pill — visibile solo quando non idle */}
            {status !== "idle" && (
                <span className={`upload-feedback upload-feedback--${status}`} title={message}>
                {statusIcon[status]} {message}
                </span>
            )}

            <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                style={{ display: "none" }}
                onChange={handleFileChange}
            />

            <button
                className={`upload-btn${isUploading ? " upload-btn--loading" : ""}`}
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || apiStatus !== "ready"}
                title="Carica un documento PDF"
            >
                {isUploading ? <SpinnerIcon /> : <UploadIcon />}
                <span>{isUploading ? "Caricamento…" : "Upload PDF"}</span>
            </button>
        </div>
    );
}

/* ── Status icons ────────────────────────────────────────── */
const statusIcon: Record<UploadStatus, string> = {
  idle:      "",
  uploading: "",
  success:   "●",
  duplicate: "●",
  error:     "●",
};

