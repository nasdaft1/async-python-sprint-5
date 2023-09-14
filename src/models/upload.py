from models.base import Auth, FileConfig
from uuid import UUID


class RequestUpLoad(Auth):
    path_file: str


class ResponseUpLoad(FileConfig):
    id: str
    name: str
    created_ad: str
    path: str
    size: int
    is_downloadable: bool
