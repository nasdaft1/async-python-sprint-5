import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sql

from src.db.models import Files, Paths
from src.models.search import ResponseSearch, ResponseSearchAll


class Search:
    session: AsyncSession

    async def search(self, id_user: UUID,
                     path: str | None,
                     extension: str | None,
                     order_by: str | None,
                     limits: int | None
                     ) -> ResponseSearchAll:
        """
        :param id_user:  uuid пользователя
        :param path:  Поиск по path
        :param extension: Поиск по file
        :param order_by: Сортировка по одному из полей
        :param limits: Длина вывода данных в результате
        :return:
        """
        if limits < 1:
            limits = None
        statement = (
            sql.select(Files.id_file.label('file'),
                       Files.file_name.label('name'),
                       Files.created_at.label('created_at'),
                       Paths.path.label('path'),
                       Files.size.label('size'),
                       Files.is_downloadable.
                       label('is_downloadable')
                       ).join(Paths).where(
                Files.account_id == id_user).limit(limits).order_by(order_by))

        if path is not None:
            statement = statement.where(Paths.path.regexp_match(path))
        if extension is not None:
            statement = statement.where(
                Files.file_name.
                regexp_match(extension))
        result = (await (self.session.execute(statement))).all()
        logging.debug(result)
        response = []
        for index in result:
            response.append(ResponseSearch(
                id=str(index[0]),
                name=index[1],
                created_ad=index[2].strftime('%Y-%m-%dT%H:%M:%SZ'),
                path=index[3],
                size=int(index[4]),
                is_downloadable=index[5],
            ))
        return ResponseSearchAll(mathes=response)
