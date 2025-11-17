import asyncio
import aiohttp
import http.server
import socketserver
import threading
import os
import logging
import secrets
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Директория для временного хостинга файлов
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

def find_free_port() -> int:
    """Находит свободный порт для запуска сервера."""
    with socketserver.TCPServer(("0.0.0.0", 0), None) as s:
        return s.server_address[1]

@asynccontextmanager
async def public_file_server(original_path: str):
    """
    Асинхронный контекстный менеджер для временной публикации файла по HTTP.
    При входе в контекст запускает HTTP-сервер и возвращает публичный URL.
    При выходе из контекста останавливает сервер и удаляет файл.
    """
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Файл для публикации не найден: {original_path}")

    public_ip = await get_public_ip()
    port = find_free_port()
    
    # Генерируем случайное имя файла для безопасности
    random_filename = f"{secrets.token_hex(16)}_{os.path.basename(original_path)}"
    served_path = os.path.join(SERVE_DIR, random_filename)
    
    # Перемещаем файл в директорию для раздачи
    os.rename(original_path, served_path)

    handler = http.server.SimpleHTTPRequestHandler
    
    # Используем functools.partial, чтобы передать директорию в обработчик
    from functools import partial
    handler_with_dir = partial(handler, directory=SERVE_DIR)

    httpd = None
    server_thread = None
    public_url = f"http://{public_ip}:{port}/{random_filename}"
    
    try:
        httpd = socketserver.TCPServer(("", port), handler_with_dir)
        
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info(f"Файл доступен по временному URL: {public_url}")
        
        yield public_url
        
    finally:
        logger.info("Остановка временного HTTP-сервера...")
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        if server_thread:
            server_thread.join(timeout=5)
        
        if os.path.exists(served_path):
            try:
                os.remove(served_path)
                logger.info(f"Удален временный файл: {served_path}")
            except OSError as e:
                logger.error(f"Ошибка при удалении временного файла {served_path}: {e}")
