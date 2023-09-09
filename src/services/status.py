import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.db.models import Files, Paths
from src.models.status import ResponseStatus, ResponseStatusFiles


class Status:
    session: AsyncSession

    async def status(self, id_user: UUID) -> ResponseStatus:
        """
        Статус файлов
        :param id_user: UUID создавший файлы
        :return: формат данных
        """
        statement = (
            sql.select(
                Files.account_id,
                Paths.path,
                sql.func.sum(Files.size).
                over(partition_by=(
                    Paths.path, Files.account_id)).label('file_sum'),
                sql.func.sum(Files.size).
                over(partition_by=Paths.path).label('all_sum'),
                sql.func.count(Files.size).
                over(partition_by=(
                    Files.account_id, Paths.path)).label('f_count'),
            ).join(Paths)).group_by(
            Paths.path, Files.size, Files.account_id).distinct()
        logging.debug(statement)
        result_folders = (await (self.session.execute(statement))).all()

        logging.debug(result_folders)
        info = {}
        folders = {}
        for folder in result_folders:
            logging.debug(folder)
            if folder[0] == id_user:
                folders[folder[1]] = ResponseStatusFiles(
                    allocated=str(folder[3]),
                    used=str(folder[2]),
                    files=folder[4])
        return ResponseStatus(
            account_id=str(id_user),
            info=info,
            folders=folders
        )
