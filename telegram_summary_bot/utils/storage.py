"""
Storage utilities for saving and loading message history.
"""

import json
import logging
from datetime import datetime
from telegram_summary_bot.config import GROUP_MEMBERS_FILE
from telegram_summary_bot.utils.database import (
    add_message as db_add_message,
    get_messages_in_range as db_get_messages_in_range,
    get_thread_titles as db_get_thread_titles,
    init_db,
    migrate_from_json
)

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

# Thread titles global variable for backward compatibility
thread_titles = {}

# Group members cache
group_members = {}


def load_group_members():
    """Load group members from the JSON file."""
    global group_members
    try:
        with open(GROUP_MEMBERS_FILE, "r", encoding="utf-8") as f:
            group_members = json.load(f)
            logger.info(f"Loaded {len(group_members)} group members")
            return group_members
    except FileNotFoundError:
        logger.warning(f"Group members file not found: {GROUP_MEMBERS_FILE}")
        return {}


def load_message_history():
    """Initialize the database and load thread titles."""
    global thread_titles
    try:
        # Initialize database tables
        init_db()
        
        # Get thread titles from database
        thread_titles = db_get_thread_titles()
        logger.info(f"Loaded {len(thread_titles)} thread titles from database")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def save_message_history():
    """No-op function for backward compatibility."""
    # This function does nothing now as messages are saved immediately in the database
    logger.info("Message history is automatically saved to database")


def get_messages_in_range(start, end):
    """Get messages within a specified time range from database."""
    return db_get_messages_in_range(start, end)


def add_message(thread_id, user_id, display_name, text, timestamp, thread_title="Main Group Chat"):
    """Add a message to the database."""
    # Update thread titles (for backward compatibility)
    global thread_titles
    if thread_id not in thread_titles:
        thread_titles[thread_id] = thread_title
    
    # Add message to database
    db_add_message(
        telegram_user_id=user_id,
        display_name=display_name,
        thread_telegram_id=thread_id,
        thread_title=thread_title,
        text=text,
        timestamp=timestamp
    )
    
    # Return a dummy count for backward compatibility
    return 1


# Initialize by loading data
load_group_members()
load_message_history() 