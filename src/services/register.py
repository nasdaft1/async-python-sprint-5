import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.register import ResponseRegister
from db.models import Access


class Register:
    session: AsyncSession

    async def register_user(self, user: str, password: str
                            ) -> ResponseRegister:
        """
        Проверка есть зарегистрированные user
        если нет его регистрация в DB
        :param user: логин
        :param password: пароль
        :return: результат операции
        """
        try:
            obj = Access(user=user, password=password)
            self.session.add(obj)
            await self.session.commit()
            logging.debug(f'user={user} зарегистрирован')
            return ResponseRegister(msg='Пользователь зарегистрирован')
        except SQLAlchemyError as error:
            logging.debug(f'user={user} уже зарегистрирован {error}')
            return ResponseRegister(msg='Пользователь уже зарегистрирован')
