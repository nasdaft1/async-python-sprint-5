from typing import List

from pydantic import BaseModel

from models.base import FileConfig


class ResponseSearch(FileConfig):
    pass


class ResponseSearchAll(BaseModel):
    mathes: List[ResponseSearch]
