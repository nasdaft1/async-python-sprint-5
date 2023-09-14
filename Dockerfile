FROM python:3.10
WORKDIR /app

EXPOSE 80

# Скопируйте в контейнер файлы, которые редко меняются
COPY requirements.txt requirements.txt


# Установите зависимости
RUN  pip install --upgrade pip \
     && pip install -r requirements.txt

# Скопируйте всё оставшееся. Для ускорения сборки образа эту команду стоит разместить ближе к концу файла. 
COPY . .


#WORKDIR /app/src # root проекта папка src 
WORKDIR src
# CMD gunicorn main:app --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app"]