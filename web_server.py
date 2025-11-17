import asyncio
import aiohttp
import http.server
import socketserver
import threading
import os
import logging
import secrets
from contextlib import asynccontextmanager
from config import HTTP_PORT

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

def create_file_handler(file_path, content_type):
    """Создает кастомный обработчик запросов для одного файла с явным content_type."""
    
    class CustomFileHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.file_path = file_path
            self.content_type = content_type
            super().__init__(*args, **kwargs)

        def do_GET(self):
            if self.path.endswith(os.path.basename(self.file_path)):
                try:
                    with open(self.file_path, 'rb') as f:
                        fs = os.fstat(f.fileno())
                        
                        self.send_response(200)
                        self.send_header("Content-type", self.content_type)
                        self.send_header("Content-Length", str(fs.st_size))
                        self.end_headers()
                        
                        self.copyfile(f, self.wfile)
                except FileNotFoundError:
                    self.send_error(404, "File not found")
            else:
                self.send_error(404, "File not found")

    return CustomFileHandler

@asynccontextmanager
async def public_file_server(original_path: str, content_type: str = 'application/octet-stream'):
    """
    Асинхронный контекстный менеджер для временной публикации файла по HTTP.
    """
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Файл для публикации не найден: {original_path}")

    public_ip = await get_public_ip()
    port = HTTP_PORT
    
    random_filename = f"{secrets.token_hex(16)}_{os.path.basename(original_path)}"
    served_path = os.path.join(SERVE_DIR, random_filename)
    
    os.rename(original_path, served_path)

    # Создаем обработчик для конкретного файла с явным content_type
    Handler = create_file_handler(served_path, content_type)

    httpd = None
    server_thread = None
    public_url = f"http://{public_ip}:{port}/{random_filename}"
    
    try:
        httpd = socketserver.TCPServer(("", port), Handler)
        
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
