"use client";
import { useEffect, useState } from "react";
import { Document } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function PdfIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
    </svg>
  );
}

export default function DocumentsPanel({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/documents/list`)
      .then((r) => r.json())
      .then((d) => setDocuments(d.documents ?? []))
      .catch(() => setError("Impossibile caricare i documenti."))
      .finally(() => setLoading(false));
  }, [isOpen]);

  const userDocs   = documents.filter((d) => d.source === "user");
  const systemDocs = documents.filter((d) => d.source === "system");

  return (
    <>
      {/* Backdrop semi-trasparente */}
      {isOpen && (
        <div className="docs-backdrop" onClick={onClose} />
      )}

      <div className={`docs-panel${isOpen ? " docs-panel--open" : ""}`}>
        <div className="docs-panel-header">
          <span>Documenti</span>
          <button className="docs-panel-close" onClick={onClose} aria-label="Chiudi">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="docs-panel-list">
          {loading && (
            <p className="docs-status">Caricamento…</p>
          )}
          {error && (
            <p className="docs-status docs-status--error">{error}</p>
          )}
          {!loading && !error && documents.length === 0 && (
            <p className="docs-status">Nessun documento disponibile.</p>
          )}

          {userDocs.length > 0 && (
            <div className="docs-group">
              <span className="docs-group-label">Caricati da te</span>
              {userDocs.map((doc) => (
                <DocItem key={doc.filename} doc={doc} />
              ))}
            </div>
          )}

          {systemDocs.length > 0 && (
            <div className="docs-group">
              <span className="docs-group-label">Knowledge base</span>
              {systemDocs.map((doc) => (
                <DocItem key={doc.filename} doc={doc} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function DocItem({ doc }: { doc: Document }) {
  return (
    <button
      className="docs-item"
      onClick={() => window.open(`${API_BASE}/documents/serve/${doc.filename}`, "_blank")}
      title={doc.filename}
    >
      <PdfIcon />
      <span className="docs-item-name">{doc.filename}</span>
      <span className="docs-item-size">{formatSize(doc.size_bytes)}</span>
    </button>
  );
}