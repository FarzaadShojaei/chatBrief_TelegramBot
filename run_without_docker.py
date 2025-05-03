import subprocess
import sys
import os

def check_requirements():
    try:
        import telegram
        import schedule
        import pytz
        import requests
        import dotenv
        return True
    except ImportError:
        return False

def main():
    if not check_requirements():
        print("Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("Starting bot...")
    from bot import SummaryBot
    bot = SummaryBot()
    bot.run()

if __name__ == "__main__":
    main() 