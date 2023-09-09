from pydantic import BaseModel


class Auth(BaseModel):
    token: str = None


class FileConfig(BaseModel):
    id: str = None
    name: str = ''
    created_ad: str = None
    path: str = '/'
    size: int = 0
    is_downloadable: bool = False
