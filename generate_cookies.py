import os
import browser_cookie3
from http.cookiejar import MozillaCookieJar

OUTPUT_FILE = 'www.youtube.com_cookies.txt'

def export_youtube_cookies_to_txt():
    try:
        cj = browser_cookie3.chrome(domain_name='youtube.com')
    except Exception as e:
        print(f"Не удалось получить cookies из Chrome: {e}")
        return

    try:
        cj.save(OUTPUT_FILE, ignore_discard=True, ignore_expires=True)
        print(f"Cookies сохранены в {OUTPUT_FILE}, сохранено {len(cj)} cookies")
    except Exception as e:
        print(f"Ошибка при сохранении cookies: {e}")

if __name__ == '__main__':
    export_youtube_cookies_to_txt()