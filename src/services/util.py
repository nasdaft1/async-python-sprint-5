import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.db.models import UniqueUUID

session: AsyncSession


def check_path_file(path_file: str) -> [str | None, dict | None]:
    """
    Проверка и получение путей и файла
    :param path_file: /xx/yy.y
    :return: file:str|None, paths:[]| None
    """

    file = path_file[path_file.rfind('/') + 1:]
    path = path_file[:path_file.rfind('/') + 1]
    paths = []
    try:
        match len(file) - file.rfind('.'), file.count('.'):
            case 1, 0:
                raise ValueError('Не указано название файла')
            case _, 0:
                raise ValueError('Не может быть названия файла без точки')
            case 1, 1:
                raise ValueError(
                    'Не может быть название файла закачиваться на .')
    except ValueError as error:
        logging.error(error)
        file = None
    try:
        while True:
            if path.count('//') == 1 or path[0] != '/':
                raise ValueError('Не верный путь // or not /')
            path = path[:path.rfind('/')]
            if path.count('/') == 0:
                paths.append('/')
                break
            paths.append(path)
    except ValueError as error:
        paths = None
        logging.error(error)

    logging.debug(f'file={file} \t paths={paths}')
    return file, paths


async def add_id(session: AsyncSession, attempt: int = 1) -> str:
    """Для получения уникального ключа"""
    # Создаем запись в БД с каталогом
    index = 0
    while True:

        key = str(uuid.uuid4())
        obj = UniqueUUID(id=str(key))

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
