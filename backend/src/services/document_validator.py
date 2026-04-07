"""
Valida se un PDF è pertinente alla cybersecurity prima di indicizzarlo.

Flusso:
  1. Estrae un campione di testo dal PDF (prime N pagine)
  2. Calcola similarity tra testo e un corpus di riferimento cyber
  3. score >= THRESHOLD_HIGH  → accetta direttamente
     score <  THRESHOLD_LOW   → rifiuta direttamente
     in mezzo                 → chiede all'LLM 
"""

from pathlib import Path

import numpy as np
import pymupdf
from langchain_core.messages import HumanMessage, SystemMessage
from services.groq_client import llm_eval

from config import settings
from services.groq_client import embeddings
import json 

# ── Corpus di riferimento cybersecurity ──────────────────────────────────────
# Frasi rappresentative del dominio. La media dei loro embedding
# costituisce il "centroide" del dominio cyber.
_CYBER_REFERENCE_SENTENCES = [
    "vulnerability assessment and penetration testing techniques",
    "network security firewall intrusion detection prevention",
    "malware analysis reverse engineering threat intelligence",
    "cryptography encryption protocols TLS SSL PKI certificates",
    "OWASP top ten web application security vulnerabilities",
    "incident response forensics security operations center SOC",
    "CVE exploit buffer overflow injection attacks",
    "zero day vulnerability patch management security updates",
    "identity access management authentication authorization",
    "ransomware phishing social engineering cyber attacks",
    "SIEM log analysis threat hunting detection rules",
    "docker kubernetes container security cloud infrastructure",
    "red team blue team purple team security testing",
    "data breach privacy GDPR compliance risk management",
    "network traffic analysis packet inspection wireshark",
]

DOC_RELEVANCE_PROMPT = """
You are an expert in evaluating documents for cybersecurity relevance. 
You are evaluating whether a document is relevant to cybersecurity.

Document sample (first pages):
---
{text_sample[:2000]}
---

A document is considered relevant if it covers topics such as:
cybersecurity, cryptography, vulnerabilities, malware, cyber attacks,
digital privacy, IT compliance, digital forensics, operating systems in a security context, etc.

A document is NOT relevant if it covers topics unrelated to cybersecurity
(e.g., cooking, medieval history, literature, general medicine, sports, etc.).

A document is also NOT relevant if it talks about IT topics but not in a security context 
(e.g., programming, machine learning, general networking, etc.) — it must have a clear cybersecurity focus.

Respond ONLY in this JSON format:
{
  "relevant": true/false,
  "reason": "short justification (max 15 words)"
}
"""

# Cache del centroide — calcolato una sola volta al primo utilizzo
_cyber_centroid: np.ndarray | None = None


def _get_cyber_centroid() -> np.ndarray:
    """Calcola (e cachea) l'embedding medio del corpus di riferimento."""
    global _cyber_centroid
    if _cyber_centroid is None:
        vecs = embeddings.embed_documents(_CYBER_REFERENCE_SENTENCES)
        _cyber_centroid = np.mean(np.array(vecs), axis=0)
    return _cyber_centroid


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _extract_sample_text(pdf_path: Path, max_pages: int = settings.sample_pages_for_validation) -> str:
    """
    Estrae testo grezzo dalle prime `max_pages` pagine del PDF.
    Usa pymupdf direttamente (niente markdown, serve solo testo per la valutazione).
    """
    doc = pymupdf.open(str(pdf_path))
    pages_to_read = min(max_pages, len(doc))
    parts = []
    for i in range(pages_to_read):
        text = doc[i].get_text("text")
        if text.strip():
            parts.append(text.strip())
    doc.close()
    return "\n".join(parts)


def _compute_cyber_score(text: str) -> float:
    """
    Restituisce la cosine similarity tra il testo campionato
    e il centroide del corpus cybersecurity.
    """
    centroid = _get_cyber_centroid()
    text_vec = np.array(embeddings.embed_query(text[:3000]))  # tronca per sicurezza
    return _cosine_similarity(text_vec, centroid)


def _ask_llm(text_sample: str) -> tuple[bool, str]:
    response = llm_eval.invoke([
        SystemMessage(content=DOC_RELEVANCE_PROMPT),
        HumanMessage(content=text_sample),
    ])

    try:
        clean = (response.content.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        return False, "LLM non ha risposto con JSON valido"

    return bool(parsed.get("relevant", False)), parsed.get("reason", "Nessuna motivazione fornita")

# ── Public API ────────────────────────────────────────────────────────────────

class ValidationResult:
    __slots__ = ("accepted", "score", "method", "reason")

    def __init__(self, accepted: bool, score: float, method: str, reason: str):
        self.accepted = accepted
        self.score    = score
        self.method   = method   # "embedding_high" | "embedding_low" | "llm"
        self.reason   = reason


def validate_document(pdf_path: Path) -> ValidationResult:
    """
    Entry point principale. Valida il PDF e restituisce un ValidationResult.

    accepted=True  → il documento può essere indicizzato
    accepted=False → il documento va eliminato e l'utente notificato
    """
    # 1. Estrai testo campione
    sample = _extract_sample_text(pdf_path)

    if len(sample.strip()) < settings.min_chars_for_validation:
        return ValidationResult(
            accepted=False,
            score=0.0,
            method="embedding_low",
            reason="Il PDF non contiene testo sufficiente per la valutazione.",
        )

    # 2. Calcola score embedding
    score = _compute_cyber_score(sample)
    print(f"Validation score for {pdf_path.name}: {score:.4f}")

    # 3. Decisione in base alle soglie
    if score >= settings.min_ingestion_score:
        return ValidationResult(
            accepted=True,
            score=score,
            method="embedding_high",
            reason="Documento pertinente alla cybersecurity (punteggio embedding elevato).",
        )

    if score < settings.min_acceptable_score:
        return ValidationResult(
            accepted=False,
            score=score,
            method="embedding_low",
            reason="Il documento non sembra inerente alla cybersecurity.",
        )

    # 4. Zona grigia → LLM decide
    llm_accepted, llm_reason = _ask_llm(sample)
    print(f"LLM decision for {pdf_path.name}: accepted={llm_accepted}, reason={llm_reason}")
    return ValidationResult(
        accepted=llm_accepted,
        score=score,
        method="llm",
        reason=llm_reason,
    )