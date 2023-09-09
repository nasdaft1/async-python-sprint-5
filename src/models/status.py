from pydantic import BaseModel
from typing import Dict


class ResponseStatusFiles(BaseModel):
    allocated: str
    used: str
    files: int


class ResponseStatus(BaseModel):
    account_id: str
    info: Dict
    folders: Dict
