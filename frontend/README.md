# Frontend – Progetto Tesi

Breve documentazione del frontend del progetto.

## Panoramica
Questo modulo contiene l’interfaccia utente dell’applicazione, sviluppata per comunicare con il backend tramite API.

## Tecnologie
- HTML, CSS, TypeScript
- Framework frontend: React
- Node.js e npm

## Requisiti
- Node.js (versione LTS consigliata)
- npm

## Struttura principale
```text
frontend/
├─ app/          # Pagina principale e layout
├─ components/   # Componenti della pagina
├─ styles/       # Stile grafico
├─ types/        # Interfacce
├─ package.json  # Script e dipendenze
└─ README.md
```

## Variabili ambiente
Creare un file `.env` nella root del frontend e configurare le variabili necessarie, ad esempio:

```env
NEXT_PUBLIC_RAG_API_URL=http://localhost:8000 per collegamento con backend