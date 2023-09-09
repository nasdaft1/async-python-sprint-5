import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from fastapi_users.authentication import CookieTransport

from src.models.auth import username_query, password_query
from src.models.files import ResponseFiles
from src.models.ping import ResponsePing
from src.models.register import ResponseRegister
from src.models.revisions import ResponseRevisions
from src.models.search import ResponseSearchAll
from src.models.status import ResponseStatus
from src.models.upload import ResponseUpLoad
from src.db.db import get_session
from src.services.base import ServiceLink
import src.services.authorization as auto
from src.core.config import config_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

cookie_transport = CookieTransport(
    cookie_name='token',
    cookie_max_age=config_token.cookie_max_age)


@router.get('/', description='Стартовая страница файлового хранилища')
async def read_root():
    logging.info('Добро пожаловать в Файловое хранилище')
    return 'Добро пожаловать в Файловое хранилище'


@router.get('/ping', description='ping_service',
            response_model=ResponsePing)
async def ping_service(
        *, db: AsyncSession = Depends(get_session)) -> ResponsePing:
    return await ServiceLink(db).access_ping()


@router.post('/register', description='register_user')
async def register_user(
        *,
        username: str = username_query,
        password: str = password_query,
        db: AsyncSession = Depends(get_session)) -> ResponseRegister:
    return await ServiceLink(db).register_user(
        user=username, password=password)


# http://127.0.0.1:8080/api/v1/auth?username=weqwe2qw&password=dF12k$O(
# weqwe2qw
# dF12k$O(
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ3ZXF3ZTJxdyIsInNjb3BlcyI6ImYyOGNmZTc5LTVjMTYtNDJiZC1iZTliLWYwNmI0ZjRlOGQwNSIsImV4cCI6MTY5NDIxNjAxN30
@router.post('/auth', description='auth_user')
async def auth_user(
        *,
        username: str = username_query,
        password: str = password_query,
        db: AsyncSession = Depends(get_session),
        response: Response):
    uuid_id = await ServiceLink(db).access_user(
        username=username, password=password)
    token = auto.create_access_token(username=username, uuid_id=uuid_id)
    # создаем cookes и отправляем его
    response.set_cookie(key=config_token.token_name,
                        value=token,
                        httponly=True,  # защищает cookie от JavaScript
                        max_age=config_token.cookie_max_age)
    return 'Токен сохранен в cookes'


@router.get('/files/', description='files_statistic')
async def files_statistic(
        *,
        id_user: UUID = Depends(auto.get_current_user),
        db: AsyncSession = Depends(get_session)) -> ResponseFiles:
    return await ServiceLink(db).files(id_user=id_user)


@router.post('/files/upload', description='files_upload')
async def files_upload(
        *, file: Annotated[UploadFile, File(
            description='A file read as UploadFile')],
        path: str,
        id_user: UUID = Depends(auto.get_current_user),
        db: AsyncSession = Depends(get_session)) -> ResponseUpLoad | str:
    return await ServiceLink(db).upload(
        path_file=path, file=file, id_user=id_user)


@router.get('/files/download', description='files_download')
async def files_download(
        *, path: str,
        compression: Literal['zip', '7z', 'tae'] = None,
        id_user: UUID = Depends(auto.get_current_user),
        db: AsyncSession = Depends(get_session)) -> StreamingResponse:
    if compression is not None:
        compression = compression.lower()
    return await ServiceLink(db).download(
        path_file=path, compression=compression, id_user=id_user)


@router.get('/user/status', description='user_status')
async def user_status(
        *, id_user: UUID = Depends(auto.get_current_user),
        db: AsyncSession = Depends(get_session)) -> ResponseStatus:
    return await ServiceLink(db).status(id_user)


@router.post('/files/search', description='files_search')
async def files_search(
        *, id_user: UUID = Depends(auto.get_current_user),
        path: str = None,
        extension: str = None,
        order_by: Literal['file', 'name', 'created_at',
        'path', 'size', 'is_downloadable'] = None,
        limit: int = 0,

        db: AsyncSession = Depends(get_session)) -> ResponseSearchAll:
    logging.debug(f'Search > path = {path} extension='
                  f'{extension} order_by={order_by} limit={limit}')

    return await ServiceLink(db).search(
        id_user=id_user,
        path=path,
        extension=extension,
        order_by=order_by,
        limits=limit)


@router.post('/files/revisions', description='files_revisions')
async def files_revisions(
        *, path: str, limit: int = 0,
        id_user: UUID = Depends(auto.get_current_user),
        db: AsyncSession = Depends(get_session)) -> ResponseRevisions:
    return await ServiceLink(db).revisions(
        path=path, path_limit=limit, id_user=id_user)
