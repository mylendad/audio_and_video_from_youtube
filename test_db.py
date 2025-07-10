import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta, timezone

from clients.pg_client import AsyncPostgresClient
from clients.async_user_actioner import AsyncUserActioner

TEST_DSN = "postgresql://postgres:postgres@localhost:5432/test_db"

@pytest_asyncio.fixture(scope="module")
async def db():
    client = AsyncPostgresClient(TEST_DSN)
    await client.connect()
    await client.init_db()
    yield client
    await client.close()

@pytest_asyncio.fixture()
async def actioner(db):
    return AsyncUserActioner(db)

@pytest.mark.asyncio
async def test_create_and_get_user(actioner):
    user_id = 1001
    username = "test_user"
    chat_id = 777
    now = datetime.now(timezone.utc)

    await actioner.create_user(user_id, username, chat_id, now)
    user = await actioner.get_user(user_id)

    assert user is not None
    assert user["user_id"] == user_id
    assert user["username"] == username
    assert user["chat_id"] == chat_id
    assert isinstance(user["last_updated_date"], datetime)

@pytest.mark.asyncio
async def test_update_user_date(actioner):
    user_id = 1001
    new_date = datetime.now(timezone.utc) + timedelta(days=1)

    await actioner.update_date(user_id, new_date)
    user = await actioner.get_user(user_id)

    assert user is not None
    assert abs((user["last_updated_date"] - new_date).total_seconds()) < 5
