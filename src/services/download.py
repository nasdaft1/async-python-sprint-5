import logging
import zipfile
import io
from uuid import UUID

from py7zr import SevenZipFile
import tarfile
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql
from fastapi import status
from fastapi.responses import StreamingResponse

from src.db.models import Files, Paths
from src.db.db import s3
from src.services.util import check_path_file


class Download:
    session: AsyncSession

    @staticmethod
    async def download_zip(file_paths: tuple) -> io.BytesIO:
        """Скачивание с хранилища файлов и архивировать на лету"""
        memory_file = io.BytesIO()
        # Создание архива с использованием асинхронных методов
        with zipfile.ZipFile(memory_file, "w") as zipf:
            for file_path in file_paths:
                logging.debug(
                    f'Добавляем в архив файл из хранилища'
                    f' {file_path[0]} по именем {file_path[1]}')
                content = await s3.download(str(file_path[0]))
                zipf.writestr(zinfo_or_arcname=file_path[1], data=content)
        memory_file.seek(0)
        return memory_file

    @staticmethod
    async def download_tar(file_paths: tuple) -> io.BytesIO:
        # https://pymotw.com/2/tarfile/
        memory_file = io.BytesIO()
        archive = tarfile.open(fileobj=memory_file, mode="w")
        try:
            for file_path in file_paths:
                logging.debug(f'Скачивается с хранилища {file_path}')
                file_uuid = str(file_path[0])
                file_name = str(file_path[1])
                content = await s3.download(file_uuid)
                info = tarfile.TarInfo(file_name)
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
        finally:
            archive.close()
        memory_file.seek(0)
        return memory_file

    @staticmethod
    async def download_7z(file_paths: tuple) -> io.BytesIO:
        memory_file = io.BytesIO()
        with SevenZipFile(memory_file, 'w') as archive:
            for file_path in file_paths:
                logging.debug(f'Скачивается с хранилища {file_path}')
                content = await s3.download(str(file_path[0]))
                archive.writestr(content, file_path[1])
        memory_file.seek(0)
        return memory_file

    async def download_s3(self, file_path: tuple) -> io.BytesIO:
        """Скачивание без архивирования"""
        logging.debug(f' Скачиваем файл с хранилища - {file_path[0][0]}')
        content = await s3.download(file_path[0][0])
        return io.BytesIO(content)

    async def check_path(self, path: str, id_user: UUID) -> str | None:
        """
        Поиск и получение UUID каталога(пути)
        :param path: имя полного пути
        :return:
        """
        statement = (
            sql.select(Paths.id_path, Paths.path).
            where(sql.and_(
                Paths.path == path,
                Paths.is_downloadable,
                Paths.account_id == id_user
            )).limit(1))
        result_path = (await (self.session.execute(statement))).one_or_none()
        if result_path is None:
            raise ValueError(f'Нет данного каталога path={path}')
        logging.debug(f'result_path={result_path}')
        return result_path[0]

    async def check_file(self, path_uuid: str, path: str,
                         file: str | None, id_user: UUID) -> tuple | None:
        """
        Поиск файлов в каталоге
        :param path_uuid: UUID пути
        :param path: имя пути к файлу
        :param file: имя файла | None нет файла
        :param id_user: UUID пользователя
        :return:
        """
        if file is None:
            statement = (
                sql.select(Files.id_file, Files.file_name).
                where(sql.and_(
                    Files.id_path == path_uuid,
                    Files.is_downloadable,
                    Files.account_id == id_user)))
            result_file = (await (self.session.execute(statement))).fetchall()
        else:
            statement = (
                sql.select(Files.id_file, Files.file_name).
                where(sql.and_(
                    Files.id_path == path_uuid,
                    Files.file_name == file,
                    Files.is_downloadable,
                    Files.account_id == id_user)))
            result_file = (await (self.session.execute(statement))).fetchall()

        if result_file is None:
            raise ValueError(f'Нет файлов в каталоге path={path}')
        for index in result_file:
            logging.debug(f'Найдены в папке {path} - {path_uuid} '
                          f'файлы {index[0]} {index[1]}')
        return tuple(result_file)

    async def download(self, path_file: str,
                       compression: str, id_user: UUID) -> StreamingResponse:
        """Скачивание файла/файлов с хранилища """
        try:
            file_name, paths = check_path_file(path_file=path_file)
            if paths is None:
                raise ValueError(f'Неверный формат path={path_file}')
            path_uuid = await self.check_path(paths[0], id_user)
            file_paths = await self.check_file(
                path_uuid, paths[0], file_name, id_user)
            zip_filename = f'download.{compression}'
            match compression:
                case 'zip':
                    memory_file = await self.download_zip(file_paths)
                case 'tar':
                    memory_file = await self.download_tar(file_paths)
                case '7z':
                    memory_file = await self.download_7z(file_paths)
                case None:
                    memory_file = await self.download_s3(file_paths)
                    zip_filename = file_name
                case _:
                    raise ValueError(f'Неверный тип compression={compression}')

            headers = {"Content-Disposition": f"attachment; "
                                              f"filename={zip_filename}"}
            logging.debug(headers)
            return StreamingResponse(content=memory_file,
                                     media_type="application/octet-stream",
                                     headers=headers)
        except ValueError as error:
            logging.error(error)
            return StreamingResponse(status_code=status.HTTP_400_BAD_REQUEST)
