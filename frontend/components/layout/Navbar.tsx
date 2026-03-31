"use client";
import { useEffect, useState } from "react";
import UploadButton from "./UploadButton";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

const Navbar = () => {
    const [apiStatus, setApiStatus] = useState<"unknown" | "ready" | "error">("unknown");
    
    // ── Health check ──────────────────────────────────────────────────────────
    useEffect(() => {
        fetch(`${API_BASE}/health`)
        .then((r) => r.json())
        .then((d) => setApiStatus(d.status === "ready" ? "ready" : "error"))
        .catch(() => setApiStatus("error"));
    }, []);
    
    return (
        <header className="header">
			<div className="header-logo">🔍</div>
			<div>
				<div className="header-title">RAG Document Search</div>
				<div className="header-sub">Interroga i tuoi documenti con l'AI</div>
			</div>

            <UploadButton />

			<span className={`status-badge status-${apiStatus}`}>
				{apiStatus === "ready" ? "● online" : apiStatus === "error" ? "● offline" : "● …"}
			</span>
		</header>
    )
}

export default Navbar;