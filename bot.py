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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Wait for Ollama to be available (initial delay)
    time.sleep(5)
    
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries} to connect to Ollama")
            
            # Try to generate text using ollama
            try:
                response = requests.post(
                    "http://ollama:11434/api/generate",
                    json={"model": "mistral", "prompt": prompt},
                    timeout=60
                )
                
                if response.status_code == 200:
                    logger.info("Successfully received response from Ollama")
                    result = response.json()
                    return result.get("response", "No text generated")
                else:
                    logger.warning(f"Ollama API returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"Error connecting to Ollama: {str(e)}")
            
            # If we're here, the request failed
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
    
    # If we exhausted all retries
    return "⚠️ Failed to generate summary. Please check if Ollama is running with the mistral model."

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

logger.info("Starting the bot...")
threading.Thread(target=schedule_task, daemon=True).start()

updater.start_polling()
updater.idle() 