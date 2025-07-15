from datetime import date
from clients.pg_client import AsyncPostgresClient

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

class AsyncUserActioner:
    def __init__(self, db: AsyncPostgresClient):
        self.db = db

    async def get_user(self, user_id: int):
        result = await self.db.fetch(GET_USER, (user_id,))
        return result[0] if result else None

    async def create_user(self, user_id: int, username: str, chat_id: int, last_updated_date: int):
        await self.db.execute(INSERT_USER, (user_id, username, chat_id, last_updated_date))

    async def update_date(self, user_id: int, update_date: int):
        await self.db.execute(UPDATE_DATE, (update_date, user_id))
