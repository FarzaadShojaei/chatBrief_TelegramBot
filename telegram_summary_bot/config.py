"""
Configuration module for the Telegram Summary Bot.
"""

import os
import logging
import pytz
from dotenv import load_dotenv

# Load secrets from secret.env
load_dotenv("secret.env")

# Basic configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
ACTUAL_GROUP_CHAT_ID = int(os.getenv("ACTUAL_GROUP_CHAT_ID", "-1002635826698"))  # From logs
TEHRAN_TZ = pytz.timezone("Asia/Tehran")
MESSAGES_FILE = "message_history.json"
GROUP_MEMBERS_FILE = "group_members.json"

# Set up logs directory
LOGS_DIR = os.environ.get("LOGS_DIR", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "telegram_bot.log")

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler(LOG_FILE)
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)

# Create formatters
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Function to check if a chat is monitored
def is_monitored_chat(chat_id):
    """Check if a chat is monitored by the bot."""
    return chat_id == GROUP_CHAT_ID or chat_id == ACTUAL_GROUP_CHAT_ID 