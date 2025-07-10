import os
import asyncio
# from datetime import datetime, date
from datetime import datetime, timezone
from envparse import Env
import browser_cookie3
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Bot, Dispatcher, types

from yt_dlp import YoutubeDL
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from cookies.updater import export_youtube_cookies_to_txt

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clients.async_user_actioner import AsyncUserActioner
from clients.pg_client import AsyncPostgresClient

env = Env()
env.read_envfile()

TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
COOKIE_FILE = "www.youtube.com_cookies.txt"
SERVICE_ACCOUNT_FILE = "key.json"
GDRIVE_FOLDER_ID = env.str("GDRIVE_FOLDER_ID")
SCOPES = ['https://www.googleapis.com/auth/drive']
ADMIN_USER_ID = env.int("ADMIN_USER_ID")

MAX_TELEGRAM_SIZE = 50 * 1024 * 1024 # 50 MB
REQUIRED_CHANNELS = env.str("REQUIRED_CHANNELS")

FORMATS = {
    'mp3': {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'extension': 'mp3',
        'send_method': 'send_audio'
    },
    '144': {
        'format': 'bestvideo[height<=144][ext=mp4]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '240': {
        'format': 'bestvideo[height<=240]+bestaudio/best[height<=240]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '360': {
        'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '480': {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '720': {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
    '1080': {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'extension': 'mp4',
        'send_method': 'send_video'
    },
}

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = AsyncPostgresClient(dsn=env.str("DB_DSN"))
user_actioner = AsyncUserActioner(db)

class DownloadState(StatesGroup):
    waiting_for_format = State()

def schedule_cookie_update(scheduler: AsyncIOScheduler):
    logger.info("Настраиваем автообновление cookies...")
    scheduler.add_job(export_youtube_cookies_to_txt, trigger="interval", hours=12, id="update_cookies")
    logger.info("Планировщик cookies активирован")

async def is_user_subscribed(user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logger.warning(f"Ошибка при проверке подписки на {channel}: {e}")
            return False
    return True

async def process_download(message: types.Message, format_key: str, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id

    user_data = await state.get_data()
    url = user_data.get("last_url")

    if not url:
        await message.answer("Сначала отправьте ссылку на видео.")
        return

    format_config = FORMATS.get(format_key)
    if not format_config:
        await message.answer("Неподдерживаемый формат.")
        return

    try:
        await user_actioner.update_date(user_id, datetime.now(timezone.utc))
    except Exception as e:
        logger.warning(f"Не удалось обновить дату для пользователя {user_id}: {e}")

    await message.answer("Пожалуйста, подождите...")

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    base_filename = f"temp_{user_id}_{timestamp}"
    output_template = f"{base_filename}.%(ext)s"
    final_path = None

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'format': format_config['format'],
        'buffersize': 1024 * 1024 * 16,
        'http_chunk_size': 1048576,
        'continuedl': True,
        'noprogress': False,
        'verbose': True,
        'cookiefile': COOKIE_FILE,
        'proxy': 'socks5://127.0.0.1:9050',
    }

    if 'postprocessors' in format_config:
        ydl_opts['postprocessors'] = format_config['postprocessors']

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url)
            final_path = ydl.prepare_filename(info)

        if not os.path.exists(final_path):
            raise FileNotFoundError("Файл не найден после скачивания")

        file_size = os.path.getsize(final_path)

        if file_size > MAX_TELEGRAM_SIZE:
            file_metadata = {'name': os.path.basename(final_path), 'parents': [GDRIVE_FOLDER_ID]}
            media = MediaFileUpload(final_path, resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
            service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=file.get("id")).execute()
            await message.answer(f"Файл слишком большой для Telegram.\nСкачать с Google Drive: {file.get('webViewLink')}")
        else:
            fs_file = types.FSInputFile(final_path)
            if format_config['send_method'] == 'send_audio':
                await message.answer_audio(fs_file)
            elif format_config['send_method'] == 'send_video':
                await message.answer_video(fs_file)

    except Exception as e:
        logger.error(f"Ошибка при скачивании/отправке: {e}")
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        if final_path and os.path.exists(final_path):
            try:
                os.remove(final_path)
            except Exception as e:
                logger.warning(f"Ошибка при удалении {final_path}: {e}")

@dp.message(Command("refresh_cookies"))
async def refresh_cookies_handler(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return

    await message.answer("Обновляю cookies...")
    success = export_youtube_cookies_to_txt()
    if success:
        await message.answer("Cookies успешно обновлены.")
    else:
        await message.answer("Не удалось обновить cookies. Проверь лог.")

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    chat_id = message.chat.id
    now = datetime.now(timezone.utc)

    if not await is_user_subscribed(user_id):
        buttons = [types.InlineKeyboardButton(text="Подписаться", url=f"https://t.me/{ch[1:]}") for ch in REQUIRED_CHANNELS]
        markup = types.InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])
        await message.answer("Чтобы пользоваться ботом, подпишитесь на каналы:", reply_markup=markup)
        return

    try:
        await user_actioner.create_user(user_id, username, chat_id, now)
    except Exception as e:
        logger.warning(f"Ошибка при создании пользователя {user_id}: {e}")

    await message.answer(f"Привет, {message.from_user.first_name}!\nЯ бот для скачивания видео с YouTube. Просто отправь мне ссылку на видео 🎥.")

@dp.message(Command("update_cookies"))
async def update_cookies_command(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        await message.answer("Доступ запрещён.")
        return

    try:
        cj = browser_cookie3.chrome(domain_name='youtube.com')
        cj.save(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
        await message.answer("Cookies обновлены успешно.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении cookies: {e}")
        await message.answer(f"Не удалось обновить cookies: {e}")

@dp.message(F.text.regexp(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+'))
async def handle_video_link(message: types.Message, state: FSMContext):
    await state.set_state(DownloadState.waiting_for_format)
    await state.update_data(last_url=message.text)

    builder = ReplyKeyboardBuilder()
    for format_key in FORMATS.keys():
        builder.add(types.KeyboardButton(text=f"/{format_key}"))
    builder.adjust(3)

    await message.answer("Выберите качество или формат:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(Command(*FORMATS.keys()))
async def handle_format_command(message: types.Message, state: FSMContext):
    format_key = message.text[1:]
    await process_download(message, format_key, state)

async def main():
    scheduler = AsyncIOScheduler()
    schedule_cookie_update(scheduler)
    scheduler.start()
    logger.info("Бот запущен!")
    await db.connect()
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")