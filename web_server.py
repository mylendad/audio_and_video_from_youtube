import asyncio
import aiohttp
from aiohttp import web
import os
import logging
import secrets
from contextlib import asynccontextmanager
from config import HTTP_PORT

logger = logging.getLogger(__name__)

SERVE_DIR = "temp_serve"
os.makedirs(SERVE_DIR, exist_ok=True)

async def get_public_ip() -> str:
    """Получает публичный IP-адрес с помощью внешнего сервиса."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org') as response:
                response.raise_for_status()
                ip = await response.text()
                logger.info(f"Успешно получен публичный IP: {ip}")
                return ip.strip()
    except Exception as e:
        logger.error(f"Не удалось получить публичный IP: {e}")
        raise ConnectionError("Не удалось определить публичный IP-адрес сервера.") from e

@asynccontextmanager
async def public_file_server(original_path: str, content_type: str = 'application/octet-stream'):
    """
    Асинхронный контекстный менеджер для временной публикации файла с использованием aiohttp.
    """
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Файл для публикации не найден: {original_path}")

    public_ip = await get_public_ip()
    port = HTTP_PORT
    
    random_filename = f"{secrets.token_hex(16)}_{os.path.basename(original_path)}"
    served_path = os.path.join(SERVE_DIR, random_filename)
    
    os.rename(original_path, served_path)

    async def handle_get(request: web.Request):
        logger.info(f"[AIOHTTP_SERVER] Получен запрос: {request.path}")
        return web.FileResponse(path=served_path, headers={"Content-Type": content_type})

    app = web.Application()
    app.router.add_get(f"/{random_filename}", handle_get)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    public_url = f"http://{public_ip}:{port}/{random_filename}"
    
    try:
        await site.start()
        logger.info(f"Файл доступен по временному URL (aiohttp): {public_url}")
        yield public_url
    finally:
        logger.info("Остановка временного aiohttp-сервера...")
        await runner.cleanup()
        if os.path.exists(served_path):
            try:
                os.remove(served_path)
                logger.info(f"Удален временный файл: {served_path}")
            except OSError as e:
                logger.error(f"Ошибка при удалении временного файла {served_path}: {e}")