import logging
import asyncio

from audio import AsyncIOScheduler, db, dp, bot, schedule_cookie_update, logger
from config import ADMIN_CHAT_ID
from aiogram.types import Message
from envparse import Env

async def main():
    scheduler = AsyncIOScheduler()
    schedule_cookie_update(scheduler)
    scheduler.start()

    logger.info("\u0411\u043e\u0442 \u0437\u0430\u043f\u0443\u0449\u0435\u043d!")
    try:
        await db.connect()
    except Exception as e:
        logger.critical(f"\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f \u043a \u0411\u0414: {e}")
        return

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\u0411\u043e\u0442 \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d")
