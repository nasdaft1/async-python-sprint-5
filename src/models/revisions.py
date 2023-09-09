from typing import List

from pydantic import BaseModel

from src.models.base import FileConfig


class ResponseRevisionsOne(FileConfig):
    rev_id: str = None
    hash: str = None
    modified_at: str


class ResponseRevisions(BaseModel):
    revisions: List[ResponseRevisionsOne]
