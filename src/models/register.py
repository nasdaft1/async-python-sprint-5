from pydantic import BaseModel


class ResponseRegister(BaseModel):
    msg: str
