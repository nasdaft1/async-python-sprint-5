import datetime
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql
from fastapi import UploadFile

from src.db.models import Files, Paths
from src.db.db import s3
from src.models.upload import ResponseUpLoad
from src.services.util import check_path_file, add_id


class UpLoad:
    session: AsyncSession

    async def save_file_db(self, file_name: str | None,
                           path: str, file: UploadFile,
                           id_user: UUID) -> ResponseUpLoad:
        """
        Запись данных в таблицу БД с файлами
        :param file_name: имя файла | None имя закачиваемого файла
        :param path: путь к файлу
        :param file: файл с данными
        :param id_user: UUID создавший файлы
        """
        name_uuid = ''
        create_at = ''
        if file_name is None:
            file_name = file.filename  # имя скачиваемого
            logging.debug(f'В path_file не указан file наследуем '
                          f'от скачиваемого {file_name}')
        # Находим UUID каталога
        statement = (
            sql.select(Paths.id_path).where(
                sql.and_(
                    Paths.path == path,
                    Paths.is_downloadable,
                    Paths.account_id == id_user
                )).limit(1))
        id_path = (await (self.session.execute(statement))).one_or_none()[0]
        logging.debug(f' file_name:{file_name}, id_file:{id_path}')

        statement = (
            sql.select(Files.id_path).
            where(sql.and_(
                Files.file_name == file_name,
                Files.id_path == str(id_path),
                Files.is_downloadable,
                Files.account_id == id_user
            )).limit(1))
        result = (await (self.session.execute(statement))).one_or_none()
        logging.debug(f' ----------- {result}')
        if result is None:
            logging.debug(f'файла {file_name} нет в хранилище {result}')

            obj = Files(id_file=await add_id(session=self.session),
                        file_name=file_name,
                        id_path=str(id_path),
                        hash='',
                        account_id=str(id_user))
            self.session.add(obj)
            await self.session.commit()
            logging.debug(f'файла {file_name} нет в хранилище, добавлен '
                          f'uuid={obj.id_file}')
            name_uuid = str(obj.id_file)
            create_at = obj.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')

        else:
            logging.debug(f'файла {file_name} есть в хранилище и будет '
                          f'переписан uuid={result[0]}')
            data_time_create = datetime.datetime.now()
            create_at = data_time_create.strftime('%Y-%m-%dT%H:%M:%SZ')
            name_uuid = str(result[0])
            # корректируем дату создания файла
            statement = (
                sql.update(Files).
                where(Files.id_file == name_uuid).
                values(created_at=data_time_create))
            await (self.session.execute(statement))

        # запись в облако
        file_data = file.file.read()
        await s3.upload(name_uuid, file_data)
        files = [f async for f in s3.list(name_uuid)]
        logging.debug(files[0])
        # вносим в таблицу HASH, Size
        statement = (
            sql.update(Files).
            where(Files.id_file == name_uuid).
            values(size=files[0].size, hash=files[0].e_tag).
            returning(Files.size, Files.hash))
        res = (await (self.session.execute(statement))).fetchone()
        await self.session.commit()

        logging.debug(f' Получаем из файла = {name_uuid} хранилища '
                      f'size={files[0].size} , hash={files[0].e_tag} {res}')
        return (ResponseUpLoad(
            id=name_uuid,
            name=file_name,
            created_ad=create_at,
            path=path,
            size=files[0].size,
            is_downloadable=True))

    async def upload(self, path_file: str,
                     file: UploadFile,
                     id_user: UUID) -> ResponseUpLoad | str:
        """
        Проверка записи о файле в БД Postgres
        Добавляем каталоги в таблицу БД
        """
        # Разбивка path_file

        file_name, paths = check_path_file(path_file)
        if paths is None:
            # неверный формат ввода path_file
            return 'Error input path'
        for index in range(len(paths)):
            path = paths[index]
            logging.debug(f'Проверяем наличие каталога {path}')
            # Проверяем наличие каталога
            statement = (
                sql.select(Paths.id_path).
                where(sql.and_(
                    Paths.path == path,
                    Paths.is_downloadable,
                    Paths.account_id == id_user
                )).limit(1))
            result = (await (self.session.execute(statement))).one_or_none()
            if result is None:
                # Создаем запись в БД с каталогом

                obj = Paths(id_path=await add_id(session=self.session),
                            path=path,
                            account_id=id_user)
                self.session.add(obj)
                await self.session.commit()
                logging.debug(f'Добавлена папка={obj.path} в '
                              f'БД uuid={obj.id_path}')
            else:
                logging.debug(f'В БД уже есть папка= {path}')
                break
        # добавляем данные о файле в таблицу БД
        return await self.save_file_db(
            file_name=file_name,
            path=paths[0],
            file=file, id_user=id_user)
