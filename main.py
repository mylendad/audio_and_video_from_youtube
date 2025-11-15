import logging
import asyncio

from aiogram import Dispatcher
from audio import AsyncIOScheduler, db, bot, logger #, schedule_cookie_update
from handlers import bot as bot_handlers

dp = Dispatcher()

async def main():
    scheduler = AsyncIOScheduler()
    # schedule_cookie_update(scheduler)
    scheduler.start()

    dp.include_router(bot_handlers.router)

    logger.info("Бот запущен!")
    try:    
        await db.connect()
    except Exception as e:
        logger.critical(f"Ошибка подключения к БД: {e}")
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
        logging.info("Бот остановлен")
