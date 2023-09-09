import logging

import psycopg2
from sqlalchemy import create_engine, inspect
import time

from src.db.models import Base
from src.core.config import config
from src.db.db import db_config


def check_db(time_delay_max: int) -> None:
    """
    Проверка наличие БД и создание таблиц если их нет
    :param time_delay_max: время максимольное между опросами базы данных
    :return:
    """
    time_delay = 1  # время между опросами БД
    database = config.postgres_db
    while True:
        try:
            conn = psycopg2.connect(
                user=config.postgres_user,
                password=config.postgres_password,
                host=config.postgres_host,
                port=config.postgres_port,
                database=database
                # Подключение к базе данных postgres, чтобы выполнить запрос
            )
            # Создание курсора для выполнения SQL-запросов
            cur = conn.cursor()
            # Выполнение запроса для проверки наличия базы данных
            cur.execute("SELECT 1 FROM pg_catalog.pg_database "
                        "WHERE datname = %s;", (database,))
            # Получение результатов запроса
            exists = bool(cur.fetchone())
            # Вывод результата
            if exists:
                logging.info(f"База данных {database} существует.")
            else:
                logging.info(f"База данных {database} не существует.")
            # Подключение к серверу PostgreSQL
            engine = create_engine(db_config.replace('+asyncpg', ''))

            # Создание объекта Inspector с использованием функции inspect()
            inspector = inspect(engine)
            # Получение списка названий таблиц
            table_list = inspector.get_table_names()
            # удаляем из списка ненужную таблицу для обработки
            table_list.remove('alembic_version')
            if len(table_list) == 0:
                # База данных без таблиц, создаем их
                logging.info('Создание таблиц')
                Base.metadata.create_all(engine)
                continue
            for table_name in table_list:
                logging.info(f'Проверка наличие таблицы {table_name} '
                             f'относительно созданной в программе')
                try:
                    # Очистка БД для тестирования
                    # cur.execute(f'TRUNCATE TABLE   {table_name}')
                    # logging.info(f'Очистка таблицы {table_name}')
                    cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                    tables_count = cur.fetchone()[0]
                    if tables_count == 0:
                        logging.info(f'В таблице {table_name} нет данных')
                    else:
                        logging.info(f'В таблице {table_name} '
                                     f'= {tables_count} строк данных')
                    cur.execute(
                        f"SELECT column_name, data_type, "
                        f"character_maximum_length "

                        f"FROM information_schema.columns "
                        f"WHERE table_name = '{table_name}'")
                    tables = cur.fetchall()
                    for column in tables:
                        logging.info(f'\t\t{column}')
                    # logging.info(tables)
                except Exception as error:
                    logging.error(
                        'В базе данных нет нужных таблиц, '
                        f'создаем новые таблицы {error}')
                    Base.metadata.create_all(engine)
            break
        except Exception as error:
            time_delay *= 1.5
            if time_delay > time_delay_max:
                time_delay = time_delay_max
            logging.error(f'Ошибка подключения к серверу'
                          f' {error} повторное подключение через '
                          f'{time_delay} с.')
            time.sleep(time_delay)
        finally:
            # Закрытие курсора и соединения
            if 'cur' in globals():
                cur.close()
            if 'conn' in globals():
                conn.close()


if __name__ == "__main__":
    check_db(time_delay_max=20)
