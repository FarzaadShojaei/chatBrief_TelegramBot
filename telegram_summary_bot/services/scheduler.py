"""
Scheduler service for running periodic tasks.
"""

import threading
import schedule
import time
import asyncio
import logging
from datetime import datetime, timedelta

from telegram_summary_bot.config import TEHRAN_TZ, GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.utils.storage import get_messages_in_range
from telegram_summary_bot.services.summarizer import summarize_messages


async def scheduled_summary(bot):
    """
    Generate and send a scheduled summary.
    
    Args:
        bot: The Telegram bot instance
    """
    now = datetime.now(TEHRAN_TZ)
    start = now - timedelta(hours=24)
    end = now
    messages = get_messages_in_range(start, end)
    
    if not any(messages.values()):
        logger.info("No messages to summarize in scheduled summary")
        return
    
    summary = summarize_messages(messages)
    
    # Format the summary with emojis and formatting
    formatted_summary = f"📊 Daily Summary:\n\n{summary}"
    
    # Try sending to both chat IDs to ensure delivery
    sent = False
    for chat_id in [GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID]:
        try:
            await bot.send_message(chat_id=chat_id, text=formatted_summary)
            logger.info(f"Successfully sent daily summary to chat {chat_id}")
            sent = True
        except Exception as e:
            logger.error(f"Failed to send daily summary to chat {chat_id}: {e}")
    
    if not sent:
        logger.error("Failed to send daily summary to any chat")


# Helper function to run the async scheduled_summary function
def run_scheduled_summary(bot):
    """Run the scheduled summary task."""
    asyncio.run(scheduled_summary(bot))


def setup_scheduler(bot):
    """
    Set up the scheduler to run tasks periodically.
    
    Args:
        bot: The Telegram bot instance
    """
    # Configure the scheduled task
    schedule.every().day.at("20:25").do(lambda: run_scheduled_summary(bot))  # UTC 20:25 = 23:55 Tehran time
    
    # Function to run the scheduler in a background thread
    def schedule_task():
        while True:
            schedule.run_pending()
            threading.Event().wait(30)
    
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=schedule_task, daemon=True)
    scheduler_thread.start()
    
    return scheduler_thread 