import os
import time

import asyncpg
import docker
import pytest
import pytest_asyncio
from clients.pg_client import AsyncPostgresClient

POSTGRES_IMAGE = "postgres:15"
POSTGRES_USER = "test_user"
POSTGRES_PASSWORD = "test_pass"
POSTGRES_DB = "test_db"
CONTAINER_NAME = "test_pg_container"
PORT = 5433


@pytest.fixture(scope="session")
def docker_postgres():
    if "DB_DSN" in os.environ:
        yield os.environ["DB_DSN"]
    else:
        client = docker.from_env()
        try:
            client.containers.get(CONTAINER_NAME).stop()
        except docker.errors.NotFound:
            pass

        container = client.containers.run(
            POSTGRES_IMAGE,
            name=CONTAINER_NAME,
            environment={
                "POSTGRES_USER": POSTGRES_USER,
                "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
                "POSTGRES_DB": POSTGRES_DB,
            },
            ports={"5432/tcp": PORT},
            detach=True,
        )

        time.sleep(3)

        for _ in range(10):
            try:
                conn = asyncpg.connect(
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD,
                    database=POSTGRES_DB,
                    host="localhost",
                    port=PORT,
                )
                break
            except Exception:
                time.sleep(1)
        else:
            container.stop()
            pytest.fail("PostgreSQL в Docker не поднялся")

        yield f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{PORT}/{POSTGRES_DB}"
        container.stop()


@pytest_asyncio.fixture(scope="module")
async def db(docker_postgres):
    client = AsyncPostgresClient(dsn=docker_postgres)
    await client.connect()
    await client.init_db()
    yield client
    await client.close()


@pytest_asyncio.fixture()
async def actioner(db):
    from clients.async_user_actioner import AsyncUserActioner

    return AsyncUserActioner(db)
