import logging
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Header
from jose import JWTError, jwt

from src.core.config import config_token


def create_access_token(username: str, uuid_id: UUID | None):
    """Создаем token c временем пользования"""
    if uuid_id is None:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password")
    data = {"sub": username, "scopes": str(uuid_id)}
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=config_token.access_token_expire_minutes)
    logging.debug(f' now ={datetime.utcnow()} end date token {expire}')

    to_encode.update({"exp": expire})
    logging.debug(to_encode)
    encoded_jwt = jwt.encode(to_encode, config_token.secret_key,
                             algorithm=config_token.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Header(None)) -> UUID | None:
    payload = {}
    logging.debug(f'{config_token.token_name}={token}')
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": config_token.token_name})
    try:
        payload = jwt.decode(token, config_token.secret_key,
                             algorithms=[config_token.algorithm])
        is_valid = jwt.decode(token, config_token.secret_key,
                              algorithms=[config_token.algorithm],
                              options={"verify_signature": False})
        token_scopes = UUID(payload.get("scopes", None))
        if token_scopes is None:
            raise credentials_exception
    except JWTError as error:
        logging.debug(error)
        raise credentials_exception
    logging.info(f'token jwt is_valid={is_valid}')
    return token_scopes
