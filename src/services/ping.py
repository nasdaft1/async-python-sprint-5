import logging
import time
from functools import wraps

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from models.ping import ResponsePing
from db.models import Access
from db.db import s3
from core.config import config


def timing_decorator(func):
    """ Асинхронный декоратор для расчета времени доступа."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            start_time = time.time()
            await func(*args, **kwargs)
            end_time = time.time()
            execution_time = round((end_time - start_time), 3)
            logging.debug(f"{func.__name__} took {execution_time} "
                          f"seconds to execute.")
        except Exception as error:
            logging.error(error)
            return 'error'
        return execution_time

    return wrapper


class Ping:
    session: AsyncSession

    @timing_decorator
    async def time_test_db(self) -> None:
        """Время доступа к БД"""
        statement = (sql.select(Access.id))
        result = (await (self.session.execute(statement))).scalars()

    @timing_decorator
    async def time_test_s3(self) -> None:
        """Время доступа к облачному хранилищу"""
        files = [f async for f in s3.list('test')]
        logging.debug(files)

    @timing_decorator
    async def time_test_nginx(self) -> None:
        """Время доступа к nginx"""
        url = f'http://{config.app_host}:{config.nginx_port}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logging.debug(response.status.real)

    async def access_ping(self) -> ResponsePing:
        """
        Проверка доступа к ресурсам
        :return: Время доступа до каждого ресурса
        """
        return ResponsePing(
            db=await self.time_test_db(),
            nginx=await self.time_test_nginx(),
            storage=await self.time_test_s3())
