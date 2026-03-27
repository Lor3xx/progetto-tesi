"use client";
import { useEffect, useRef } from "react";

interface InputBarProps {
    onSubmit: (text: string) => void;
    loading: boolean;
    input: string;
    setInput: (value: string) => void;
}

const InputBar = ({ onSubmit, loading, input, setInput }: InputBarProps) => {
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        const ta = inputRef.current;
        if (!ta) return;
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 140) + "px";
    }, [input]);

    const handleSubmit = () => {
        const q = input.trim();
        if (!q || loading) return;
        onSubmit(q);
    };

    const handleKey = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="input-bar">
            <div className="input-inner">
                <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Scrivi la tua domanda…"
                    rows={1}
                    disabled={loading}
                />
                <button
                    className="send-btn"
                    onClick={handleSubmit}
                    disabled={loading || !input.trim()}
                    aria-label="Invia"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                        <line x1="22" y1="2" x2="11" y2="13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                </button>
            </div>
            <p className="input-hint">Enter per inviare · Shift+Enter per andare a capo</p>
        </div>
    );
};

export default InputBar;