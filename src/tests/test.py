import logging
from uuid import UUID
import os
import random
import string

import pytest
from httpx import AsyncClient
import sqlalchemy as sql

import db.db
from fastapi.testclient import TestClient
from conftest import async_session as t_async_session
from main import app
from db.models import Access, Files, Paths
from services.util import check_path_file
from core.config import config_token
from db.db import s3, get_session
from core.config import config

from db.db import async_session

user: UUID
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base_url = f'http://{config.app_host}:{config.app_port}/{config.app_prefix}'

token = {'Test': ''}
id_key = {'1': '1'}


@pytest.mark.parametrize('name_input, expected',
                         [('/1.3', ['1.3', '/']),
                          ('/.3', ['.3', '/']),
                          ('/3/5/4.7', ['4.7', '/3/5/']),
                          ('//4.7', [None, None]),
                          ('/r.5/4.7', [None, None]),
                          ('/1.', [None, None]),
                          ('/1/', [None, '/1/']),
                          ('/1/4', [None, None]),
                          ('/', [None, '/']),
                          ])
def test_util__check_path_file(name_input: str, expected: list):
    result1, reselt2 = None, None
    try:
        result1, reselt2 = check_path_file(name_input)
    except ValueError as error:
        logging.debug(error)
        expected = [None, None]
    print(f'{result1} {reselt2}  --- {name_input}')
    assert [result1, reselt2] == expected


async def connect_db():
    async with async_session() as session:
        """Проверка что в БД данные вносятся"""
        statement = sql.select(sql.func.count(Access.id))
        count_as = (await session.execute(statement)).fetchone()
        statement = sql.select(sql.func.count(Files.id_file))
        count_fi = (await session.execute(statement)).fetchone()
        statement = sql.select(sql.func.count(Paths.id_path))
        count_pa = (await session.execute(statement)).fetchone()
        logging.error(f'Количество данные в таблицах as={count_as[0]} fi={count_fi[0]} pa={count_pa[0]} ')
    async with t_async_session() as session:
        """Проверка что в БД данные вносятся"""
        statement = sql.select(sql.func.count(Access.id))
        count_as = (await session.execute(statement)).fetchone()
        statement = sql.select(sql.func.count(Files.id_file))
        count_fi = (await session.execute(statement)).fetchone()
        statement = sql.select(sql.func.count(Paths.id_path))
        count_pa = (await session.execute(statement)).fetchone()
        logging.error(f'Количество данные в таблицах as={count_as[0]} fi={count_fi[0]} pa={count_pa[0]} ')


async def test_star_db():
    await connect_db()


async def test_in():
    async with AsyncClient(app=app, base_url=base_url) as ac:
        response = await ac.get('/')
        print(response)
        assert response.status_code == 200
        assert response.text == '"Добро пожаловать в Файловое хранилище"'


async def test_ping():
    async with AsyncClient(app=app, base_url=base_url) as ac:
        response = await ac.get('/ping')
        print(response)
        assert response.status_code == 200
        assert response.json().get('db') is not None
        assert response.json().get('cache') is None
        assert response.json().get('nginx') is not None
        assert response.json().get('storage') is not None


@pytest.mark.parametrize('username, password, code, res_text',
                         [('ggH4e3/1', 'ggH4e3/1', 200, True),
                          ('1вH45e3/1', '35.2dJwы', 200, True),
                          ('ggH46e3/1', 'ggH4e3/1', 200, True),
                          ('1вH47e3/1', '35.2dJwы', 200, True),
                          ('ggH4e83/1', 'ggH4e3/1', 200, True),
                          ('1вHgf3e3/1', '35.2dJwы', 200, True),
                          ('ggH4e93/1', 'ggH4e3/1', 200, True),
                          ('1вH4e3/1', '35.2dJwы', 200, True),
                          ('1вH4e3/1', '3wы', 422, False),
                          ('1вH4e3/1', '3w423fsdfы', 200, False)])
async def test_register(username, password, code, res_text):
    """Проверка регистрации пользователей и ошибок"""
    async with AsyncClient(app=app, base_url=base_url) as ac:
        params = {'username': username, 'password': password}
        response = await ac.post('/register', params=params)

        assert response.status_code == code
        if res_text:
            assert response.text == '{"msg":"Пользователь зарегистрирован"}'
        else:
            assert response.text != '{"msg":"Пользователь зарегистрирован"}'


@pytest.mark.parametrize('username, password',
                         [('ggH4e3/1', 'ggH4e3/1'),
                          ('1вH4e3/1', '35.2dJwы')])
async def test_get_user(username, password):
    """Проверка что в БД данные вносятся"""
    async with async_session() as session:
        statement = sql.select(Access.id).where(Access.user == username)
        global user
        user = (await session.execute(statement)).one_or_none()
        global id_key

        logging.debug(f'+++++{user}')
        assert user is not None
        id_key[username] = str(user[0])

    return user


@pytest.mark.parametrize('username, password',
                         [('ggH4e3/1', 'ggH4e3/1'),
                          ('1вH4e3/1', '35.2dJwы')])
async def test_auth(username, password):
    """Авторизация и получение токенов и их корректность"""
    async with AsyncClient(app=app, base_url=base_url) as ac:
        params = {'username': username, 'password': password}
        response = await ac.post("/auth", params=params)
        global token
        token[username] = response.json().get('Токен сохранен в cookes')
        logging.info(f'token[{username}] = {token[username]}')
        assert response.status_code == 200
        assert token[username] is not None

    key = list(token)
    print('Список ключей пользователей токенов', key)
    assert token[key[0]] != token[key[1]]


def test_token():
    assert len(token) == 3


async def generated_file(file_name: str, path_test, length: int = 1024):
    """Генерация данных для файла"""

    data = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    with open(f'{BASE_DIR}\\{path_test}{file_name}', mode='w') as file:
        file.write(data)


async def storages():
    """Проверка количества файлов в облачном хранилище"""
    data = [f async for f in s3.list()]
    return len(data)


@pytest.mark.parametrize('username, password, path, size, file_name, file_new',
                         [('ggH4e3/1', 'ggH4e3/1', '/1/', 2000, '1.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/1/', 2100, '1.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 2000, '3.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 1000, '4.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 500, '4.txt', 0)])  # переписываем старый
@pytest.mark.asyncio
async def test_update(username, password, path, size, file_name, file_new):
    """Запись файла в облачное хранилище"""
    count_file_storages_start = await storages()
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])
        # Создание временных файлов
        path_test = config.test_dir
        await generated_file(file_name, path_test, size)

        params = {'path': path}
        files = {'file': open(f'{BASE_DIR}\\{path_test}{file_name}', 'rb')}
        print(f'{BASE_DIR}\\{path_test}{file_name} запись временного файла ')
        response = await ac.post("/files/upload",
                                 params=params,
                                 files=files)
        assert response.status_code == 200
        assert response.json().get('id') is not None
        assert response.json().get('path') == path
        assert response.json().get('size') == size
        assert response.json().get('name') == file_name
        assert response.json().get('is_downloadable') is True
    count_file_storages = await storages()
    assert count_file_storages == count_file_storages_start + file_new, 'Не сработала перезапись файла'


@pytest.mark.parametrize('username, password, path, size, file_name, file_new',
                         [('ggH4e3/1', 'ggH4e3/1', '/1/', 2000, '1.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/1/', 2100, '1.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 2000, '3.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 2000, '3.txt', 2),
                          ])  # переписываем старый
@pytest.mark.asyncio
async def test_storage(username, password, path, size, file_name, file_new):
    """Проверка наличия в облачном хранилище файлов"""
    async with async_session() as session:
        statement = (sql.select(Access.user, Files.file_name,
                                Files.unique_id, Files.file_name, Files.hash, Files.size
                                ).join(Access).join(Paths).where(sql.and_(
            Access.user == username, Files.file_name == file_name,
            Paths.path == path)))
        data = (await session.execute(statement)).fetchone()

        data2 = [f async for f in s3.list(str(data[2]))][0]
        assert data is not None
        assert data2.key == str(data[2])  # сравнение ключей (облако==БД)
        assert data2.e_tag == data[4]  # сравнение hash (облако==БД)
        assert data[5] == size  # сравнение size (облако==исходные данные)

        assert data2.size == data[5]  # сравнение size (облако==БД)


@pytest.mark.parametrize('username, path_file, compression, file_test, file_size',
                         [('ggH4e3/1', '/1/', 'zip', '1.zip', 1000),  # проверка скачивания одного файла в папке
                          ('1вH4e3/1', '/2/', 'zip', '2.zip', 1000),  # проверка скачивания два файла в папке
                          ('1вH4e3/1', '/2/', '7z', '1.7z', 1000),  # проверка скачивания два файла в папке
                          ('ggH4e3/1', '/2/', 'tar', '1.tag', 1000),  # проверка скачивания два файла в папке
                          ('ggH4e3/1', '/1/1.txt', 'zip', '3.zip', 1000),  # проверка скачивания одного файла в папке
                          ])
async def test_files_download(username, path_file, compression, file_test, file_size):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])

        params = {'path': path_file, 'compression': compression}
        response = await ac.get("/files/download",
                                params=params)
        if response.status_code == 200:
            # Получение имени файла из заголовка Content-Disposition
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                file_name = content_disposition.split('filename=')[1].strip('"')
            else:
                file_name = 'xxx.txt'
            path_test = 'TEST\\'
            # file_name = f'download.{compression}'
            path_file = f'{BASE_DIR}\\{path_test}{file_test}'

            # Сохранение файла
            with open(path_file, 'wb') as file:
                file.write(response.content)
            # размер скачиваемого файла

            print(f"Файл {path_file} успешно скачан!")
            assert os.path.getsize(path_file) > 100
        else:
            print("Не удалось скачать файл. Проверьте параметры запроса.")


@pytest.mark.parametrize(
    'username, data',
    [('ggH4e3/1', {'/1/': {'allocated': '4100', 'files': 1, 'used': '2000'}}),
     ('1вH4e3/1', {'/1/': {'allocated': '4100', 'files': 1, 'used': '2100', },
                   '/2/': {'allocated': '3000', 'files': 2, 'used': '3000'}})])
async def test_user_status(username, data):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])

        response = await ac.get("/user/status")
        assert response.status_code == 200
        result = response.json().get('folders')
        assert result == data


# 'file', 'name', 'created_at', 'path', 'size', 'is_downloadable'
@pytest.mark.parametrize('username, order_by, path, size, file_name, limit',
                         [('ggH4e3/1', 'file', '/1/', 2000, '1.txt', 1),
                          ('ggH4e3/1', 'size', '/1/', 2000, '1.txt', 0),
                          ('ggH4e3/1', 'created_at', '/1/', 2000, '1.txt', -1),
                          ('1вH4e3/1', 'file', '/1/', 2100, '1.txt', 1),
                          ('1вH4e3/1', 'size', '/2/', 2000, '3.txt', 1),
                          ('1вH4e3/1', 'created_at', '/2/', 1000, '4.txt', 1),
                          ])  # переписываем старый
async def test_files_search(username, order_by, path, size, file_name, limit):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])

        params = {'path': path,
                  'extension': file_name,
                  'order_by': order_by}
        response = await ac.post("/files/search",
                                 params=params)
        assert response.status_code == 200
        data = response.json().get('mathes')[0]
        assert data['name'] == file_name
        assert data['path'] == path
        assert data['size'] == size


@pytest.mark.parametrize('username, password, path, size, file_name, limit',
                         [('ggH4e3/1', 'ggH4e3/1', '/1/', 2000, '1.txt', 1),
                          ('ggH4e3/1', 'ggH4e3/1', '/1/', 2000, '1.txt', 0),
                          ('ggH4e3/1', 'ggH4e3/1', '/1/', 2000, '1.txt', -1),

                          ('1вH4e3/1', '35.2dJwы', '/1/', 2100, '1.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 1000, '4.txt', 1),
                          ('1вH4e3/1', '35.2dJwы', '/2/', 1000, '4.txt', 1),
                          ])  # переписываем старый
async def test_files_revisions(username, password, path, size, file_name, limit):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])
        params = {'path': path, 'limit': limit}
        response = await ac.post("/files/revisions",
                                 params=params)
        result = response.json().get('revisions')
        assert response.status_code == 200

        # assert response.json() == 0
        assert result[0]['size'] == size
        assert result[0]['path'] == path
        assert result[0]['name'] == file_name


# 1вH4e3/1
@pytest.mark.parametrize('username, long',
                         [('ggH4e3/1', 1),
                          ('1вH4e3/1', 3)])
async def test_files(username, long):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])
        response = await ac.get("/files/")

        assert response.status_code == 200
        data = response.json().get('files')
        assert len(data) == long
        assert str(response.json().get('account_id')) == id_key[username]


async def test_end_db():
    await connect_db()
