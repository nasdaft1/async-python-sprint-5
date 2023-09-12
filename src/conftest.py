from typing import AsyncGenerator
import pytest
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient

import src.db.db as db
from src.db.models import Base
from src.main import app

engine_test = db.create_async_engine
async_session_maker = db.async_session
Base.metadata.bind = engine_test


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# app.dependency_overrides[get_async_session] = override_get_async_session

@pytest.fixture(autouse=True, scope='session')
async def prepare_database() -> None:
    async with db.engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(Base.metadata.create_all)
        pass
    yield
    async with db.engine.begin() as conn:
        pass
        # await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(Base.metadata.clear())


@pytest.fixture(scope='session')
def event_loop(request) -> None:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
