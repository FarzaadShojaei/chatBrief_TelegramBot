"""
Storage utilities for saving and loading message history.
"""

import json
import logging
from datetime import datetime
from collections import defaultdict
from telegram_summary_bot.config import MESSAGES_FILE, GROUP_MEMBERS_FILE

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

# Thread logs and titles
thread_logs = defaultdict(list)
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
    """Load saved messages if file exists."""
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Convert defaultdict and datetime objects
            for thread_id, messages in data["thread_logs"].items():
                for msg in messages:
                    # Convert string timestamp back to datetime
                    msg["time"] = datetime.fromisoformat(msg["time"])
                thread_logs[int(thread_id)] = messages
                
            for thread_id, title in data["thread_titles"].items():
                thread_titles[int(thread_id)] = title
                
            logger.info(f"Loaded {sum(len(msgs) for msgs in thread_logs.values())} messages from history")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.info(f"No valid message history found: {e}")


def save_message_history():
    """Save messages to file."""
    try:
        # Need to convert datetime objects to strings for JSON serialization
        serializable_logs = {}
        for thread_id, messages in thread_logs.items():
            serializable_logs[thread_id] = [
                {**msg, "time": msg["time"].isoformat()} 
                for msg in messages
            ]
            
        data = {
            "thread_logs": serializable_logs,
            "thread_titles": thread_titles
        }
        
        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {sum(len(msgs) for msgs in thread_logs.values())} messages to history")
    except Exception as e:
        logger.error(f"Failed to save message history: {e}")


def get_messages_in_range(start, end):
    """Get messages within a specified time range."""
    filtered_logs = defaultdict(list)
    for thread_id, messages in thread_logs.items():
        filtered = [msg for msg in messages if start <= msg["time"] <= end]
        if filtered:
            filtered_logs[thread_id] = filtered
    return filtered_logs


def add_message(thread_id, user_id, display_name, text, timestamp, thread_title="Main Group Chat"):
    """Add a message to the log."""
    if thread_id not in thread_titles:
        thread_titles[thread_id] = thread_title

    thread_logs[thread_id].append({
        "time": timestamp,
        "user_id": user_id,
        "display_name": display_name,
        "text": text
    })
    
    # Save messages to file after each new message
    save_message_history()
    
    return sum(len(msgs) for msgs in thread_logs.values())


# Initialize by loading data
load_group_members()
load_message_history() 