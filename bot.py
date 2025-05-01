# telegram-summary-bot/bot.py

import os
from telegram import Update, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from datetime import datetime, timedelta
import pytz
import logging
import threading
import schedule
import requests
import openai
from dotenv import load_dotenv
from collections import defaultdict

# Load secrets from secret.env
load_dotenv("secret.env")

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
TEHRAN_TZ = pytz.timezone("Asia/Tehran")
USE_OPENAI = bool(OPENAI_API_KEY)

# Group members: key = user_id, value = display name
import json

def load_group_members():
    try:
        with open("group_members.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

group_members = load_group_members()

# Initialize
if USE_OPENAI:
    openai.api_key = OPENAI_API_KEY

bot = Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(level=logging.INFO)

# Structure: {thread_id or None: list of messages}
thread_logs = defaultdict(list)
thread_titles = {}  # {thread_id: topic title}

# Handlers
def save_message(update: Update, context: CallbackContext):
    if update.effective_chat.id != GROUP_CHAT_ID:
        return

    user_id = update.effective_user.id
    display_name = update.effective_user.username or update.effective_user.first_name
    text = update.message.text
    timestamp = datetime.now(TEHRAN_TZ)
    thread_id = update.message.message_thread_id or 0  # 0 = main thread
    thread_title = update.message.is_topic_message and update.message.topic_name or "Main Group Thread"

    # Do not auto-register unknown users to preserve manual group_members list

    if thread_id not in thread_titles:
        thread_titles[thread_id] = thread_title

    thread_logs[thread_id].append({
        "time": timestamp,
        "user_id": user_id,
        "display_name": display_name,
        "text": text
    })

def get_messages_in_range(start, end):
    filtered_logs = defaultdict(list)
    for thread_id, messages in thread_logs.items():
        filtered = [msg for msg in messages if start <= msg["time"] <= end]
        if filtered:
            filtered_logs[thread_id] = filtered
    return filtered_logs

def summarize_messages(threaded_messages):
    if not threaded_messages:
        return "No messages in the selected timeframe."

    member_list = ", ".join(group_members.values())
    prompt_sections = []

    for thread_id, messages in threaded_messages.items():
        conversation = "\n".join([
            f"[{msg['time'].strftime('%H:%M')}] {msg['display_name']}: {msg['text']}"
            for msg in messages
        ])
        thread_title = thread_titles.get(thread_id, f"Thread {thread_id}")

        prompt_sections.append(
        f"[Topic: {thread_title}]\n"
        f"Messages\n:{conversation}"
    )  # fixed line break format  # fixed line break format

    full_prompt = (
        "These are categorized chat messages from a Telegram group.\n\n"
        "For each topic, list all group members by name. For each member:\n\n"
        "- If they spoke in that topic, summarize their message.\n"
        "- If they didn't speak, write: 'Did not participate.'\n\n"
        f"Group members: {member_list}\n\n"
        + "\n".join(prompt_sections)
    )
    
dp.add_handler(CommandHandler("summary", manual_summary))

threading.Thread(target=schedule_task, daemon=True).start()

updater.start_polling()
updater.idle()
