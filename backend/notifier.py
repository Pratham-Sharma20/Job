import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_notification(job):
    """Sends a Telegram markdown message about a newly scraped job."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notifications skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured in .env.")
        return

    company = job.get("company", "Unknown Company")
    title = job.get("title", "Unknown Title")
    location = job.get("location", "Unknown Location")
    apply_link = job.get("apply_link", "")

    # Construct the markdown message
    message = (
        f"🚨 *New Job Added!*\n\n"
        f"🏢 *Company:* {company}\n"
        f"💼 *Role:* {title}\n"
        f"📍 *Location:* {location}\n"
    )
    
    if apply_link:
        message += f"🔗 *Apply:* [Link]({apply_link})\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send Telegram notification (status {response.status_code}): {response.text}")
        else:
            print(f"Telegram notification sent successfully for {title} @ {company}.")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
