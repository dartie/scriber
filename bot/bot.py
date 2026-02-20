import os
import logging
import tempfile
import httpx

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WHISPER_API_URL = os.environ.get("WHISPER_API_URL", "http://whisper-api:8000/transcribe")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a voice message and I'll transcribe it for you!"
    )


async def transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    voice = message.voice or message.audio

    if not voice:
        return

    await message.reply_text("⏳ Transcribing...")

    suffix = ".ogg" if message.voice else ".mp3"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(tmp_path)

        async with httpx.AsyncClient(timeout=120) as client:
            with open(tmp_path, "rb") as f:
                response = await client.post(
                    WHISPER_API_URL,
                    files={"file": (os.path.basename(tmp_path), f, "audio/ogg")},
                )
            response.raise_for_status()
            data = response.json()

        transcript = data.get("transcript", "").strip()
        language = data.get("language", "unknown")
        duration = data.get("duration", 0)

        if transcript:
            await message.reply_text(
                f"📝 *Transcript* (_{language}_, {duration:.1f}s):\n\n{transcript}",
                parse_mode="Markdown",
            )
        else:
            await message.reply_text("⚠️ Couldn't detect any speech in the audio.")

    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.text}")
        await message.reply_text(f"❌ API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text(f"❌ Something went wrong: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, transcribe_voice))
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

