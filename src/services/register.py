import logging

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.models.register import ResponseRegister
from src.db.models import Access


class Register:
    session: AsyncSession

    async def register_user(self, user: str, password: str) -> ResponseRegister:
        """
        Проверка есть зарегистрированные user
        если нет его регистрация в DB
        :param user: логин
        :param password: пароль
        :return: результат операции
        """
        statement = (sql.select(Access).where(Access.user == user).limit(1))
        result = await (self.session.execute(statement))
        if result.one_or_none() is None:
            self.session.add(Access(user=user, password=password))
            await self.session.commit()
            logging.debug(f'user={user} зарегистрирован')
            return ResponseRegister(msg=f'user={user} зарегистрирован')
        logging.debug(f'user={user} уже зарегистрирован')
        return ResponseRegister(msg=f'user={user} уже зарегистрирован')
