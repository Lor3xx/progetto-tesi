from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings
import base64
from pathlib import Path

# LLM - Groq per le chiamate di chat
llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_llm_model,
    temperature=0.2,
)

# Embeddings - HuggingFace in locale, nessuna API key necessaria
embeddings = HuggingFaceEmbeddings(
    model_name=settings.embedding_model,
    model_kwargs={"device": "cpu"},
)


def describe_image(image_path: Path, context: str = "") -> str:
    """
    Invia un'immagine al modello vision Groq e restituisce
    una descrizione testuale dettagliata.

    context: testo del chunk vicino all'immagine, aiuta il modello
             a capire l'argomento e dare una descrizione più precisa.
    """
    # Groq vision accetta immagini come base64 data URL
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = image_path.suffix.lstrip(".")
    mime_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    data_url = f"data:{mime_type};base64,{image_data}"

    context_hint = (
        f"This image comes from a cybersecurity document. "
        f"Nearby text context: {context[:300]}"
        if context else
        "This image comes from a cybersecurity document."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{context_hint}\n\n"
                        "Analyze this image in detail. "
                        "Describe all technical content: diagrams, schemas, attack flows, "
                        "network topologies, code snippets, tables, charts, CVE references, "
                        "or any cybersecurity-relevant information visible. "
                        "Be precise and exhaustive. If the image contains no useful technical "
                        "information (decorative, logo, generic icon), respond only with: SKIP"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        }
    ]

    # Usiamo il client Groq diretto (non LangChain) perché
    # ChatGroq non supporta ancora il formato multimodale con base64
    from groq import Groq
    from config import settings
    _vision_client = Groq(api_key=settings.groq_api_key)

    response = _vision_client.chat.completions.create(
        model=settings.groq_vision_model,
        messages=messages,
        max_tokens=1024,
        temperature=0.1,  # bassa: vogliamo descrizioni fattuali, non creative
    )
    return response.choices[0].message.content.strip()