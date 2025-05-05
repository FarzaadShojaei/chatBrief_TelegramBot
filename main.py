#!/usr/bin/env python
"""
Main entry point for the Telegram Summary Bot.
"""

import asyncio
import atexit
import logging
from telegram import Update

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.bot_init import create_bot, create_application, application_startup
from telegram_summary_bot.services.scheduler import setup_scheduler
from telegram_summary_bot.utils.storage import save_message_history


def main():
    """Main function to start the bot."""
    logger.info("Starting the Telegram Summary Bot...")
    
    # Create bot instance
    bot = create_bot()
    
    # Create the application
    application = create_application()
    
    # Register the startup handler
    application.post_init = application_startup
    
    # Register shutdown handler to save messages
    atexit.register(save_message_history)
    
    # Setup the scheduler
    setup_scheduler(bot)
    
    # Run the bot
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == "__main__":
    main() 