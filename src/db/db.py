import logging

from s3 import S3Client

from src.core.config import config, config_storage
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

db_config = f'postgresql+asyncpg://{config.postgres_user}' \
            f':{config.postgres_password}@{config.postgres_host}' \
            f':{config.postgres_port}/{config.postgres_db}'

# https://github.com/mrslow/yandex-s3
s3 = S3Client(access_key=config_storage.aws_access_key_id,
              secret_key=config_storage.aws_secret_access_key,
              region=config_storage.region,
              s3_bucket=config_storage.bucket_name)

logging.debug(f'Connect DB= {db_config}')

engine = create_async_engine(db_config, echo=config.postgres_echo, future=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
