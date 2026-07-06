# Oído — Latin American Spanish Listening Trainer

Audio-first listening fluency training through three progressive stages:

| Stage | Module | What it trains |
|-------|--------|----------------|
| 1 | **Vocabulario** | Recognize high-frequency words in isolation |
| 2 | **Estructura** | Decode natural utterances — clitics, idioms, ellipsis |
| 3 | **Velocidad** | Follow extended speech at native conversational speed |

## Setup

### 1. Install dependencies

```bash
cd /path/to/spanish-listening-app
npm install
```

### 2. Add your Anthropic API key

```bash
cp .env.example .env
```

Open `.env` and paste your key (get one at https://console.anthropic.com):

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start the app

```bash
npm run dev
```

This launches two servers in parallel:

| Server | URL | What it does |
|--------|-----|--------------|
| Express proxy | http://localhost:3457 | Forwards `/api/claude` → Anthropic, adds API key |
| Static file server | http://localhost:3456 | Serves `index.html` and `wordlist.csv` |

### 4. Open the app

Navigate to **http://localhost:3456** in your browser.

## Requirements

- Node.js 18+ and npm
- A modern browser with Web Speech API support (Chrome or Safari recommended for best voice coverage)
- An Anthropic API key with access to `claude-sonnet-4-6`

## Architecture

```
Browser (port 3456)
  └─► POST http://localhost:3457/api/claude
        └─► server.js (Express — injects API key from .env)
              └─► https://api.anthropic.com/v1/messages
```

All session data and settings are stored in browser `localStorage` — nothing
is sent to any server other than Anthropic.
