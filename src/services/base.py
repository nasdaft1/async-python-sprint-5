from sqlalchemy.ext.asyncio import AsyncSession
from services.register import Register
from services.auth import Auth
from services.ping import Ping
from services.upload import UpLoad
from services.download import Download
from services.filesall import FilesAll
from services.status import Status
from services.search import Search
from services.revisions import Revisions


class ServiceLink(Register, Auth, Ping,
                  UpLoad, Download, FilesAll,
                  Status, Search, Revisions):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
