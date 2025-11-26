import os
import asyncio
import re
import time
from datetime import datetime, timezone
from lib import browser_cookie3
import logging
import mimetypes
# import aiohttp

from aiogram import Bot, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import URLInputFile
import glob

from web_server import public_file_server
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from generate_cookies import export_youtube_cookies_to_txt

from redis_lock import acquire_user_lock, release_user_lock
from clients.async_user_actioner import AsyncUserActioner
from clients.pg_client import AsyncPostgresClient
from clients.storage_client import storage_client

from config import TOKEN, ADMIN_CHAT_ID, ADMIN_USER_ID, DB_DSN, REQUIRED_CHANNELS, COOKIE_FILE
from constants import FORMATS


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Лимит размера файла для прямой отправки (49 МБ для надежности)
MAX_FILE_SIZE = 49 * 1024 * 1024


bot = Bot(token=TOKEN)

db = AsyncPostgresClient(dsn=DB_DSN)
user_actioner = AsyncUserActioner(db)

class DownloadState(StatesGroup):
    waiting_for_format = State()

# async def debug_url(url: str):
#     logger.info(f"--- DEBUGGING URL: {url} ---")
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 logger.info(f"DEBUG: Status: {response.status}")
#                 logger.info("DEBUG: Headers:")
#                 for key, value in response.headers.items():
#                     logger.info(f"  {key}: {value}")
#                 
#                 content_preview = await response.content.read(512)
#                 logger.info(f"DEBUG: Content Preview (first 512 bytes): {content_preview.decode('utf-8', errors='ignore')}")
#     except Exception as e:
#         logger.error(f"DEBUG: Error while fetching URL: {e}", exc_info=True)
#     logger.info("--- END DEBUGGING ---")
   
def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 Б"
    
    units = ("Б", "КБ", "МБ", "ГБ")
    i = 0
    size = size_bytes
    
    while size >= 1024 and i < len(units)-1:
        size /= 1024
        i += 1
        
    return f"{size:.2f} {units[i]}"  


def is_youtube_url(url: str) -> bool:
    """Checks if the given URL is a valid YouTube URL."""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

async def estimate_video_size(url: str, format_config: dict) -> int:
    ydl_opts = {
        'quiet': True,
        'simulate': True,
        'format': format_config['format'],
        'cookiefile': COOKIE_FILE,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    if 'postprocessors' in format_config:
        ydl_opts['postprocessors'] = format_config['postprocessors']

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            
            if 'requested_downloads' in info and info['requested_downloads']:
                filesize = info['requested_downloads'][0].get('filesize')
                if filesize:
                    return filesize
                    
            tbr = info.get('tbr') or 0
            duration = info.get('duration') or 1
            
            estimated_size = (tbr * 1000 * duration) / 8
            return int(estimated_size)
            
    except Exception as e:
        logger.error(f"Ошибка оценки размера: {e}")
        return 0

async def send_subscription_request(chat_id: int):
    """
    Sends a message with inline buttons for required channel subscriptions.
    If no valid channels are configured, this function does nothing.
    """
    channel_buttons = []
    for channel in REQUIRED_CHANNELS:
        channel_name = channel.strip()
        url_username = channel_name.lstrip('@')
        # Ensure we have a non-empty username for the URL to be valid
        if url_username:
            channel_buttons.append(
                types.InlineKeyboardButton(
                    text=f"Подписаться на {channel_name}",
                    url=f"https://t.me/{url_username}"
                )
            )

    # If there are no valid channels to subscribe to, do not send the message.
    if not channel_buttons:
        logger.info("Subscription request skipped: no valid REQUIRED_CHANNELS are set.")
        return

    # Build the keyboard with one button per row for channels
    keyboard_rows = [[button] for button in channel_buttons]
    # Add the "check" button on the final row
    keyboard_rows.append([
        types.InlineKeyboardButton(text="Я подписался", callback_data="check_subscription_callback")
    ])

    markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    await bot.send_message(
        chat_id,
        "Для использования бота необходимо подписаться на каналы:",
        reply_markup=markup
    )


async def ensure_user_exists(message_or_query: types.Message | types.CallbackQuery) -> bool:
    user_id = message_or_query.from_user.id
    user = await user_actioner.get_user(user_id)
    
    if user is not None:
        return True
        
    if await is_user_subscribed(user_id):
        username = message_or_query.from_user.username or ""
        chat_id = message_or_query.message.chat.id if isinstance(message_or_query, types.CallbackQuery) else message_or_query.chat.id
        now = datetime.now(timezone.utc)
        
        try:
            await user_actioner.create_user(user_id, username, chat_id, now)
            logger.info(f"Авторегистрация пользователя: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка авторегистрации {user_id}: {e}")

    if isinstance(message_or_query, types.CallbackQuery):
        await message_or_query.message.answer("Для использования бота:\n1. Подпишитесь на каналы\n2. Нажмите /start")
    else:
        await message_or_query.answer("Для использования бота:\n1. Подпишитесь на каналы\n2. Нажмите /start")
        
    return False

async def is_user_subscribed(user_id: int) -> bool:
    """Checks if the user is subscribed to all required channels."""
    # Skip check if the list is not defined or contains only empty strings
    if not REQUIRED_CHANNELS or not any(c.strip() for c in REQUIRED_CHANNELS):
        return True

    for channel in REQUIRED_CHANNELS:
        channel_name = channel.strip()
        if not channel_name:
            continue  # Skip any empty entries in the list

        try:
            member = await bot.get_chat_member(chat_id=channel_name, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logger.warning(f"Ошибка при проверке подписки на {channel_name}: {e}")
            # If we can't check one channel, we assume failure for security.
            return False
    return True

async def process_download(message: types.Message, format_key: str, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await ensure_user_exists(message):
        return

    user_data = await state.get_data()
    url = user_data.get("last_url")

    if not url:
        await message.answer("Сначала отправьте ссылку на видео.")
        return

    if not is_youtube_url(url):
        await message.answer("Пожалуйста, отправьте действительную ссылку на YouTube.")
        return

    format_config = FORMATS.get(format_key)
    if not format_config:
        await message.answer("Неподдерживаемый формат.")
        return

    if not await is_user_subscribed(user_id):
        await message.answer("Для скачивания необходимо подписаться на каналы.")
        await send_subscription_request(chat_id)
        return

    if not acquire_user_lock(user_id):
        await message.answer(" У вас уже выполняется загрузка. Пожалуйста, подождите.")
        return

    try:
        await user_actioner.update_date(user_id, datetime.now(timezone.utc))
    except Exception as e:
        logger.warning(f" Не удалось обновить дату для пользователя {user_id}: {e}")

    status_message = await message.answer("Пожалуйста, подождите...")

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    base_filename = f"temp_{user_id}_{timestamp}"
    output_template = f"{base_filename}.%(ext)s"
    final_path = None

    last_update_time = 0
    loop = asyncio.get_running_loop()

    async def edit_status_message(text: str):
        try:
            await status_message.edit_text(text)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                logger.warning(f"Could not edit progress message: {e}")
        except Exception as e:
            logger.warning(f"Could not edit progress message: {e}")

    def progress_hook(d):
        nonlocal last_update_time
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - last_update_time < 5:
                return

            percent_str = d.get('_percent_str', '0.0%').strip()
            speed_str = d.get('_speed_str', 'N/A').strip()
            eta_str = d.get('_eta_str', 'N/A').strip()
            
            text = f" Загрузка: {percent_str} | Скорость: {speed_str} | ETA: {eta_str}"
            asyncio.run_coroutine_threadsafe(edit_status_message(text), loop)
            last_update_time = current_time
        
        elif d['status'] == 'finished':
            asyncio.run_coroutine_threadsafe(edit_status_message(" Загрузка завершена, обработка..."), loop)

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'format': format_config['format'],
        'buffersize': 1024 * 1024 * 16,
        'http_chunk_size': 1048576,
        'continuedl': True,
        'noprogress': True, 
        'verbose': False,
        'cookiefile': COOKIE_FILE,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'progress_hooks': [progress_hook],
    }

    if 'postprocessors' in format_config:
        ydl_opts['postprocessors'] = format_config['postprocessors']
        ydl_opts['keepvideo'] = True  

    try:
        logger.info(f"Начало обработки: {url}")
        logger.info(f"Формат: {format_key}")
        logger.info(f"Параметры: {format_config}")
        
        with YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url)
            url = None
            logger.info(f"Информация о видео: {info.get('title')}")
            logger.info(f"Расширение: {info.get('ext')}")
            if 'requested_downloads' in info and info['requested_downloads']:
                logger.info(f"Запрошенные загрузки: {info['requested_downloads'][0]}")

            if 'postprocessors' in format_config:
                ext = format_config['extension']
                final_path = f"{base_filename}.{ext}"
                
                for i in range(15):
                    if os.path.exists(final_path):
                        break
                    logger.info(f"Ожидание файла ({i+1}/15): {final_path}")
                    await asyncio.sleep(1)
                else:
                    raise FileNotFoundError(f"Конвертированный файл не найден: {final_path}")
            else:
                ext = info.get('ext', 'mp4')
                final_path = f"{base_filename}.{ext}"
                
                if not os.path.exists(final_path):
                    candidates = glob.glob(f"{base_filename}*")
                    logger.info(f"Файл не найден, кандидаты: {candidates}")
                    
                    filtered_candidates = [
                        f for f in candidates 
                        if not re.search(r'\.f\d+\.', f)
                        and not f.endswith('.part')        
                        and not f.endswith('.ytdl')                             ]
                    
                    logger.info(f"Отфильтрованные кандидаты: {filtered_candidates}")
                    
                    if filtered_candidates:
                        filtered_candidates.sort(key=os.path.getmtime, reverse=True)
                        final_path = filtered_candidates[0]
                        logger.info(f"Выбран файл по дате изменения: {final_path}")
                    
                    if not os.path.exists(final_path) and candidates:
                        final_path = candidates[0]
                        logger.info(f"Выбран первый кандидат: {final_path}")

        if not os.path.exists(final_path):
            raise FileNotFoundError(f"Файл не найден после скачивания: {final_path}")

        file_size = os.path.getsize(final_path)
        logger.info(f"Финальный путь: {final_path}, размер: {file_size} байт")

        if file_size <= MAX_FILE_SIZE:
            logger.info("Файл меньше 50 МБ, отправка напрямую.")
            fs_file = types.FSInputFile(final_path)
            if format_config['send_method'] == 'send_audio':
                await message.answer_audio(fs_file)
            elif format_config['send_method'] == 'send_video':
                await message.answer_video(fs_file)
            else:
                await message.answer_document(fs_file)
        else:
            logger.info("Файл > 50 МБ. Загрузка на удаленное хранилище для получения ссылки.")
            await status_message.edit_text("Загрузка большого файла на сервер...")

            try:
                # 1. Загрузка на удаленное хранилище и получение URL
                public_url = await storage_client.upload_file(final_path)
                logger.info(f"Файл загружен, получен URL: {public_url}")

                # 2. Отправка ссылки пользователю для отладки
                await status_message.edit_text("Отправка ссылки на файл...")
                await message.answer(
                    f"Файл слишком большой для автоматической отправки.\n\n"
                    f"Вы можете скачать его по прямой ссылке (отладочный режим):\n"
                    f"{public_url}"
                )
                await status_message.delete()

            except Exception as e:
                logger.error(f"Ошибка при обработке большого файла: {e}", exc_info=True)
                await message.answer(f"Не удалось обработать большой файл. Ошибка: {e}")
                # Ошибку не перевыбрасываем, чтобы выполнился блок finally для очистки,
                # но пользователь уже уведомлен.


    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}. Aborting download process.")
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при скачивании/отправке: {e}", exc_info=True)
        error_message = f"Произошла ошибка: {str(e)}"
        
        if "File not found" in str(e):
            error_message += "\n\n Файл не был создан после обработки. Возможно, проблема с конвертацией."
        elif "Unable to download webpage" in str(e):
            error_message += "\n\n Ошибка доступа к видео. Проверьте ссылку или попробуйте позже."
        elif "Private video" in str(e):
            error_message += "\n\n Это приватное видео. Доступ ограничен."
        elif "Members-only" in str(e):
            error_message += "\n\n Видео доступно только для участников канала."
        elif "Copyright" in str(e):
            error_message += "\n\Видео содержит защищенный авторским правом контент."
        
        try:
            await message.answer(error_message)
        except TelegramForbiddenError:
            logger.warning(f"Bot is blocked by user {user_id}. Could not send final error message.")
        
        await state.clear()

    finally:
        
        release_user_lock(user_id)
        if final_path and os.path.exists(final_path):
            try:
                os.remove(final_path)
                logger.info(f"Удален временный файл: {final_path}")
            except Exception as e:
                logger.warning(f"Ошибка при удалении {final_path}: {e}")
        
        temp_files = glob.glob(f"{base_filename}*")
        for temp_file in temp_files:
            if temp_file != final_path and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Удален временный файл: {temp_file}")
                except Exception as e:
                    logger.warning(f"Ошибка удаления временного файла {temp_file}: {e}")