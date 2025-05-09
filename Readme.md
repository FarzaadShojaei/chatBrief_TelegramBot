# Telegram Summary Bot

A bot that automatically generates summaries of group chat conversations.

## Features

- Monitors group chat messages
- Provides on-demand summaries with `/summary` command
- Generates daily summaries automatically
- Handles threaded conversations
- Uses Ollama's Mistral AI model for intelligent summaries

## Project Structure

The bot has been modularized for better maintainability:

```
telegram_summary_bot/
  ├── __init__.py
  ├── bot_init.py      # Bot initialization
  ├── config.py        # Configuration settings
  ├── handlers/        # Message handlers
  │   ├── __init__.py
  │   └── message_handlers.py
  ├── services/        # Core services
  │   ├── __init__.py
  │   ├── ai_generator.py  # AI integration
  │   ├── scheduler.py     # Scheduled tasks
  │   └── summarizer.py    # Summary generation
  └── utils/           # Utility functions
      ├── __init__.py
      └── storage.py   # Message storage
```

## Setup

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up Ollama with the Mistral model:
   ```
   ollama pull mistral
   ```

3. Create a `secret.env` file with your Telegram bot token and chat IDs:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   GROUP_CHAT_ID=your_group_chat_id
   ACTUAL_GROUP_CHAT_ID=your_actual_group_chat_id
   ```
   
   Note: Make sure you get the correct group chat ID. You can find it by:
   - Adding the bot to your group
   - Sending a message in the group 
   - Checking the bot logs to see which chat ID is being used
   - Setting both GROUP_CHAT_ID and ACTUAL_GROUP_CHAT_ID to ensure the bot works correctly

4. Create a `group_members.json` file with the group members:
   ```json
   {
       "user_id_1": "Display Name 1",
       "user_id_2": "Display Name 2"
   }
   ```

5. Run the bot:
   ```
   python main.py
   ```

## Docker Support

To run the bot in Docker:

```
docker-compose up -d
```
