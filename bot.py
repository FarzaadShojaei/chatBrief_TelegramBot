# telegram-summary-bot/bot.py

import os
from telegram import Update, Bot, ParseMode
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
import json
import subprocess

class Config:
    def __init__(self):
        load_dotenv("secret.env")
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
        self.TEHRAN_TZ = pytz.timezone("Asia/Tehran")
        self.OLLAMA_URL = "http://ollama:11434/api/generate"
        self.OLLAMA_MODEL = "mistral"
        self.SUMMARY_TIME_UTC = "23:25"  # 23:55 Tehran time
        self.DOCKER_COMPOSE_FILE = "docker-compose.yml"

class MessageStore:
    def __init__(self):
        self.thread_logs = defaultdict(list)
        self.thread_titles = {}
        self.group_members = self.load_group_members()

    @staticmethod
    def load_group_members():
        try:
            with open("group_members.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_message(self, timestamp, user_id, display_name, text, thread_id, thread_title):
        if thread_id not in self.thread_titles:
            self.thread_titles[thread_id] = thread_title

        self.thread_logs[thread_id].append({
            "time": timestamp,
            "user_id": user_id,
            "display_name": display_name,
            "text": text
        })

    def get_messages_in_range(self, start, end):
        filtered_logs = defaultdict(list)
        for thread_id, messages in self.thread_logs.items():
            filtered = [msg for msg in messages if start <= msg["time"] <= end]
            if filtered:
                filtered_logs[thread_id] = filtered
        return filtered_logs

class OllamaClient:
    def __init__(self, url, model):
        self.url = url
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.max_retries = 5
        self.initial_delay = 2

    def generate(self, prompt):
        time.sleep(5)  # Initial delay
        retry_delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Attempt {attempt+1}/{self.max_retries} to connect to Ollama")
                response = requests.post(
                    self.url,
                    json={"model": self.model, "prompt": prompt},
                    timeout=60
                )

                if response.status_code == 200:
                    self.logger.info("Successfully received response from Ollama")
                    result = response.json()
                    return result.get("response", "No text generated")
                else:
                    self.logger.warning(f"Ollama API returned status {response.status_code}")

            except Exception as e:
                self.logger.error(f"Error connecting to Ollama: {str(e)}")

            if attempt < self.max_retries - 1:
                self.logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        return "⚠️ Failed to generate summary. Please check if Ollama is running with the mistral model."

class SummaryBot:
    def __init__(self):
        self.config = Config()
        self.message_store = MessageStore()
        self.ollama_client = OllamaClient(
            self.config.OLLAMA_URL,
            self.config.OLLAMA_MODEL
        )
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize bot and updater
        self.bot = Bot(token=self.config.TELEGRAM_TOKEN)
        self.updater = Updater(token=self.config.TELEGRAM_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        
        # Register handlers
        self.register_handlers()

    def register_handlers(self):
        self.dp.add_handler(CommandHandler("start", self.start_command))
        self.dp.add_handler(CommandHandler("summary", self.manual_summary))
        self.dp.add_handler(CommandHandler("stop", self.stop_command))
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.save_message))

    def start_command(self, update: Update, context: CallbackContext):
        help_text = """
🤖 *Welcome to Chat Summary Bot!*

*Available Commands:*
/start - Show this help message
/summary - Generate a summary of last 24h chats
/stop - Stop the bot

*Summary Limitations:*
• Summarizes last 24 hours of chat
• Maximum 5 retries for Ollama connection
• Timeout of 60 seconds per request
• Auto-summary at 23:55 Tehran time
• Uses Mistral model for summarization

*Auto Summary:*
The bot automatically generates summaries:
• Every day at 23:55 Tehran time
• Includes all topics/threads
• Groups messages by user

*Group Members:*
Currently tracking messages for:
{}
        """
        member_list = "\n".join([f"• {name}" for name in self.message_store.group_members.values()])
        
        try:
            # Start docker containers
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            update.message.reply_text(
                help_text.format(member_list),
                parse_mode=ParseMode.MARKDOWN
            )
        except subprocess.CalledProcessError as e:
            update.message.reply_text(
                "❌ Error starting the bot containers. Please check the logs.",
                parse_mode=ParseMode.MARKDOWN
            )

    def stop_command(self, update: Update, context: CallbackContext):
        try:
            # Stop docker containers
            subprocess.run(["docker-compose", "down"], check=True)
            update.message.reply_text(
                "🛑 Bot has been stopped. Use /start to start it again.",
                parse_mode=ParseMode.MARKDOWN
            )
        except subprocess.CalledProcessError as e:
            update.message.reply_text(
                "❌ Error stopping the bot containers. Please check the logs.",
                parse_mode=ParseMode.MARKDOWN
            )

    def save_message(self, update: Update, context: CallbackContext):
        if update.effective_chat.id != self.config.GROUP_CHAT_ID:
            return

        self.message_store.save_message(
            timestamp=datetime.now(self.config.TEHRAN_TZ),
            user_id=update.effective_user.id,
            display_name=update.effective_user.username or update.effective_user.first_name,
            text=update.message.text,
            thread_id=update.message.message_thread_id or 0,
            thread_title=update.message.is_topic_message and update.message.topic_name or "Main Group Thread"
        )

    def manual_summary(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            "🔄 Generating summary... This may take up to 60 seconds.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        now = datetime.now(self.config.TEHRAN_TZ)
        start = now - timedelta(hours=24)
        summary = self.generate_summary(start, now)
        
        update.message.reply_text(
            f"📊 *Summary of the last 24 hours:*\n\n{summary}",
            parse_mode=ParseMode.MARKDOWN
        )

    def scheduled_summary(self):
        now = datetime.now(self.config.TEHRAN_TZ)
        start = now - timedelta(hours=24)
        summary = self.generate_summary(start, now)
        self.bot.send_message(
            chat_id=self.config.GROUP_CHAT_ID,
            text=f"📊 *Daily Summary:*\n\n{summary}",
            parse_mode=ParseMode.MARKDOWN
        )

    def generate_summary(self, start, end):
        messages = self.message_store.get_messages_in_range(start, end)
        if not messages:
            return "No messages in the selected timeframe."

        member_list = ", ".join(self.message_store.group_members.values())
        prompt_sections = []

        for thread_id, thread_messages in messages.items():
            conversation = "\n".join([
                f"[{msg['time'].strftime('%H:%M')}] {msg['display_name']}: {msg['text']}"
                for msg in thread_messages
            ])
            thread_title = self.message_store.thread_titles.get(thread_id, f"Thread {thread_id}")

            prompt_sections.append(
                f"[Topic: {thread_title}]\n"
                f"Messages:\n{conversation}"
            )

        full_prompt = (
            "These are categorized chat messages from a Telegram group.\n\n"
            "For each topic, list all group members by name. For each member:\n\n"
            "- If they spoke in that topic, summarize their message.\n"
            "- If they didn't speak, write: 'Did not participate.'\n\n"
            f"Group members: {member_list}\n\n"
            + "\n".join(prompt_sections)
        )

        self.logger.info("Generating summary using Ollama")
        return self.ollama_client.generate(full_prompt)

    def schedule_task(self):
        schedule.every().day.at(self.config.SUMMARY_TIME_UTC).do(self.scheduled_summary)
        while True:
            schedule.run_pending()
            threading.Event().wait(30)

    def run(self):
        self.logger.info("Starting the bot...")
        threading.Thread(target=self.schedule_task, daemon=True).start()
        self.updater.start_polling()
        self.updater.idle()

if __name__ == "__main__":
    bot = SummaryBot()
    bot.run() 