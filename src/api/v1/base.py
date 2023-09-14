import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from fastapi_users.authentication import CookieTransport

from models.auth import username_query, password_query
from models.files import ResponseFiles
from models.ping import ResponsePing
from models.register import ResponseRegister
from models.revisions import ResponseRevisions
from models.search import ResponseSearchAll
from models.status import ResponseStatus
from models.upload import ResponseUpLoad
from db.db import get_session
from services.base import ServiceLink
import services.authorization as auto
from core.config import config_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

cookie_transport = CookieTransport(
    cookie_name='token',
    cookie_max_age=config_token.cookie_max_age)


@router.get('/', description='Стартовая страница файлового хранилища')
async def read_root() -> str:
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


@router.post('/auth', description='auth_user')
async def auth_user(
        response: Response,
        username: str = username_query,
        password: str = password_query,
        db: AsyncSession = Depends(get_session)):
    uuid_id = await ServiceLink(db).access_user(
        username=username, password=password)
    token = auto.create_access_token(username=username, uuid_id=uuid_id)
    # создаем cookies и отправляем его
    response.set_cookie(key=config_token.token_name,
                        value=token,
                        httponly=True,  # защищает cookie от JavaScript
                        max_age=config_token.cookie_max_age)
    return {'Токен сохранен в cookes': token}


@router.get('/files/', description='files_statistic')
async def files_statistic(
        request: Request,
        db: AsyncSession = Depends(get_session)) -> ResponseFiles:
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).files(id_user=id_user)


@router.post('/files/upload', description='files_upload')
async def files_upload(
        request: Request,
        file: Annotated[UploadFile, File(
            description='A file read as UploadFile')],
        path: str,
        db: AsyncSession = Depends(get_session)) -> ResponseUpLoad | str:
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).upload(
        path_file=path, file=file, id_user=id_user)


@router.get('/files/download', description='files_download')
async def files_download(
        request: Request,
        path: str,
        compression: Literal['zip', '7z', 'tar'] = None,
        db: AsyncSession = Depends(get_session)) -> StreamingResponse:
    if compression is not None:
        compression = compression.lower()
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).download(
        path_file=path, compression=compression, id_user=id_user)


@router.get('/user/status', description='user_status')
async def user_status(
        request: Request,
        db: AsyncSession = Depends(get_session)) -> ResponseStatus:
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).status(id_user)


@router.post('/files/search', description='files_search')
async def files_search(
        request: Request,
        path: str = None,
        extension: str = None,
        order_by: Literal['file', 'name', 'created_at',
        'path', 'size', 'is_downloadable'] = None,
        limit: int = 0,
        db: AsyncSession = Depends(get_session)) -> ResponseSearchAll:
    logging.debug(f'Search > path = {path} extension='
                  f'{extension} order_by={order_by} limit={limit}')
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).search(
        id_user=id_user,
        path=path,
        extension=extension,
        order_by=order_by,
        limits=limit)


@router.post('/files/revisions', description='files_revisions')
async def files_revisions(
        request: Request,
        path: str, limit: int = 0,
        db: AsyncSession = Depends(get_session)) -> ResponseRevisions:
    id_user = await auto.get_current_user(request)
    return await ServiceLink(db).revisions(
        path=path, path_limit=limit, id_user=id_user)
