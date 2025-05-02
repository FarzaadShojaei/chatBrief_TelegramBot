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

# Create a simple shell script
RUN echo '#!/bin/bash \n\
echo "Waiting for Ollama to start..." \n\
sleep 10 \n\
echo "Starting bot..." \n\
python bot.py' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 