"""
Router per la gestione e il listing delle conversazioni salvate da LangGraph
su SQLite tramite SqliteSaver.

Le tabelle rilevanti create da SqliteSaver sono:
  - checkpoints          (thread_id, checkpoint_ns, checkpoint_id, ...)

Da queste ricaviamo thread_id, timestamp e il primo messaggio utente per
costruire l'anteprima da mostrare nella sidebar.
"""

from __future__ import annotations

from copyreg import pickle
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from config import settings 
from api.schemas import ConversationListResponse, ConversationPreview 

router = APIRouter(prefix="/conversations", tags=["conversations"])

# ---------------------------------------------------------------------------
# Helper: connessione al DB
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """
    Apre una connessione read-only al database SQLite usato da SqliteSaver.
    Usa `settings.sqlite_path` — assicurati che questo campo esista in
    src/config.py, ad es.:
        sqlite_path: str = "checkpoints.db"
    """
    try:
        # uri=True + ?mode=ro apre in sola lettura senza bloccare il writer
        conn = sqlite3.connect(
            settings.sqlite_path,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"Database non disponibile: {e}")


# ---------------------------------------------------------------------------
# Utility: estrai il primo messaggio utente dal JSON dei metadata LangGraph
# ---------------------------------------------------------------------------

def _extract_title_from_checkpoint(raw_checkpoint: bytes | None) -> str:
    data = _parse_checkpoint(raw_checkpoint)

    channel_values: dict = data.get("channel_values", {})

    # campi custom del tuo AgentState
    for field in ("user_query", "query", "input", "question"):
        value = channel_values.get(field)
        if value and isinstance(value, str) and value.strip():
            title = value.strip()
            return title[:80] + ("…" if len(title) > 80 else "")

    # fallback sui messaggi
    messages = channel_values.get("messages", [])
    if messages and isinstance(messages, list):
        for m in messages:
            if isinstance(m, dict) and m.get("type") == "human":
                content = m.get("content")
                if content:
                    title = content.strip()
                    return title[:80] + ("…" if len(title) > 80 else "")

    return "Nuova conversazione"


def _parse_ts_from_checkpoint(raw_checkpoint: bytes | None) -> str:
    data = _parse_checkpoint(raw_checkpoint)

    ts = data.get("ts")

    if not ts:
        return datetime.now(timezone.utc).isoformat()

    try:
        return datetime.fromisoformat(ts).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _parse_checkpoint(raw: bytes | None) -> dict:
    import msgpack

    if not raw:
        return {}

    try:
        return msgpack.unpackb(raw, raw=False)
    except Exception as e:
        print("Errore parsing msgpack:", e)
        return {}

# ---------------------------------------------------------------------------
# Endpoint: lista conversazioni
# ---------------------------------------------------------------------------

@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    #db: sqlite3.Connection = Depends(get_db),
) -> ConversationListResponse:
    """
    Restituisce l'elenco dei thread salvati, ordinati per data di aggiornamento
    decrescente (conversazione più recente prima).

    Ogni elemento include:
    - thread_id
    - title (primo messaggio utente estratto dai metadata)
    - created_at / updated_at
    - message_count (numero di checkpoint con step > 0, proxy del numero di turni)
    """
    db = get_db()  # apre la connessione read-only al DB SQLite
    #print(db)
    try:
        # ----------------------------------------------------------------
        # 1. Conta i thread totali (per la paginazione del frontend)
        # ----------------------------------------------------------------
        total_row = db.execute(
            "SELECT COUNT(DISTINCT thread_id) AS cnt FROM checkpoints"
        ).fetchone()
        total = total_row["cnt"] if total_row else 0

        if total == 0:
            return ConversationListResponse(conversations=[], total=0)

        # ----------------------------------------------------------------
        # 2. Per ogni thread: primo e ultimo checkpoint_id come proxy di data
        #    Usiamo MIN/MAX su checkpoint_id; se sono ULID o timestamp-based
        #    l'ordinamento lessicografico coincide con quello temporale.
        # ----------------------------------------------------------------
        rows = db.execute(
            """
            SELECT
                c.thread_id,
                MIN(c.checkpoint_id) AS first_checkpoint_id,
                MAX(c.checkpoint_id) AS last_checkpoint_id,
                COUNT(*)            AS checkpoint_count
            FROM checkpoints c
            GROUP BY c.thread_id
            ORDER BY last_checkpoint_id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        # ----------------------------------------------------------------
        # 3. Per ogni thread, recupera il metadata del PRIMO checkpoint
        #    (contiene il messaggio iniziale dell'utente).
        # ----------------------------------------------------------------
        conversations: list[ConversationPreview] = []

        for row in rows:
            thread_id = row["thread_id"]

            # Metadata del primo checkpoint → titolo
            # 🔹 primo checkpoint
            first_cp = db.execute(
                """
                SELECT checkpoint
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY checkpoint_id ASC
                """,
                (thread_id,),
            ).fetchall()

            # 🔹 trova primo con messaggi
            first_with_content = None
            for r in first_cp:
                data = _parse_checkpoint(r["checkpoint"])
                if data.get("channel_values", {}).get("messages"):
                    first_with_content = r["checkpoint"]
                    break

            # 🔹 ultimo checkpoint
            last_cp = db.execute(
                """
                SELECT checkpoint
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY checkpoint_id DESC
                LIMIT 1
                """,
                (thread_id,),
            ).fetchone()

            title = _extract_title_from_checkpoint(first_with_content)
            created_at = _parse_ts_from_checkpoint(first_with_content)
            updated_at = _parse_ts_from_checkpoint(last_cp["checkpoint"] if last_cp else None)
            # Stima message_count: ogni coppia (utente + assistente) genera
            # più checkpoint; usiamo checkpoint_count // 2 come approssimazione.
            message_count = max(1, row["checkpoint_count"] // 2)

            conversations.append(
                ConversationPreview(
                    thread_id=thread_id,
                    title=title,
                    created_at=created_at,
                    updated_at=updated_at,
                    message_count=message_count,
                )
            )

        db.close()
        return ConversationListResponse(conversations=conversations, total=total)

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {e}")


# ---------------------------------------------------------------------------
# Endpoint: dettaglio singola conversazione (opzionale, utile per il frontend)
# ---------------------------------------------------------------------------

@router.get("/{thread_id}", response_model=ConversationPreview)
async def get_conversation(
    thread_id: str,
    #db: sqlite3.Connection = Depends(get_db),
) -> ConversationPreview:
    """
    Restituisce i metadati di una singola conversazione dato il thread_id.
    Utile per aggiornare il titolo nella sidebar dopo che l'utente ha inviato
    il primo messaggio.
    """
    db = get_db()  # apre la connessione read-only al DB SQLite
    try:
        row = db.execute(
            """
            SELECT
                MIN(checkpoint_id) AS first_checkpoint_id,
                MAX(checkpoint_id) AS last_checkpoint_id,
                COUNT(*)           AS checkpoint_count
            FROM checkpoints
            WHERE thread_id = ?
            """,
            (thread_id,),
        ).fetchone()

        if not row or row["checkpoint_count"] == 0:
            raise HTTPException(status_code=404, detail="Conversazione non trovata")

        # 🔹 primo checkpoint
        first_cp = db.execute(
            """
            SELECT checkpoint
            FROM checkpoints
            WHERE thread_id = ?
            ORDER BY checkpoint_id ASC
            """,
            (thread_id,),
        ).fetchone()

        # 🔹 trova primo con messaggi
        first_with_content = None
        for r in first_cp:
            data = _parse_checkpoint(r["checkpoint"])
            if data.get("channel_values", {}).get("messages"):
                first_with_content = r["checkpoint"]
                break

        # 🔹 ultimo checkpoint
        last_cp = db.execute(
            """
            SELECT checkpoint
            FROM checkpoints
            WHERE thread_id = ?
            ORDER BY checkpoint_id DESC
            LIMIT 1
            """,
            (thread_id,),
        ).fetchone()

        title = _extract_title_from_checkpoint(first_with_content)
        created_at = _parse_ts_from_checkpoint(first_with_content)
        updated_at = _parse_ts_from_checkpoint(last_cp["checkpoint"] if last_cp else None)
        
        db.close()
        return ConversationPreview(
            thread_id=thread_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            message_count=max(1, row["checkpoint_count"] // 2),
        )

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {e}")


# ---------------------------------------------------------------------------
# Endpoint: elimina una conversazione (cancella i checkpoint da SQLite)
# ---------------------------------------------------------------------------

@router.delete("/{thread_id}", status_code=204)
async def delete_conversation(thread_id: str) -> None:
    """
    Elimina tutti i checkpoint e i metadata associati a un thread_id.
    Attenzione: apre il DB in modalità scrittura (non read-only).
    """
    try:
        conn = sqlite3.connect(
            settings.sqlite_path,
            check_same_thread=False,
        )
        conn.execute(
            "DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Errore eliminazione: {e}")