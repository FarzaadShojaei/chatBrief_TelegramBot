from telegram import Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from dotenv import load_dotenv
import os
import logging
import sys

class Config:
    def __init__(self):
        load_dotenv("secret.env")
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if not self.TELEGRAM_TOKEN:
            print("❌ Error: TELEGRAM_TOKEN not found in secret.env")
            sys.exit(1)

class ChatIdBot:
    def __init__(self):
        self.config = Config()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize bot and updater
        self.updater = Updater(self.config.TELEGRAM_TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        
        # Register handlers
        self.register_handlers()

    def register_handlers(self):
        self.dp.add_handler(CommandHandler("start", self.start_command))
        self.dp.add_handler(MessageHandler(Filters.all, self.print_chat_id))

    def start_command(self, update: Update, context: CallbackContext):
        help_text = """
🔍 *Chat ID Helper Bot*

This bot helps you find chat IDs needed for the Summary Bot setup.

*Instructions:*
1. Add this bot to your group
2. Send any message in the group
3. The bot will show the chat ID
4. Use this ID in your `secret.env` file

*Available Commands:*
/start - Show this help message
        """
        update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    def print_chat_id(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        user_name = update.effective_user.first_name
        
        info_text = f"""
📱 *Chat Information:*
• Chat ID: `{chat_id}`
• Chat Type: {chat_type}
• Message from: {user_name}

✏️ *Setup Instructions:*
1. Copy this chat ID: `{chat_id}`
2. Add it to your `secret.env` file as:
   ```
   GROUP_CHAT_ID={chat_id}
   ```
        """
        update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        self.logger.info("Starting Chat ID Bot...")
        print("\n🤖 Bot is running... Send a message in your group to get the chat ID")
        print("Press Ctrl+C to stop\n")
        self.updater.start_polling()
        self.updater.idle()

if __name__ == "__main__":
    bot = ChatIdBot()
    bot.run()
