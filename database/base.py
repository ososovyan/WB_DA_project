from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase
from sqlalchemy.testing import future

class Base(DeclarativeBase):
    pass

class Database:

    def __init__(self, connection_string: str, echo: bool = False):
        self.engine = create_engine(
            connection_string,
            echo=echo,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=Session
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()