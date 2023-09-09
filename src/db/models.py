import uuid

from sqlalchemy import Boolean, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Импортируем базовый класс для моделей.
Base = declarative_base()

generator = lambda: str(uuid.uuid4())


class UniqueUUID(Base):
    __tablename__ = "unique_uuid"
    id = Column(UUID(as_uuid=True),primary_key=True, unique=True)


class Access(Base):
    __tablename__ = "access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generator)
    tocken = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user = Column(String(12), unique=True)
    password = Column(String(20))


class Files(Base):
    __tablename__ = "files"

    id_file = Column(UUID(as_uuid=True), primary_key=True)
    file_name = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    id_path = Column(UUID, ForeignKey('paths.id_path'))
    size = Column(Integer, default=0)
    is_downloadable = Column(Boolean, default=True)
    hash = Column(String(64))
    modified_at = Column(DateTime, server_default=func.now())
    account_id = Column(UUID, ForeignKey('access.id'))


class Paths(Base):
    __tablename__ = "paths"

    id_path = Column(UUID(as_uuid=True), primary_key=True)
    path = Column(String(100))
    is_downloadable = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    account_id = Column(UUID, ForeignKey('access.id'))
