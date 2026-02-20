# 🎙️ Whisper App

A self-hosted voice transcription service with an optional summarization feature. Send audio via a web UI, REST API, or Telegram bot — everything runs locally on your own machine.

---

## Features

- 🎤 Transcribe audio files or live microphone recordings via a web UI
- 🤖 Telegram bot integration — send voice messages, get transcripts back
- 🌐 REST API for programmatic access
- 📝 Optional local summarization via Ollama (no external API keys needed)
- 🔒 Fully self-hosted — audio never leaves your server

---

## Project Structure

```
whisper-app/
├── docker-compose.yml
├── .env
├── .gitignore
├── api/
│   ├── Dockerfile
│   ├── main.py
│   └── static/
│       └── index.html
└── bot/
    ├── Dockerfile
    └── bot.py
```

---

## Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- [Colima](https://github.com/abiosoft/colima) (if on macOS without Docker Desktop)
- A Telegram bot token (optional — only needed for the Telegram bot)

---

## Setup

### 1. Clone or create the project

```bash
mkdir whisper-app && cd whisper-app
mkdir -p api/static bot
```

Copy all project files into the appropriate directories as described in the Project Structure above.

### 2. Configure environment variables

Copy the example below into a `.env` file in the project root:

```bash
# Required for Telegram bot — omit if you don't need it
TELEGRAM_TOKEN=your-telegram-token-here

# Whisper model to use for transcription
# Options: tiny, base, small, medium, large
# Larger = more accurate but slower and more memory
WHISPER_MODEL=base

# Optional — enable local summarization via Ollama
# Remove or leave empty to disable summarization entirely
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
```

> ⚠️ Never commit `.env` to version control. It's already listed in `.gitignore`.

### 3. Get a Telegram bot token (optional)

If you want to use the Telegram bot:

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token you receive and paste it as `TELEGRAM_TOKEN` in `.env`

---

## Deployment

### Without summarization (transcript only)

```bash
docker compose up --build
```

### With summarization (Ollama)

Pull the Ollama model once before starting (it gets cached locally):

```bash
docker compose up -d ollama
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3.2
docker compose up --build
```

### Run in the background

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop everything:

```bash
docker compose down
```

---

## Resource Requirements

### Whisper models

| Model | RAM needed | Speed | Accuracy |
|-------|-----------|-------|----------|
| `tiny` | ~1 GB | Very fast | Basic |
| `base` | ~1 GB | Fast | Good |
| `small` | ~2 GB | Moderate | Better |
| `medium` | ~5 GB | Slow | Great |
| `large` | ~10 GB | Very slow | Best |

### Ollama summarization models

| Model | Size | Notes |
|-------|------|-------|
| `llama3.2` | ~2 GB | Recommended — good balance |
| `llama3.2:1b` | ~1.3 GB | Faster, slightly less accurate |
| `mistral` | ~4 GB | High quality |
| `phi3` | ~2.3 GB | Fast and capable |

---

## macOS / Colima Notes

Docker on macOS runs inside a Linux VM. The VM has its own memory limit separate from your Mac's physical RAM. If you're running large models, increase the Colima VM resources:

```bash
colima stop
colima start --memory 12 --cpu 4
```

Models are cached on your Mac to avoid re-downloading on every run:

- Whisper models → `./cache/whisper`
- Ollama models → `~/.ollama`

These folders are mounted into the containers via the `volumes` section in `docker-compose.yml`.

---

## Usage

### Web UI

Open your browser at:

```
http://localhost:8000
```

You can either upload an audio file or record directly from your microphone. The transcript (and summary, if enabled) will appear on the page.

### REST API

**Transcribe an audio file:**

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@your_audio.mp3"
```

**Example response:**

```json
{
  "transcript": "Hey, just a reminder about the meeting tomorrow at 3pm.",
  "summary": "A reminder about a meeting scheduled for tomorrow at 3pm.",
  "language": "en",
  "duration": 4.2
}
```

When summarization is disabled, `summary` will be `null`.

**Health check:**

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "model": "base",
  "summarization": "disabled"
}
```

### Telegram Bot

1. Open Telegram and find your bot by its username
2. Send `/start` to confirm it's running
3. Send any voice message — you'll receive the transcript and (optionally) a summary in reply

---

## Configuration Reference

All configuration is done via environment variables in `.env`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_TOKEN` | No | — | Telegram bot token from @BotFather |
| `WHISPER_MODEL` | No | `base` | Whisper model size |
| `OLLAMA_URL` | No | — | Ollama API URL. If unset, summarization is disabled |
| `OLLAMA_MODEL` | No | `llama3.2` | Ollama model to use for summarization |

---

## Troubleshooting

**Container runs out of memory with large models**

Increase Colima (or Docker Desktop) memory as described in the macOS section above.

**`http://localhost:8000` is unreachable**

Check that the container is running and that uvicorn is binding to `0.0.0.0`:

```bash
docker compose ps
docker compose logs whisper-api
```

**Ollama summarization returns `null`**

Make sure `OLLAMA_URL` is set in `.env` and the model has been pulled:

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama list
```

If the model isn't listed, pull it:

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama3.2
```

**Telegram bot doesn't respond**

Verify the token is correct and the bot container is running:

```bash
docker compose logs telegram-bot
```

---

## License

MIT
