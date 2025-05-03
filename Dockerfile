FROM python:3.11-slim

# Speed up build and prevent unnecessary installations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bot.py .
COPY get_chat_id.py .
COPY group_members.json .
COPY secret.env .

# Create healthcheck script
RUN echo '#!/bin/bash\n\
curl -s http://ollama:11434/api/tags | grep -q "mistral" || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for Ollama and mistral model to be ready..."\n\
until /app/healthcheck.sh; do\n\
    echo "Waiting for mistral model to be available..."\n\
    sleep 5\n\
done\n\
echo "Starting bot..."\n\
exec python bot.py' > /app/start.sh && \
    chmod +x /app/start.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

CMD ["/app/start.sh"] 