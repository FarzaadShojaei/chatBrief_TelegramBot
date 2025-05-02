# Running the Telegram Bot on Your Server

## Prerequisites
- Docker and Docker Compose installed on your server
- Access to the internet (ability to connect to Telegram API)
- Your server's own IP address and port

## Setup Steps

1. **Copy the Bot Files to Your Server**
   ```bash
   scp -r * user@your-server-ip:~/telegram-bot/
   ```

2. **Create an Environment File**
   Create a `.env` file on your server with:
   ```
   TELEGRAM_TOKEN=your_telegram_token
   OPENAI_API_KEY=your_openai_key
   GROUP_CHAT_ID=your_group_chat_id
   ```

3. **Fix Python-Telegram-Bot Version Issue**
   If you get an error about `Filters`, run:
   ```bash
   pip install python-telegram-bot==13.15
   ```

4. **Run with Docker**
   ```bash
   cd ~/telegram-bot
   docker-compose up -d
   ```

5. **Check Logs**
   ```bash
   docker logs telegram_summary_bot -f
   ```

## Troubleshooting

- **Network Issues**: Ensure your server can connect to `api.telegram.org`
- **Permission Issues**: Make sure group_members.json has read permissions
- **API Key Issues**: Verify your OpenAI API key is valid and has sufficient quota

## Running Without Docker
If you prefer not to use Docker:

```bash
cd ~/telegram-bot
pip install -r requirements.txt
python bot.py
```

To keep it running after you log out:
```bash
nohup python bot.py > bot.log 2>&1 &
``` 