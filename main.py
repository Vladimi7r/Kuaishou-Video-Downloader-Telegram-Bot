import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
from bs4 import BeautifulSoup
import io
from urllib.parse import urljoin

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = '7704188651:AAGFC-IG0LEqOKHYShf3ZQv9XqRYMyUZ1XQ'

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me a Kuaishou video URL, and I will download it for you.')

def get_video_url(page_url: str) -> str:
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        
        if not video_tag:
            return None
            
        video_src = video_tag.get('src') or video_tag.get('data-src')
        if not video_src:
            return None
            
        # Handle relative URLs
        video_url = urljoin(page_url, video_src)
        return video_url
        
    except Exception as e:
        logger.error(f"Error extracting video URL: {e}")
        return None

def download_video(video_url: str) -> io.BytesIO:
    try:
        response = requests.get(video_url, headers=HEADERS, stream=True, timeout=10)
        response.raise_for_status()
        
        video_file = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            video_file.write(chunk)
        video_file.seek(0)
        return video_file
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    
    # Basic URL validation
    if not url.startswith(('https://www.kuaishou.com/', 'https://m.kuaishou.com/')):
        update.message.reply_text("Please provide a valid Kuaishou URL.")
        return
        
    try:
        video_url = get_video_url(url)
        if not video_url:
            update.message.reply_text("❌ Could not find video in the provided URL.")
            return
            
        video_file = download_video(video_url)
        
        # Check file size (Telegram limit: 50MB for videos)
        if video_file.getbuffer().nbytes > 50 * 1024 * 1024:
            update.message.reply_text("⚠️ The video is too large to send via Telegram (max 50MB).")
            return
            
        update.message.reply_video(
            video=video_file,
            filename='kuaishou_video.mp4',
            caption="Here's your video! 🎥"
        )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        update.message.reply_text("❌ An error occurred while processing your request. Please try again later.")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
