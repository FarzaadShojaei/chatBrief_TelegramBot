FROM python:3.11-slim

# Speed up build and prevent unnecessary installations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy application files
COPY main.py .
COPY telegram_summary_bot/ ./telegram_summary_bot/
COPY group_members.json .
COPY secret.env .

# Create a simple shell script to wait for Ollama before starting
RUN echo '#!/bin/bash \n\
echo "Waiting for Ollama to start..." \n\
sleep 10 \n\
echo "Starting bot..." \n\
python main.py' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 