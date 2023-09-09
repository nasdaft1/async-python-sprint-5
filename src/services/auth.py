import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.db.models import Access


class Auth:
    session: AsyncSession

    async def access_user(self, username: str, password: str) -> UUID | None:
        """
        Проверка есть зарегистрированные user
        если нет его регистрация в DB
        :param username: логин
        :param password: пароль
        :return: код UUID пользователя | None нет доступа
        """
        statement = (sql.select(Access.id).where(
            Access.user == username,
            Access.password == password).limit(1))
        result = (await (self.session.execute(statement))).one_or_none()

        if result is None:
            logging.debug(f'user={username} доступ закрыт')
            return None
        logging.debug(f'user={username} Authorization: Bearer <{result[0]}>')
        return result[0]
