import psycopg2
from psycopg2 import sql

import asyncpg
from asyncpg import Pool

import asyncio
import logging

from typing import Optional, List, Tuple, Any

logger = logging.getLogger(__name__)

CREATE_QUERY = """
    CREATE TABLE IF NOT EXISTS users (
        user_id bigint PRIMARY KEY,
        username varchar,
        chat_id integer not null,
        last_updated_date integer not null
    );
"""

class AsyncPostgresClient:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[Pool] = None

    async def connect(self, retries: int = 5):
        delay = 1
        for attempt in range(retries):
            try:
                self.pool = await asyncpg.create_pool(self.dsn)
                logger.info("Connected to Postgres")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to DB (attempt {attempt+1}/{retries}): {e}")
                await asyncio.sleep(delay)
                delay *= 2
        raise ConnectionError("Failed to connect to Postgres after retries")

    async def init_db(self):
        await self.execute(CREATE_QUERY, ())

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, params: Tuple[Any, ...]) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *params)

    async def execute(self, query: str, params: Tuple[Any, ...]) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(query, *params)

