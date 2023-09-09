from sqlalchemy.ext.asyncio import AsyncSession
from src.services.register import Register
from src.services.auth import Auth
from src.services.ping import Ping
from src.services.upload import UpLoad
from src.services.download import Download
from src.services.filesall import FilesAll
from src.services.status import Status
from src.services.search import Search
from src.services.revisions import Revisions


class ServiceLink(Register, Auth, Ping,
                  UpLoad, Download, FilesAll,
                  Status, Search, Revisions):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
