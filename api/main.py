import os
import tempfile
import asyncio
import logging
import httpx

import whisper
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
OLLAMA_URL = os.environ.get("OLLAMA_URL")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)
logger.info("Model ready.")

if OLLAMA_URL:
    logger.info(f"Summarization enabled via Ollama at {OLLAMA_URL} using {OLLAMA_MODEL}")
else:
    logger.info("Summarization disabled — OLLAMA_URL not set")


def summarize(transcript: str) -> str | None:
    if not OLLAMA_URL:
        return None
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": (
                    "Summarize the following voice message transcript in 2-3 sentences. "
                    "Be concise and capture the key points. "
                    "Reply with the summary only, no preamble.\n\n"
                    f"Transcript:\n{transcript}"
                ),
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return None


app = FastAPI(title="Whisper Transcription API")
app.mount("/static", StaticFiles(directory="static"), name="static")


class TranscriptionResult(BaseModel):
    transcript: str
    summary: str | None = None
    language: str
    duration: float


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/transcribe", response_model=TranscriptionResult)
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "audio.ogg")[1] or ".ogg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        contents = await file.read()
        tmp.write(contents)

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: model.transcribe(tmp_path)
        )
        transcript = result["text"].strip()

        summary = await loop.run_in_executor(None, lambda: summarize(transcript))

        return TranscriptionResult(
            transcript=transcript,
            summary=summary,
            language=result.get("language", "unknown"),
            duration=result.get("segments", [{}])[-1].get("end", 0.0),
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": WHISPER_MODEL,
        "summarization": OLLAMA_MODEL if OLLAMA_URL else "disabled",
    }