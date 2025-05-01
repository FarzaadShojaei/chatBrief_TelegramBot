from telegram.ext import Updater, MessageHandler, Filters
from dotenv import load_dotenv
import os

load_dotenv("secret.env")  # لود کردن توکن از فایل محیطی

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def print_chat_id(update, context):
    print(f"Chat ID: {update.effective_chat.id}")
    print(f"User: {update.effective_user.first_name} - Message: {update.message.text}")

updater = Updater(TELEGRAM_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(MessageHandler(Filters.all, print_chat_id))

print("Listening for messages... (Send a message in your group)")
updater.start_polling()
updater.idle()
