"use client";
import { useEffect } from "react";
import { ConfirmDialogProps } from "@/types";

export default function ConfirmDialog({ message, onConfirm, onCancel }: ConfirmDialogProps) {
    // Blocca scroll e chiude con Escape
    useEffect(() => {
        document.body.style.overflow = "hidden";
        const handleKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") onCancel();
        };
        window.addEventListener("keydown", handleKey);
        return () => {
        document.body.style.overflow = "";
        window.removeEventListener("keydown", handleKey);
        };
    }, [onCancel]);

    return (
        <div className="dialog-overlay" onClick={onCancel}>
        <div className="dialog-box" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-icon">🗑️</div>
            <p className="dialog-message">{message}</p>
            <div className="dialog-actions">
            <button className="dialog-btn dialog-btn--confirm" onClick={onConfirm}>
                Elimina
            </button>
            <button className="dialog-btn dialog-btn--cancel" onClick={onCancel}>
                Annulla
            </button>
            </div>
        </div>
        </div>
    );
}