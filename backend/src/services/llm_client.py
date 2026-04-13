from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings
import base64
from pathlib import Path
from langchain_classic.chains.hyde.base import HypotheticalDocumentEmbedder
from langchain_core.prompts import PromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# ---- Modelli Groq e HF deprecati ----
# LLM - Groq per le chiamate di chat
llm_groq = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_llm_model,
    temperature=0.2,
)

# LLM per valutazione e miglioramento iterativo della risposta
llm_eval_groq = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_eval_model,
    temperature=0.0,  # valutazione più oggettiva possibile
)

# Embeddings - HuggingFace in locale, nessuna API key necessaria
embeddings_hf = HuggingFaceEmbeddings(
    model_name=settings.hf_embedding_model,
    model_kwargs={"device": "cpu"},
)


# ---- Modelli Google Gemini ----
# LLM - Gemini per le chiamate di chat
llm_gemini = ChatGoogleGenerativeAI(
    google_api_key=settings.gemini_api_key,
    model=settings.gemini_llm_model,
    temperature=0.2,
)

# LLM per valutazione e miglioramento iterativo della risposta
llm_eval_gemini = ChatGoogleGenerativeAI(
    google_api_key=settings.gemini_api_key,
    model=settings.gemini_eval_model,
    temperature=0.0,  # valutazione più oggettiva possibile
)

# Embeddings - Google Gemini (API-based, niente locale)
embeddings_gemini = GoogleGenerativeAIEmbeddings(
    google_api_key=settings.gemini_api_key,
    model=settings.gemini_embedding_model,
)

# ---- Modello attivo: Gemini o Groq e HF ----
llm = llm_gemini
llm_eval = llm_eval_groq
embeddings = embeddings_hf
llm_enhance = llm_groq
llm_validator = llm_groq

# Modello con temperatura dinamica
def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Ritorna LLM con temperatura configurabile."""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.gemini_api_key,
        model=settings.gemini_llm_model,
        temperature=temperature,
    )

llm_hyde = ChatGoogleGenerativeAI(
    google_api_key=settings.gemini_api_key,
    model=settings.gemini_hyde_model,
    temperature=0.2,
)


# --- HyDE ---
hyde_prompt = PromptTemplate.from_template(
    """You are a cybersecurity expert. Write a brief technical paragraph (3-5 sentences) 
    that could appear in a cybersecurity document and directly answers this question:

    {QUESTION}

    Write only the paragraph, no introduction, no conclusion, no commentary."""
)

hyde_embedder = HypotheticalDocumentEmbedder.from_llm(
    llm=llm_hyde,
    base_embeddings=embeddings,
    custom_prompt=hyde_prompt,
)


def describe_image(image_path: Path, context: str = "") -> str:
    """
    Invia un'immagine al modello e restituisce
    una descrizione testuale dettagliata.

    context: testo del chunk vicino all'immagine, aiuta il modello
             a capire l'argomento e dare una descrizione più precisa.
    """
    
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