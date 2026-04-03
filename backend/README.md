# Backend — Progetto Tesi

Backend del progetto, responsabile di creazione chatbot rag ed esposizione API.

## Tecnologie
- Node.js
- langchain e langgraph

## Struttura progetto
```txt
backend/
├─ src/
│  ├─ agent/
│  ├─ api/
│  ├─ services/
│  ├─ test/
│  └─ config.py     # modificare qua le impostazioni del modello
├─ .env
├─ package.json
├─ main.py          # inizializzazione rag
└─ README.md
```

## Configurazione ambiente
1. Crea il file `.env`
2. Imposta le variabili principali:

```env
GROQ_API_KEY | OPENAI_API_KEY
```