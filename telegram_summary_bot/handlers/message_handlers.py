"""
Message handlers for the Telegram bot.
"""

import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import CallbackContext

from telegram_summary_bot.config import is_monitored_chat, TEHRAN_TZ, GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.utils.storage import add_message, get_messages_in_range, group_members
from telegram_summary_bot.services.summarizer import summarize_messages


async def save_message(update: Update, context: CallbackContext):
    """
    Handler for saving messages.
    
    Args:
        update: The Telegram update
        context: The callback context
    """
    # Log all incoming messages for debugging
    logger.info(f"Received message in chat {update.effective_chat.id}")
    logger.info(f"From user: {update.effective_user.id} - {update.effective_user.username or update.effective_user.first_name}")
    logger.info(f"Message text: {update.message.text}")
    
    # Check if the message is from the configured group
    if not is_monitored_chat(update.effective_chat.id):
        logger.warning(f"Ignoring message from chat {update.effective_chat.id} - not the target group")
        return

    user_id = update.effective_user.id
    display_name = update.effective_user.username or update.effective_user.first_name
    text = update.message.text
    timestamp = datetime.now(TEHRAN_TZ)
    
    # For non-topic groups or main thread, use thread_id 0
    thread_id = getattr(update.message, 'message_thread_id', None) or 0
    
    # For non-topic groups, use a default title
    if hasattr(update.message, 'is_topic_message') and update.message.is_topic_message:
        thread_title = update.message.topic_name
    else:
        thread_title = "Main Group Chat"

    # Check if this user is known in our group_members list
    user_id_str = str(user_id)
    if user_id_str not in group_members:
        logger.info(f"User {user_id} ({display_name}) not in group_members.json")

    # Save the message
    logger.info(f"Saving message from {display_name} in thread {thread_id}: {text[:30]}...")
    
    # Add message to storage
    total_messages = add_message(
        thread_id=thread_id,
        user_id=user_id,
        display_name=display_name,
        text=text,
        timestamp=timestamp,
        thread_title=thread_title
    )
    
    logger.info(f"Message saved. Total messages in logs: {total_messages}")


async def manual_summary(update: Update, context: CallbackContext):
    """
    Handler for generating a summary on demand.
    
    Args:
        update: The Telegram update
        context: The callback context
    """
    logger.info(f"Summary requested by user {update.effective_user.id} in chat {update.effective_chat.id}")
    
    # Log current state of message storage for debugging
    logger.info("Getting messages from the last 24 hours")
    
    now = datetime.now(TEHRAN_TZ)
    start = now - timedelta(hours=24)
    end = now
    
    logger.info(f"Getting messages from {start} to {end}")
    messages = get_messages_in_range(start, end)
    
    logger.info(f"Found {sum(len(msgs) for msgs in messages.values())} messages in time range")
    
    if not any(messages.values()):
        await update.message.reply_text("No messages found in the last 24 hours.")
        return
        
    summary = summarize_messages(messages)
    formatted_summary = f"📊 Summary of the last 24 hours:\n\n{summary}"
    
    # Reply to the message that requested the summary
    await update.message.reply_text(formatted_summary)
    
    # If the request came from a different chat than the monitored ones,
    # also send the summary to the monitored chats as a courtesy
    request_chat_id = update.effective_chat.id
    if request_chat_id != GROUP_CHAT_ID and request_chat_id != ACTUAL_GROUP_CHAT_ID:
        logger.info(f"Summary requested from non-monitored chat {request_chat_id}, also sending to monitored chats")
        
        for chat_id in [GROUP_CHAT_ID, ACTUAL_GROUP_CHAT_ID]:
            if chat_id != request_chat_id:  # Don't send twice to the same chat
                try:
                    await context.bot.send_message(chat_id=chat_id, text=formatted_summary)
                    logger.info(f"Summary also sent to chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send summary to chat {chat_id}: {e}")


async def process_all_messages(update: Update, context: CallbackContext):
    """
    General handler for all incoming messages.
    
    Acts as a catch-all to ensure we don't miss any messages.
    
    Args:
        update: The Telegram update
        context: The callback context
    """
    if not update.effective_message:
        return
        
    # Check if the message is from our target group
    if not is_monitored_chat(update.effective_chat.id):
        return
        
    # Handle edited messages
    if update.edited_message:
        logger.info(f"Received edited message in group from {update.effective_user.username or update.effective_user.first_name}")
        # We don't process edited messages for now
        return
        
    # For non-text messages that we don't want to save, just log them
    if not update.effective_message.text:
        logger.info(f"Received non-text message in group from {update.effective_user.username or update.effective_user.first_name}")
        return
        
    # We've received a text message from the target group, call our regular handler
    logger.info(f"process_all_messages caught a message: {update.effective_message.text[:30]}...")
    
    # Forward to our main handler
    await save_message(update, context)


async def handle_error(update: Update, context: CallbackContext):
    """
    Error handler for the bot.
    
    Args:
        update: The Telegram update
        context: The callback context
    """
    logger.error(f"Update {update} caused error: {context.error}")
    # You can add error reporting here, like sending a message to an admin 