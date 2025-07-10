from datetime import datetime
from typing import Optional, Dict, Any
from clients.pg_client import AsyncPostgresClient

import logging

GET_USER = """
    SELECT user_id, username, chat_id, last_updated_date FROM users WHERE user_id = $1;
"""

INSERT_USER = """
    INSERT INTO users (user_id, username, chat_id, last_updated_date)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (user_id) DO NOTHING;
"""

UPDATE_DATE = """
    UPDATE users SET last_updated_date = $1 WHERE user_id = $2;
"""

logger = logging.getLogger(__name__)

class AsyncUserActioner:
    def __init__(self, db: AsyncPostgresClient):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        result = await self.db.fetch(GET_USER, (user_id,))
        if not result:
            logger.info(f"🔍 Пользователь {user_id} не найден")
            return None
        row = result[0]
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "chat_id": row["chat_id"],
            "last_updated_date": datetime.fromtimestamp(row["last_updated_date"])
        }

    async def create_user(self, user_id: int, username: str, chat_id: int, last_updated_date: datetime) -> None:
        logger.info(f"Создание пользователя: id={user_id}, username={username}, chat_id={chat_id}")
        await self.db.execute(INSERT_USER, (user_id, username, chat_id, int(last_updated_date.timestamp())))

    async def update_date(self, user_id: int, update_date: datetime) -> None:
        logger.info(f"Обновление времени пользователя {user_id} -> {update_date.isoformat()}")
        await self.db.execute(UPDATE_DATE, (int(update_date.timestamp()), user_id))

