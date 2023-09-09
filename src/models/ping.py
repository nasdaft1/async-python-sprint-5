from typing import Union

from pydantic import BaseModel


class ResponsePing(BaseModel):
    db: Union[float, str] = None
    cache: Union[float, str] = None
    nginx: Union[float, str] = None
    storage: Union[float, str] = None
