import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn

from src.core.config import AppConfig, StorageConfig
from src.api.v1 import base
from src.check_db import check_db

config = AppConfig()
config_s3 = StorageConfig()

app = FastAPI(

    title=config.app_title,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse
)

app.include_router(base.router, prefix="/api/v1")

if __name__ == "__main__":
    check_db(time_delay_max=20)
    logging.info(f'Starting the server host={config.app_title} '
                 f'port={config.app_port}')
    uvicorn.run(
        "main:app",
        host=config.app_host,
        port=config.app_port,
        reload=True,
    )
