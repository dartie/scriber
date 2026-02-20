import os
import tempfile
import asyncio
import logging

import whisper
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)
logger.info("Model ready.")

app = FastAPI(title="Whisper Transcription API")
app.mount("/static", StaticFiles(directory="static"), name="static")


class TranscriptionResult(BaseModel):
    transcript: str
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
        return TranscriptionResult(
            transcript=result["text"].strip(),
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
    return {"status": "ok", "model": WHISPER_MODEL}

