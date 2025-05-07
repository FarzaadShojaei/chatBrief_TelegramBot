FROM python:3.11-slim

# Speed up build and prevent unnecessary installations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for SQLite
RUN mkdir -p /app/data

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY telegram_summary_bot/ ./telegram_summary_bot/
COPY group_members.json .
COPY secret.env .

# Create a startup script that waits for Ollama before starting the bot
RUN echo '#!/bin/bash \n\
echo "Waiting for Ollama to start..." \n\
max_attempts=30 \n\
counter=0 \n\
until curl -s http://ollama:11434/api/tags > /dev/null || [ $counter -eq $max_attempts ]; do \n\
    echo "Attempt $counter/$max_attempts: Ollama is not available yet..." \n\
    counter=$((counter+1)) \n\
    sleep 2 \n\
done \n\
if [ $counter -eq $max_attempts ]; then \n\
    echo "Warning: Ollama may not be fully ready, but continuing..." \n\
fi \n\
echo "Starting bot..." \n\
python -O main.py' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 