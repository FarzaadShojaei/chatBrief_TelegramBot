FROM python:3.11-slim

# Speed up build and prevent unnecessary installations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies explicitly
RUN pip install --no-cache-dir python-telegram-bot==13.15 \
    schedule==1.2.0 \
    pytz==2023.3 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# Copy application files
COPY bot.py .
COPY group_members.json .
COPY secret.env .

# Create wait-for-ollama script
RUN echo '#!/bin/sh \n\
echo "Waiting for Ollama to be available..." \n\
while ! curl -s http://ollama:11434/api/completions; do \n\
  echo "Ollama not available yet - waiting..." \n\
  sleep 5 \n\
done \n\
echo "Ollama is available, pulling mistral model..." \n\
curl -X POST http://ollama:11434/api/pull -d "{\\"name\\":\\"mistral\\"}" \n\
echo "Starting bot..." \n\
exec python bot.py' > /app/wait-for-ollama.sh && chmod +x /app/wait-for-ollama.sh

ENTRYPOINT ["/app/wait-for-ollama.sh"] 