#!/usr/bin/env python
"""
Main entry point for the Telegram Summary Bot.
"""

import asyncio
import atexit
import json
import logging
import os
from telegram import Update

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.bot_init import create_bot, create_application, application_startup
from telegram_summary_bot.services.scheduler import setup_scheduler
from telegram_summary_bot.utils.storage import save_message_history
from telegram_summary_bot.utils.database import migrate_from_json


def migrate_existing_data():
    """Migrate existing JSON data to PostgreSQL if it exists."""
    json_file = "message_history.json"
    if os.path.exists(json_file):
        try:
            logger.info(f"Found existing message history file: {json_file}")
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Migrate data to database
            migrate_from_json(data)
            
            # Backup the JSON file
            backup_file = f"{json_file}.bak"
            os.rename(json_file, backup_file)
            logger.info(f"Data migration complete. Original file backed up as {backup_file}")
        except Exception as e:
            logger.error(f"Error migrating existing data: {e}")
    else:
        logger.info("No existing message history file found. Starting with empty database.")


def main():
    """Main function to start the bot."""
    logger.info("Starting the Telegram Summary Bot...")
    
    # Migrate existing data
    migrate_existing_data()
    
    # Create bot instance
    bot = create_bot()
    
    # Create the application
    application = create_application()
    
    # Register the startup handler
    application.post_init = application_startup
    
    # Register shutdown handler to save messages (kept for compatibility)
    atexit.register(save_message_history)
    
    # Setup the scheduler
    setup_scheduler(bot)
    
    # Run the bot
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == "__main__":
    main() 