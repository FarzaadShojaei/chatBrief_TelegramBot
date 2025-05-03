# Telegram Daily Summary Bot

This bot summarizes group chats by topic and person:
- Sends a summary every day at 23:55 Tehran time
- Responds to commands for managing the bot
- Works with Mistral model via Ollama

## Commands
- `/start` - Start the bot (equivalent to `docker-compose up -d`)
- `/summary` - Generate a summary of last 24h chats
- `/stop` - Stop the bot (equivalent to `docker-compose down`)

## Summary Features
- Summarizes last 24 hours of chat
- Groups messages by topic and user
- Shows participation status for all group members
- Auto-summary daily at 23:55 Tehran time

## Limitations
- Maximum 5 retries for Ollama connection
- 60-second timeout per summary request
- Requires Docker and Docker Compose
- Only summarizes text messages

## Structure
- `Config`: Manages environment variables and configuration
- `MessageStore`: Handles message storage and retrieval
- `OllamaClient`: Manages Ollama API interactions
- `SummaryBot`: Main bot class orchestrating all operations

## Setup
1. Copy `secret.env.example` to `secret.env` and fill in your values
2. Update `group_members.json` with your group members
3. Use bot commands:
   - `/start` to start the bot
   - `/summary` to get chat summary
   - `/stop` to stop the bot

## Running without Docker
If running locally without Docker:
1. Make sure Python 3.11 is installed
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python bot.py`
