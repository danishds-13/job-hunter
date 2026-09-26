import os
import requests
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing from .env")

if not CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID is missing from .env")


def send_telegram_message(message):
    """
    Send a message to the configured Telegram chat.
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    if not response.ok:
        print("Telegram error:")
        print(response.text)

        return False

    return True


if __name__ == "__main__":

    test_message = """🚀 DevOps Job Hunter

Telegram connection successful!

Your automated job alerts are ready.
"""

    if send_telegram_message(test_message):
        print("======================================")
        print("TELEGRAM TEST SUCCESSFUL")
        print("======================================")
        print("Message sent successfully!")