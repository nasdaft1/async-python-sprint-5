import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.db.models import Files, Paths
from src.models.revisions import ResponseRevisions, ResponseRevisionsOne


class Revisions:
    session: AsyncSession

    async def revisions(self, path: str,
                        path_limit: int | None,
                        id_user: UUID) -> ResponseRevisions:
        """
        Вернуть информацию об изменениях файла по заданным параметрам.
        :param path: путь к файлам text | uuid
        :param path_limit: длина выводимого списка
        :param id_user: UUID создавший файлы
        :return:
        """

        if path_limit < 1:
            path_limit = None
        statement = (
            sql.select(Files.id_file,
                       Files.file_name,
                       Files.created_at,
                       Paths.path,
                       Files.size,
                       Files.is_downloadable,
                       Files.id_path,
                       Files.hash,
                       Files.modified_at,
                       Paths.id_path,
                       Files.account_id).
            join(Paths).where(sql.and_(
                Files.account_id == id_user,
                sql.or_(Paths.path == path,
                        sql.cast(Paths.id_path, sql.String) == path)
            ))).limit(path_limit).order_by(sql.desc(Files.created_at))
        logging.debug(f' Запрос SQL={statement}')
        result = (await (self.session.execute(statement))).all()
        logging.debug(result)
        files = []
        for files_list in result:
            files.append(ResponseRevisionsOne(
                id=str(files_list[0]),
                name=files_list[1],
                created_ad=files_list[2].strftime('%Y-%m-%dT%H:%M:%SZ'),
                path=files_list[3],
                size=files_list[4],
                is_downloadable=files_list[5],
                rev_id=str(files_list[6]),
                hash=files_list[7],
                modified_at=files_list[8].strftime('%Y-%m-%dT%H:%M:%SZ')
            ))
        return ResponseRevisions(
            revisions=files)
