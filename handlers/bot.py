import logging
from aiogram import Router, F, types
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from audio import process_download, DownloadState, ensure_user_exists, is_user_subscribed, send_subscription_request, estimate_video_size, format_size
from config import ADMIN_USER_ID, ADMIN_CHAT_ID
from constants import FORMATS
from generate_cookies import export_youtube_cookies_to_txt
from redis_lock import get_all_locks

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("health"))
async def healthcheck(message: types.Message):
    try:
        await message.answer("Бот работает.")
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {message.from_user.id}.")


@router.message(Command("locks"))
async def list_locks(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_USER_ID:
        try:
            await message.answer("Нет доступа.")
        except TelegramForbiddenError:
            logger.warning(f"Bot is blocked by user {user_id}.")
        return

    try:
        locks = get_all_locks()
        if not locks:
            await message.answer("Нет активных блокировок.")
        else:
            await message.answer("Активные блокировки:\n" + "\n".join(locks))
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}.")


@router.message(Command("check_subscription"))
async def check_subscription_command(message: types.Message):
    user_id = message.from_user.id
    try:
        if await is_user_subscribed(user_id):
            await message.answer("Вы подписаны на все каналы! Теперь вы можете скачивать видео.")
        else:
            await send_subscription_request(message.chat.id)
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}. Cannot process check_subscription command.")
          

@router.callback_query(F.data == "check_subscription_callback")
async def check_subscription_callback_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        if await is_user_subscribed(user_id):
            await callback.message.edit_text("Подписка подтверждена! Теперь вы можете скачивать видео.")
            await callback.answer()
        else:
            await callback.answer("Вы ещё не подписались на все каналы!", show_alert=True)
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}. Cannot process subscription callback.")


@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    try:
        if not await ensure_user_exists(message):
            return
        
        if not await is_user_subscribed(user_id):
            await send_subscription_request(message.chat.id)
            return

        await message.answer(f"Привет, {message.from_user.first_name}! Отправь ссылку на видео или аудио.")
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}. Cannot process start command.")


@router.message(F.text.regexp(r'https?://(?:www\.?youtube\.com/watch\?v=|youtu\.be/)["\w\-]+'))
async def handle_video_link(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        await message.answer("Пожалуйста подождите")

        if not await is_user_subscribed(user_id):
            await message.answer("Для скачивания необходимо подписаться на каналы.")
            await send_subscription_request(message.chat.id)
            return

        await state.set_state(DownloadState.waiting_for_format)
        await state.update_data(last_url=message.text)

        cached_sizes = {}

        response = "Выберите качество:\n\n"
        for format_key, format_info in FORMATS.items():
            key = (message.text, format_key)
            try:
                if key in cached_sizes:
                    size = cached_sizes[key]
                else:
                    size = await estimate_video_size(message.text, format_info)
                    cached_sizes[key] = size

                if size > 0:
                    size_str = format_size(size)
                    response += f"/{format_key} - {size_str}\n"
                else:
                    response += f"/{format_key}\n"
            except Exception as e:
                response += f"/{format_key}\n"

        builder = ReplyKeyboardBuilder()
        for format_key in FORMATS.keys():
            builder.add(types.KeyboardButton(text=f"/{format_key}"))
        builder.adjust(3)

        await message.answer(response, reply_markup=builder.as_markup(resize_keyboard=True))
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}. Cannot process video link.")


@router.message(Command(*FORMATS.keys()))
async def handle_format_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        format_key = message.text[1:]
        if format_key not in FORMATS:
            await message.answer("Неверный формат.")
            return

        user_data = await state.get_data()
        url = user_data.get("last_url")

        if not url:
            await message.answer("Сначала отправьте ссылку на видео.")
            return

        await process_download(message, format_key, state)

        await state.clear()
    except TelegramForbiddenError:
        logger.warning(f"Bot is blocked by user {user_id}, download process aborted.")
