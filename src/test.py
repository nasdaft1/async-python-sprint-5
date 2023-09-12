import logging
from uuid import UUID
import os
import random
import string

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sqlalchemy as sql

from src.main import app
from src.db.models import Access, Files, Paths
from src.db import db
from src.services.util import check_path_file
from src.core.config import config_token
from src.db.db import s3, db_config
from src.db.models import Base
from src.services.upload import UpLoad

client = TestClient(app)

dns = db.db_config.replace('+asyncpg', '')
engine = sql.create_engine(dns)
Session = db.async_session

user: UUID
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_url = 'http://127.0.0.1:8080/api/v1'
token = {'Test': ''}
id_key = {'1': '1'}


# # Подключение к серверу PostgreSQL
# engine = async sql.create_engine(db_config.replace('+asyncpg', ''))
# # Base.metadata.create_all(engine)
# Base.metadata.clear(engine)

async def test_create_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


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
    try:
        result1, reselt2 = check_path_file(name_input)
    except ValueError as error:
        logging.debug(error)
        expected = [None, None]
    print(f'{result1} {reselt2}  --- {name_input}')
    assert [result1, reselt2] == expected


# async def test_create_file_db():
#     UpLoad.file_create(
#         file_name='58952b95-55dc-4e61-9707-c19022dde5cc',
#         id_path='',
#         id_user=22,
#         file_hash='',
#         file_size='',
#         file_uuid='')
#     async with Session() as session:
#         statement = sql.select(Files.account_id, Files.file_name)
#         data = (await session.execute(statement)).fetchall()
#         assert len(data)

@pytest.mark.asyncio
async def test_in():
    async with AsyncClient(app=app, base_url='http://127.0.0.1:8080/api/v1') as ac:
        response = await ac.get('/')
        print(response)
        assert response.status_code == 200
        assert response.text == '"Добро пожаловать в Файловое хранилище"'


@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(app=app, base_url='http://127.0.0.1:8080/api/v1') as ac:
        response = await ac.get('/ping')
        assert response.status_code == 200


@pytest.mark.parametrize('username, password, code, res_text',
                         [('ggH4e3/1', 'ggH4e3/1', 200, True),
                          ('1вH4e3/1', '35.2dJwы', 200, True),
                          ('1вH4e3/1', '3wы', 422, False),
                          ('1вH4e3/1', '3w423fsdfы', 200, False)])
async def test_register(username, password, code, res_text):
    """Проверка регистрации пользователей и ошибок"""
    async with AsyncClient(app=app, base_url='http://127.0.0.1:8080/api/v1') as ac:
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
    async with Session() as session:
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
    async with AsyncClient(app=app, base_url='http://127.0.0.1:8080/api/v1') as ac:
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


# assert token[key[0]] != token[key[1]] # не генерятся ли одинаковые

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
    async with AsyncClient(app=app, base_url=html_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])
        # Создание временных файлов
        path_test = 'TEST\\'
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
    async with Session() as session:
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
    async with AsyncClient(app=app, base_url=html_url) as ac:
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
    async with AsyncClient(app=app, base_url=html_url) as ac:
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
    async with AsyncClient(app=app, base_url=html_url) as ac:
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
    async with AsyncClient(app=app, base_url=html_url) as ac:
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
    async with AsyncClient(app=app, base_url=html_url) as ac:
        # Создание cookies
        ac.cookies.set(name=config_token.token_name, value=token[username])
        response = await ac.get("/files/")

        assert response.status_code == 200
        data = response.json().get('files')
        assert len(data) == long
        assert str(response.json().get('account_id')) == id_key[username]


async def test_viev_db():
    async with Session() as session:
        statement = sql.select(Files.account_id, Files.file_name,
                               Files.unique_id, Paths.path, Paths.id_path, Files.size).join(Paths)

        data = (await session.execute(statement)).fetchall()
        for line in data:
            logging.error(f'+++++{line}')

# if __name__ == "__main__":
#     asyncio.run(test_register())
# asyncio.run(test_auth())
# id_user = ''
# asyncio.run(test_update(id_user))
# asyncio.run(test_files_download(id_user))
# asyncio.run(test_user_status(id_user))
# asyncio.run(test_files_search(id_user))
# asyncio.run(test_files_revisions(id_user))
# asyncio.run(test_files(id_user))
