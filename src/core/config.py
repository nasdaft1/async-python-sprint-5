import logging
import os
from typing import List, Literal
from pydantic import conint, constr
from pydantic_settings import BaseSettings


def path_config() -> str:
    basa_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if basa_dir[-3:] == 'src':
        basa_dir = basa_dir[:-3]  # для MIGRATIONS
    logging.info(f'Путь прописан {basa_dir}')
    return basa_dir


class AppConfig(BaseSettings):
    app_title: str = "ShorterLinks API"
    app_host: str = '127.0.0.1'
    app_port: conint(ge=1, le=65535) = 8080
    app_prefix: str = 'api/v1'
    postgres_echo: bool = True
    postgres_db_dns: str = 'postgresql+asyncpg://app:123qwe@127.0.0.1:5432/db_url'
    postgres_db_dns_test: str = 'postgresql+asyncpg://root:root@127.0.0.1:5433/test'
    test_dir: str = 'TEST\\'

    nginx_port: conint(ge=1, le=65535) = 80

    log_level: Literal[
        'DEBUG', 'ERROR', 'WARNING',
        'CRITICAL', 'INFO', 'FATAL'] = 'INFO'
    log_file: str = 'log1.txt'
    log_handlers: List[str] = ['console', 'file']
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    class Config:
        env_file = f'{path_config()}.env'
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
        env_file = f'{path_config()}.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


class TestStorageConfig(BaseSettings):
    t_service_name: str = None
    t_endpoint_url: str
    t_aws_access_key_id: str
    t_aws_secret_access_key: str
    t_bucket_name: str
    t_region: str = None

    class Config:
        env_file = f'{path_config()}.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


class Crypt(BaseSettings):
    token_name: str = 'X-Bearer_token'
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30  # минуты
    cookie_max_age: int = 1800  # секунды

    class Config:
        env_file = f'{path_config()}.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


config = AppConfig()
config_storage = StorageConfig()
t_config_storage = TestStorageConfig()
config_token = Crypt()

logging.debug(f'Read configuration {config}')
logging.debug(f'Read configuration {config_storage}')
