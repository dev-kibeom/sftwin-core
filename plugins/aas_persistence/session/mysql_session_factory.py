import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class MysqlSessionFactory:
    def __init__(
        self,
        db_url: str | None = None,
        **engine_kwargs: object,
    ) -> None:
        user = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "sftwin_admin")
        password = os.getenv("MYSQL_PASSWORD") or os.getenv(
            "DB_PASSWORD", "SecureAdminPassword123!"
        )
        host = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
        port = os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306")
        dbname = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "sftwin_db")

        default_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
        resolved_url = db_url or os.getenv("DATABASE_URL") or default_url

        self._engine: Engine = create_engine(resolved_url, **engine_kwargs)
        self._session_maker = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def get_session(self) -> Session:
        return self._session_maker()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session: Session = self.get_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self._engine.dispose()
