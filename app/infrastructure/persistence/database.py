"""
Infrastructure: SQLAlchemy ORM setup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False}  # SQLite chỉ
    )


def create_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
