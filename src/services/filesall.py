import logging

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.db.models import Files, Paths, UUID
from src.models.files import ResponseFiles, ResponseFilesOne


class FilesAll:
    session: AsyncSession

    async def files(self, id_user: UUID) -> ResponseFiles:
        """
        Выводит список файлов
        :param id_user: UUID создавший файлы
        :return:
        """
        statement = (
            sql.select(Files.id_file,
                       Files.file_name,
                       Files.created_at,
                       Paths.path,
                       Files.size,
                       Files.is_downloadable,
                       Files.hash,
                       Files.modified_at,
                       Files.id_path).
            join(Paths)).where(Files.account_id == id_user)
        logging.debug(f' Запрос SQL={statement}')
        result = (await (self.session.execute(statement))).all()
        logging.debug(result)
        files_list = []
        for line in result:
            files_list.append(ResponseFilesOne(
                id=str(line[0]),
                name=line[1],
                created_ad=line[2].strftime('%Y-%m-%dT%H:%M:%SZ'),
                path=line[3],
                size=int(line[4]),
                is_downloadable=line[5]))
        return ResponseFiles(
            account_id=str(id_user),
            files=files_list)
