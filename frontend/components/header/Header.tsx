"use client";
import { useEffect, useState } from "react";
import UploadButton from "./UploadButton";
import DocumentsPanel from "../documents/DocumentsPanel";
import { DocumentsIcon } from "../documents/UploadIcon";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

const Header = () => {
    const [apiStatus, setApiStatus] = useState<"unknown" | "ready" | "error">("unknown");
    const [isPanelOpen, setIsPanelOpen] = useState(false);
    
    // ── Health check ──────────────────────────────────────────────────────────
    useEffect(() => {
        fetch(`${API_BASE}/health`)
        .then((r) => r.json())
        .then((d) => setApiStatus(d.status === "ready" ? "ready" : "error"))
        .catch(() => setApiStatus("error"));
    }, []);
    
    return (
        <>
            <header className="header">
                <button
                    className="header-hamburger"
                    onClick={() => window.dispatchEvent(new CustomEvent("toggle-sidebar"))}
                    aria-label="Menu"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="3" y1="6" x2="21" y2="6"/>
                        <line x1="3" y1="12" x2="21" y2="12"/>
                        <line x1="3" y1="18" x2="21" y2="18"/>
                    </svg>
                </button>

                <div className="header-logo">🔍</div>
                <div>
                    <div className="header-title">{"RAG Document Search"}</div>
                    <div className="header-sub">{"Interroga i tuoi documenti con l'AI"}</div>
                </div>

                <div className="upload-wrapper">
                    <button
                        className={`upload-btn${isPanelOpen ? " upload-btn--active" : ""}`}
                        onClick={() => setIsPanelOpen((v) => !v)}
                        disabled={apiStatus !== "ready"}
                        title="Vedi documenti caricati"
                    >
                        <DocumentsIcon />
                        <span>Documenti</span>
                    </button>

                    <UploadButton apiStatus={apiStatus} />
                </div>

                <span className={`status-badge status-${apiStatus}`}>
                    {apiStatus === "ready" ? "● online" : apiStatus === "error" ? "● offline" : "● …"}
                </span>
            </header>

            <DocumentsPanel
                isOpen={isPanelOpen}
                onClose={() => setIsPanelOpen(false)}
            />
        </>
    )
}

export default Header;