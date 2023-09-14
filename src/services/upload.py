from datetime import datetime
import logging
from uuid import UUID
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql
from fastapi import UploadFile
from pydantic import BaseModel

from db.models import Files, Paths
from db.db import s3
from models.upload import ResponseUpLoad
from services.util import check_path_file, add_id


class Data(BaseModel):
    unique_id: str | None = None  # уникальный индекс между путем и файлом
    file_name: str | None = None
    path: str
    id_path: str | None = None
    id_user: str | None = None
    id_file: UUID | None = None
    file_hash: str | None = None
    file_size: int | None = None
    file_uuid: str | None = None
    file_date: datetime = sql.func.now()
    storage_file: str | None = None  # имя хранения в облаке


class UpLoad:
    session: AsyncSession

    @staticmethod
    async def storage_upload(file: UploadFile, file_name: str | None
                             ) -> Tuple[str, str, datetime]:
        """
        Запись файла в облачное хранилище
        и получение size:str, hash:str записанного файла туда
        :param file: ссылка на файл который будет записываться
        :param file_name: имя файла как будет называться в хранилище
        :return: file -> size:str, hash:str, file_modific:datetime
        """

        # запись в облако
        file_data = file.file.read()
        await s3.upload(file_name, file_data)
        data = [f async for f in s3.list(file_name)][0]
        logging.debug(data)
        return data.size, data.e_tag, data.last_modified

    async def file_create(self, args: Data) -> None:
        obj = Files(
            unique_id=args.unique_id,
            file_name=args.file_name,
            id_path=args.id_path,
            hash=args.file_hash,
            size=args.file_size,
            account_id=args.id_user)
        logging.info(obj)
        self.session.add(obj)
        await self.session.commit()

    async def file_update(self, args: Data) -> None:
        file_name_update = sql.update(Files).where(
            Files.id_file == args.id_file).values(
            file_name=args.file_name,
            hash=args.file_hash,
            size=args.file_size)
        await self.session.execute(file_name_update)

    async def save_file_db(self, file: UploadFile,
                           args: Data) -> ResponseUpLoad:
        """ Запись данных в таблицу БД с файлами. """
        sql_id_file = (sql.select(Files.unique_id).where(sql.and_(
            Files.file_name == args.file_name,
            Files.id_path == args.id_path)).limit(1))
        logging.debug(sql_id_file)

        id_file = (await self.session.execute(sql_id_file)).fetchone()
        if id_file is None:
            args.unique_id = await add_id(session=self.session)
        else:
            args.unique_id = str(id_file[0])
        # запись в хранилище
        args.file_size, args.file_hash, args.file_date = await \
            self.storage_upload(file, args.unique_id)
        if id_file is None:
            await self.file_create(args)
        else:
            args.id_file = str(id_file[0])
            await self.file_update(args)
        await self.session.commit()
        return (ResponseUpLoad(
            id=args.unique_id,
            name=args.file_name,
            created_ad=args.file_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            path=args.path,
            size=args.file_size,
            is_downloadable=True))

    async def upload(self, path_file: str, file: UploadFile,
                     id_user: str) -> ResponseUpLoad | str:
        """
        Проверка записи о файле в БД Postgres
        Добавляем каталоги в таблицу БД
        """
        args = Data
        args.id_user = id_user
        args.file_name, args.path = check_path_file(path_file)
        if args.file_name is None:
            args.file_name = file.filename  # имя скачиваемого
            logging.debug(f'В path_file не указан file наследуем '
                          f'от скачиваемого {args.file_name}')
        exists_query = (sql.select(Paths.id_path).where(
            sql.and_(Paths.path == args.path,
                     Paths.is_downloadable,
                     Paths.account_id == args.id_user))).limit(1)
        id_path = (await self.session.execute(exists_query)).fetchone()
        # Проверяем наличие каталога
        if id_path is None:
            # # Создаем запись в БД с каталогом
            unique_id = await (add_id(session=self.session))
            obj = Paths(unique_id=unique_id,
                        path=args.path, account_id=args.id_user)

            self.session.add(obj)
            await self.session.commit()
            args.id_path = str(obj.id_path)
            logging.debug(f'Добавлена папка={args.path} ')
        else:
            args.id_path = str(id_path[0])
            logging.debug(f'В БД уже есть папка= {args.id_path} ')
            # приведение в общий формат поиска и добавления
        # добавляем данные о файле в таблицу БД

        return await self.save_file_db(file=file, args=args)
