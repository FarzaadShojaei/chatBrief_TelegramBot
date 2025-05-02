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
import time
from dotenv import load_dotenv
from collections import defaultdict

# Load secrets from secret.env
load_dotenv("secret.env")

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
TEHRAN_TZ = pytz.timezone("Asia/Tehran")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama:11434/api/generate")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Using Ollama API URL: {OLLAMA_API_URL}")

# Group members: key = user_id, value = display name
import json

def load_group_members():
    try:
        with open("group_members.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

group_members = load_group_members()

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)

# Structure: {thread_id or None: list of messages}
thread_logs = defaultdict(list)
thread_titles = {}  # {thread_id: topic title}

# Updater
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dp = updater.dispatcher

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

def manual_summary(update: Update, context: CallbackContext):
    now = datetime.now(TEHRAN_TZ)
    start = now - timedelta(hours=24)
    end = now
    messages = get_messages_in_range(start, end)
    summary = summarize_messages(messages)
    update.message.reply_text(f"📊 Summary of the last 24 hours:\n\n{summary}")

def scheduled_summary():
    now = datetime.now(TEHRAN_TZ)
    start = now - timedelta(hours=24)
    end = now
    messages = get_messages_in_range(start, end)
    summary = summarize_messages(messages)
    bot.send_message(chat_id=GROUP_CHAT_ID, text=f"📊 Daily Summary:\n\n{summary}")

# Scheduled summary task
def schedule_task():
    schedule.every().day.at("20:25").do(scheduled_summary)  # UTC 20:25 = 23:55 Tehran time
    while True:
        schedule.run_pending()
        threading.Event().wait(30)

def get_messages_in_range(start, end):
    filtered_logs = defaultdict(list)
    for thread_id, messages in thread_logs.items():
        filtered = [msg for msg in messages if start <= msg["time"] <= end]
        if filtered:
            filtered_logs[thread_id] = filtered
    return filtered_logs

# Function to use Ollama for text generation
def generate_with_ollama(prompt):
    try:
        logger.info(f"Sending request to Ollama at {OLLAMA_API_URL}")
        response = requests.post(OLLAMA_API_URL, json={
            "model": "mistral",  # Using Mistral as default model
            "prompt": prompt,
            "stream": False
        })
        if response.status_code == 200:
            return response.json()["response"]
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return f"⚠️ Failed to generate summary. API returned status {response.status_code}"
    except Exception as e:
        logger.error(f"Error calling Ollama API: {str(e)}")
        return f"⚠️ Error generating summary: {str(e)}"

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
        )

    full_prompt = (
        "These are categorized chat messages from a Telegram group.\n\n"
        "For each topic, list all group members by name. For each member:\n\n"
        "- If they spoke in that topic, summarize their message.\n"
        "- If they didn't speak, write: 'Did not participate.'\n\n"
        f"Group members: {member_list}\n\n"
        + "\n".join(prompt_sections)
    )
    
    # Use Ollama directly
    logger.info("Generating summary using Ollama")
    return generate_with_ollama(full_prompt)

# Register handlers
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, save_message))
dp.add_handler(CommandHandler("summary", manual_summary))

threading.Thread(target=schedule_task, daemon=True).start()

updater.start_polling()
updater.idle() 