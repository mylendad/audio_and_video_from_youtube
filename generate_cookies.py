import os
from lib import browser_cookie3
from http.cookiejar import MozillaCookieJar
import logging

# TODO: This script has a critical architectural flaw. It depends on a local
# Google Chrome browser installation to extract cookies, making the application
# non-portable and unsuitable for containerized deployment. This entire mechanism
# needs to be re-thought for a production environment, for example by using aaudio_and_video_from_youtube
# proper API-based authentication method or a more robust cookie management solution.

OUTPUT_FILE = 'www.youtube.com_cookies.txt'

def export_youtube_cookies_to_txt():
    """
    Extracts YouTube cookies from Chrome and saves them to a Netscape-formatted
    text file.
    """
    # Create an empty MozillaCookieJar, which can be saved to a file.
    mozilla_cj = MozillaCookieJar()

    try:
        # browser_cookie3.chrome returns a standard CookieJar, which is iterable.
        chrome_cookies = browser_cookie3.chrome(domain_name='youtube.com')
        
        # Iterate over the cookies and add them to our saveable MozillaCookieJar.
        for cookie in chrome_cookies:
            mozilla_cj.set_cookie(cookie)

    except Exception as e:
        logging.error(f"Не удалось получить cookies из Chrome: {e}")
        return False

    try:
        # Save the MozillaCookieJar to the output file.
        mozilla_cj.save(OUTPUT_FILE, ignore_discard=True, ignore_expires=True)
        logging.info(f"Cookies сохранены в {OUTPUT_FILE}, сохранено {len(mozilla_cj)} cookies")
        return True
    except Exception as e:
        logging.error(f"Ошибка при сохранении cookies: {e}")
        return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    export_youtube_cookies_to_txt()