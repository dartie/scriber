FROM python:3.11-slim

WORKDIR /app
RUN pip install python-telegram-bot httpx

COPY bot.py .

CMD ["python", "bot.py"]

