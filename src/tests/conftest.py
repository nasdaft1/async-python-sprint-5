import logging
import pytest
import asyncio
import os
import shutil
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from s3 import S3Client

from db.db import engine
from db.db import get_session
from db.models import Base
from main import app
from core.config import config, t_config_storage
from sqlalchemy.pool import NullPool

# подключаем тестовую БД
db_config = config.postgres_db_dns_test

engine = create_async_engine(db_config, poolclass=NullPool)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def test_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        logging.debug(f'Connect DB проверка= {db_config}')
        yield session


client = TestClient(app)

# подмена функции для тестирования
app.dependency_overrides[get_session] = test_get_session
# подмена функции для тестирования
s3 = S3Client(access_key=t_config_storage.aws_access_key_id,
              secret_key=t_config_storage.aws_secret_access_key,
              region=t_config_storage.region,
              s3_bucket=t_config_storage.bucket_name)

app.dependency_overrides[s3] = s3


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logging.info(f'Удаление бд с  {db_config}')


@pytest.fixture(scope='session')
def make_static_dir():
    """Создаем и удаляем каталог для временных файлов"""
    static_dir = config.test_dir
    os.makedirs(static_dir, exist_ok=True)
    yield static_dir
    shutil.rmtree(static_dir, ignore_errors=True)


@pytest.fixture(scope='session')
def event_loop(request) -> None:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def event_loop(request) -> None:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
