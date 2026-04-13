"use client";
import { Settings, SettingsDialogProps } from "@/types";
import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_RAG_API_URL ?? "http://localhost:8000";

export default function SettingsDialog({ threadId, onClose }: SettingsDialogProps) {
	const [settings, setSettings] = useState<Settings>({
		tone: "technical",
		temperature: 0.2,
		response_length: "balanced",
	});
	const [isLoading, setIsLoading] = useState(true);
	const [isSaving, setIsSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Carica le impostazioni attuali
	useEffect(() => {
		const fetchSettings = async () => {
            try {
                setIsLoading(true);
                const res = await fetch(`${API_BASE}/conversations/${threadId}/settings`);
                
                // Log di debug
                console.log(`[SettingsDialog] Fetching ${API_BASE}/conversations/${threadId}/settings`);
                console.log(`[SettingsDialog] Status: ${res.status}`);
                
                if (!res.ok) {
                    const errorText = await res.text();
                    console.log(`[SettingsDialog] Error response: ${errorText}`);
                    throw new Error(`HTTP ${res.status}: ${errorText}`);
                }
                
                const data = await res.json();
                console.log(`[SettingsDialog] Settings loaded:`, data);
                setSettings(data);
                setError(null);
            } catch (err) {
                console.error("[SettingsDialog] fetch error:", err);
            } finally {
                setIsLoading(false);
            }
        };
		fetchSettings();
	}, [threadId]);

	const handleSave = async () => {
		try {
			setIsSaving(true);
			setError(null);

			const res = await fetch(`${API_BASE}/conversations/${threadId}/settings`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(settings),
			});

			if (!res.ok) throw new Error(`HTTP ${res.status}`);

			onClose();
		} catch (err) {
			console.error("[SettingsDialog] save error:", err);
			setError("Errore nel salvataggio delle impostazioni");
		} finally {
			setIsSaving(false);
		}
	};

	return (
		<div className="dialog-overlay" onClick={onClose}>
			<div className="dialog-content" onClick={(e) => e.stopPropagation()}>
				<div className="dialog-header">
					<h2>Impostazioni Chat</h2>
					<button className="dialog-close" onClick={onClose}>×</button>
				</div>

				{isLoading ? (
					<div className="dialog-body">
						<p>Caricamento...</p>
					</div>
				) : (
					<>
						<div className="dialog-body">
							{error && <p className="dialog-error">{error}</p>}

							{/* Tono */}
							<div className="settings-group">
								<label>Stile di risposta</label>
								<div className="settings-options">
									{(["technical", "simple", "educational"] as const).map((tone) => (
										<button
											key={tone}
											className={`settings-option${settings.tone === tone ? " active" : ""}`}
											onClick={() => setSettings({ ...settings, tone })}
										>
											{tone === "technical" && "Tecnico"}
											{tone === "simple" && "Semplice"}
											{tone === "educational" && "Didattico"}
										</button>
									))}
								</div>
								<p className="settings-description">
									{settings.tone === "technical" && "Linguaggio tecnico preciso con acronimi."}
									{settings.tone === "simple" && "Spiegazioni semplici senza gergo tecnico."}
									{settings.tone === "educational" && "Approccio didattico e progressivo."}
								</p>
							</div>

							{/* Temperature */}
							<div className="settings-group">
								<label>Temperatura (creatività)</label>
								<input
									type="range"
									min="0"
									max="2"
									step="0.1"
									value={settings.temperature}
									onChange={(e) =>
										setSettings({ ...settings, temperature: parseFloat(e.target.value) })
									}
									className="settings-slider"
								/>
								<div className="settings-temp-display">
									<span className="temp-value">{settings.temperature.toFixed(1)}</span>
									<span className="temp-label">
										{settings.temperature <= 0.3 && "Deterministico"}
										{settings.temperature >= 0.4 && settings.temperature <= 0.7 && "Bilanciato"}
										{settings.temperature >= 0.8 && settings.temperature < 1.5 && "Creativo"}
										{settings.temperature >= 1.5 && "Molto creativo (rischio di risposte tecniche meno precise)"}
									</span>
								</div>
							</div>

							{/* Lunghezza risposta */}
							<div className="settings-group">
								<label>Lunghezza risposta</label>
								<div className="settings-options">
									{(["concise", "balanced", "detailed"] as const).map((length) => (
										<button
											key={length}
											className={`settings-option${settings.response_length === length ? " active" : ""}`}
											onClick={() => setSettings({ ...settings, response_length: length })}
										>
											{length === "concise" && "Concisa"}
											{length === "balanced" && "Bilanciata"}
											{length === "detailed" && "Dettagliata"}
										</button>
									))}
								</div>
								<p className="settings-description">
									{settings.response_length === "concise" && "Max ~150 token"}
									{settings.response_length === "balanced" && "~300-400 token"}
									{settings.response_length === "detailed" && "600+ token"}
								</p>
							</div>
						</div>

						<div className="dialog-footer">
							<button className="btn-cancel" onClick={onClose} disabled={isSaving}>
								Annulla
							</button>
							<button
								className="btn-save"
								onClick={handleSave}
								disabled={isSaving}
							>
								{isSaving ? "Salvataggio..." : "Salva"}
							</button>
						</div>
					</>
				)}
			</div>
		</div>
	);
}