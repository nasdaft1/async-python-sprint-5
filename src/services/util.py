import logging
import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.db.models import UniqueUUID

session: AsyncSession


def check_path_file(path_file: str) -> [str | None, str | None]:
    """
    Проверка и получение путей и файла
    :param path_file: /xx/yy.y
    :return: file:str|None, paths:[]| None
    """
    file = path_file[path_file.rfind('/') + 1:]
    path = path_file[:path_file.rfind('/') + 1]

    try:
        match len(file) - file.rfind('.'), file.count('.'):
            case 1, 0:
                file = None
            case _, 0:
                raise ValueError('Не может быть названия файла без точки')
            case 1, 1:
                raise ValueError(
                    'Не может быть название файла закачиваться на .')
        if path.count('//') == 1 or path[0] != '/':
            raise ValueError('Не верный путь // or not /')
        if path.count('.') != 0:
            raise ValueError('Error путь содержит (.) запрещенный символ')
    except ValueError as error:
        path = None
        file = None
        logging.error(error)
    logging.debug(f'file={file} \t paths={path}')
    return file, path


async def add_id(session: AsyncSession, attempt: int = 1) -> UUID:
    """Для получения уникального ключа"""
    # Создаем запись в БД с каталогом
    index = 0
    while True:

        key = uuid.uuid4()
        obj = UniqueUUID(id=key)

        try:
            session.add(obj)
            await session.commit()
            logging.debug(
                f'Сгенерировано уникальное значение для двух таблиц {key}')
            break
        except SQLAlchemyError as error:
            logging.debug(f'Ошибка уникальности UUID {error}')
        index += 1
        # для избегания зацикливания
        if index > attempt:
            raise ValueError('Не может быть с генерирован уникальный UUID')
    return key
