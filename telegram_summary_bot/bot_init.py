"""
Telegram bot initialization module.
"""

import logging
from telegram import Bot, Update
from telegram.ext import (
    Application, MessageHandler, filters, 
    CommandHandler, CallbackContext
)

from telegram_summary_bot.config import TELEGRAM_TOKEN, GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.handlers.message_handlers import (
    save_message, manual_summary, process_all_messages, handle_error
)


def create_bot():
    """Create a Telegram bot instance."""
    return Bot(token=TELEGRAM_TOKEN)


def create_application():
    """Create and configure the Telegram application."""
    # Initialize the application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register handlers
    # Explicitly handle all message types that might have text content
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))
    
    # Add a command handler for the summary
    application.add_handler(CommandHandler("summary", manual_summary))
    
    # Add a catch-all handler with lower priority to make sure we don't miss any messages
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_all_messages), group=1)
    
    # Add error handler
    application.add_error_handler(handle_error)
    
    return application


async def check_group_access(bot):
    """
    Verify that the bot has access to the configured groups.
    
    Args:
        bot: The Telegram bot instance
        
    Returns:
        bool: True if at least one group could be accessed, False otherwise
    """
    try:
        # Try both group chat IDs
        success = False
        for chat_id in [GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID]:
            try:
                logger.info(f"Verifying access to group chat {chat_id}...")
                chat = await bot.get_chat(chat_id)
                logger.info(f"Successfully accessed group: {chat.title}")
                success = True
                
                # Try to send a test message, but catch any errors
                try:
                    test_msg = await bot.send_message(
                        chat_id=chat_id, 
                        text="📝 Bot started and is now monitoring messages for daily summaries.\nUse /summary to get a summary of the last 24 hours."
                    )
                    logger.info(f"Test message sent successfully: {test_msg.message_id}")
                except Exception as e:
                    logger.error(f"Failed to send message to group chat {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Failed to access group chat {chat_id}: {e}")
                
        return success
    except Exception as e:
        logger.error(f"Failed to access group chats: {e}")
        logger.error("Please make sure the bot is added to the group and has appropriate permissions")
        return False


async def application_startup(app):
    """
    Function called at application startup.
    
    Args:
        app: The Telegram application
    """
    logger.info("Application startup handler called")
    
    # Check group access
    success = await check_group_access(app.bot)
    if not success:
        logger.error("Failed to verify group access at startup - messages may not be captured correctly")
    
    return 