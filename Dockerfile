FROM python:3.11-slim

# Speed up build and prevent unnecessary installations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set default Ollama API URL (can be overridden in docker-compose)
ENV OLLAMA_API_URL=http://ollama:11434/api/generate

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

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://ollama:11434/api/health || exit 1

CMD ["python", "bot.py"] 