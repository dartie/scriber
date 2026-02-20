FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install fastapi uvicorn python-multipart openai-whisper

COPY main.py .
COPY static/ static/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

