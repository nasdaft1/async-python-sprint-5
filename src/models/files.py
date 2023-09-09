from typing import List

from pydantic import BaseModel

from src.models.base import FileConfig


class ResponseFilesOne(FileConfig):
    pass


class ResponseFiles(BaseModel):
    account_id: str
    files: List[ResponseFilesOne]
