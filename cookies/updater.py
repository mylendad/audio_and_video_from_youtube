import browser_cookie3
from http.cookiejar import MozillaCookieJar
import logging

from aiogram import types, Router


router = Router()


OUTPUT_FILE = 'www.youtube.com_cookies.txt'
logger = logging.getLogger(__name__)

def export_youtube_cookies_to_txt() -> bool:
    try:
        cj = browser_cookie3.chrome(domain_name='youtube.com')
    except Exception as e:
        logger.error(f"Не удалось получить cookies из Chrome: {e}")
        return False

    try:
        cj.save(OUTPUT_FILE, ignore_discard=True, ignore_expires=True)
        logger.info(f"Cookies сохранены в {OUTPUT_FILE}, сохранено {len(cj)} cookies")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении cookies: {e}")
        return False
