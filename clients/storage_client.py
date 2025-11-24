import asyncssh
import os
from urllib.parse import urljoin
import logging

from config import (
    STORAGE_HOST,
    STORAGE_PORT,
    STORAGE_USER,
    STORAGE_PASSWORD,
    STORAGE_PRIVATE_KEY_PATH,
    STORAGE_PATH,
    STORAGE_PUBLIC_URL_PREFIX
)

logger = logging.getLogger(__name__)

class StorageClient:
    def __init__(self):
        self.host = STORAGE_HOST
        self.port = STORAGE_PORT
        self.user = STORAGE_USER
        self.password = STORAGE_PASSWORD
        self.key_path = STORAGE_PRIVATE_KEY_PATH
        self.remote_path = STORAGE_PATH
        self.url_prefix = STORAGE_PUBLIC_URL_PREFIX

        if not all([self.host, self.user, self.remote_path, self.url_prefix]):
            raise ValueError("Storage client is not configured. Please check STORAGE_HOST, STORAGE_USER, STORAGE_PATH, and STORAGE_PUBLIC_URL_PREFIX.")
        if not self.password and not self.key_path:
            raise ValueError("Storage client auth is not configured. Please provide either STORAGE_PASSWORD or STORAGE_PRIVATE_KEY_PATH.")

    async def upload_file(self, local_path: str) -> str:
        """
        Uploads a file to the remote storage via SFTP and returns its public URL.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        file_name = os.path.basename(local_path)
        remote_file_path = os.path.join(self.remote_path, file_name)

        conn_opts = {
            "host": self.host.strip(),
            "port": self.port,
            "username": self.user,
            "known_hosts": None
        }
        if self.key_path:
            conn_opts["client_keys"] = [self.key_path]
        elif self.password:
            conn_opts["password"] = self.password

        logger.info(f"Connecting to storage at {self.host}:{self.port}...")
        try:
            async with asyncssh.connect(**conn_opts) as conn:
                logger.info(f"Uploading {local_path} to {remote_file_path}...")
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(local_path, remote_file_path)
                    # Устанавливаем права на файл, чтобы веб-сервер мог его прочитать
                    await sftp.chmod(remote_file_path, 0o644)
                logger.info("File uploaded and permissions set successfully.")

            public_url = urljoin(self.url_prefix, file_name)
            logger.info(f"File is available at public URL: {public_url}")
            
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}", exc_info=True)
            raise ConnectionError("Failed to upload file to storage.") from e

storage_client = StorageClient()
