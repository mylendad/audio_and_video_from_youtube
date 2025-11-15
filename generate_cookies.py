import os
from lib import browser_cookie3
from http.cookiejar import MozillaCookieJar
import logging

# TODO: This script has a critical architectural flaw. It depends on a local
# Google Chrome browser installation to extract cookies, making the application
# non-portable and unsuitable for containerized deployment. This entire mechanism
# needs to be re-thought for a production environment, for example by using a
# proper API-based authentication method or a more robust cookie management solution.

OUTPUT_FILE = 'www.youtube.com_cookies.txt'

def export_youtube_cookies_to_txt():
    try:
        cj = browser_cookie3.chrome(domain_name='youtube.com')
    except Exception as e:
        logging.error(f"Не удалось получить cookies из Chrome: {e}")
        return

    try:
        cj.save(OUTPUT_FILE, ignore_discard=True, ignore_expires=True)
        logging.info(f"Cookies сохранены в {OUTPUT_FILE}, сохранено {len(cj)} cookies")
    except Exception as e:
        logging.error(f"Ошибка при сохранении cookies: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    export_youtube_cookies_to_txt()