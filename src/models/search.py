from typing import List

from pydantic import BaseModel

from src.models.base import FileConfig


class ResponseSearch(FileConfig):
    pass


class ResponseSearchAll(BaseModel):
    mathes: List[ResponseSearch]
