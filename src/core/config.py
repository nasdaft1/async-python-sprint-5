import logging
import os
from typing import List, Literal
from pydantic import conint, constr
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR[-3:] == 'src':
    BASE_DIR = BASE_DIR[:-3]  # для MIGRATIONS


class AppConfig(BaseSettings):
    app_title: str = "ShorterLinks API"
    app_host: str = '127.0.0.1'
    app_port: conint(ge=1, le=65535) = 8080
    postgres_user: constr(min_length=3) = 'app'
    postgres_password: constr(min_length=3) = '123qwe'
    postgres_db: constr(min_length=2) = 'db'
    postgres_host: str = '127.0.0.1'
    postgres_port: conint(ge=1, le=65535) = 5433
    postgres_echo: bool = True

    nginx_port: conint(ge=1, le=65535) = 80

    log_level: Literal[
        'DEBUG', 'ERROR', 'WARNING',
        'CRITICAL', 'INFO', 'FATAL'] = 'INFO'
    log_file: str = 'log1.txt'
    log_handlers: List[str] = ['console']
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    class Config:
        env_file = f'{BASE_DIR}.env'
        env_file_encoding = 'utf-8'
        #  все дополнительные переменные,
        #  которые не определены как поля в модели,
        #  будут игнорироваться extra='allow'
        extra = 'allow'


class StorageConfig(BaseSettings):
    service_name: str = None
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_name: str
    region: str = None

    class Config:
        env_file = f'{BASE_DIR}src\\.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


class Crypt(BaseSettings):
    token_name: str = 'Bearer_token'
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30  # минуты
    cookie_max_age: int = 1800  # секунды

    class Config:
        env_file = f'{BASE_DIR}src\\.crypt_env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


config = AppConfig()
config_storage = StorageConfig()
config_token = Crypt()

logging.debug(f'Read configuration {config}')
logging.debug(f'Read configuration {config_storage}')
