import logging
import zipfile
import io
from uuid import UUID
from typing import Tuple

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
    async def download_zip(file_paths: Tuple) -> io.BytesIO:
        """Скачивание с хранилища файлов и архивировать на лету"""
        memory_file = io.BytesIO()
        # Создание архива с использованием асинхронных методов
        with zipfile.ZipFile(memory_file, "w") as zipf:
            for file_path in file_paths:
                file_down = str(file_path[0])
                name_arh = file_path[1]
                logging.debug(
                    f'Добавляем в архив файл из хранилища'
                    f' {file_down} по именем {name_arh}')
                logging.info(f'{file_down}')
                data = [f async for f in s3.list(file_down)]
                logging.debug(data)
                content = await s3.download(file_down)
                zipf.writestr(zinfo_or_arcname=name_arh, data=content)
        memory_file.seek(0)
        return memory_file

    @staticmethod
    async def download_tar(file_paths: tuple) -> io.BytesIO:
        # https://pymotw.com/2/tarfile/
        memory_file = io.BytesIO()
        archive = tarfile.open(fileobj=memory_file, mode="w")
        try:
            for file_path in file_paths:
                logging.debug(f'Добавляем в архив файл '
                              f'из хранилища {file_path}')
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
                logging.debug(f'Скачиваем архив файл из '
                              f'хранилища {file_path}')
                content = await s3.download(str(file_path[0]))
                archive.writestr(content, file_path[1])
        memory_file.seek(0)
        return memory_file

    @staticmethod
    async def download_s3(file_path: tuple, file_name: str | None
                          ) -> io.BytesIO:
        """Скачивание без архивирования"""
        if file_name is None:
            file_download = file_path
        else:
            file_download = file_path[0]

        logging.debug(f' Скачиваем файл с хранилища - {file_download}')
        content = await s3.download(file_download)
        return io.BytesIO(content)

    async def download(self, path_file: str,
                       compression: str, id_user: UUID) -> StreamingResponse:
        """Скачивание файла/файлов с хранилища """
        try:
            file_name, path = check_path_file(path_file=path_file)

            statement = (
                sql.select(Files.unique_id, Files.file_name).
                join(Paths).
                where(sql.and_(
                    Paths.path == path,
                    Files.is_downloadable,
                    Files.account_id == id_user)))
            if file_name is not None:  # добавляем условие поиска
                statement = statement.where(Files.file_name == str(file_name))
            files = (await (self.session.execute(statement))).fetchall()
            logging.debug(f'path = {path}')
            logging.debug(f'SQL = {statement}')
            logging.debug(f'----- files = {files}')
            logging.debug(f'----- file = {file_name}')
            zip_filename = f'download.{compression}'
            match compression:
                case 'zip':
                    memory_file = await self.download_zip(files)
                case 'tar':
                    memory_file = await self.download_tar(files)
                case '7z':
                    memory_file = await self.download_7z(files)
                case None:
                    memory_file = await self.download_s3(files, file_name)
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
