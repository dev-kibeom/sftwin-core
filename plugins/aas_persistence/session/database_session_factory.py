from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseSessionFactory:
    """SQLAlchemy 세션 및 엔진 라이프사이클 관리자."""

    def __init__(
        self,
        db_url: str = "mysql+pymysql://root:password@localhost:3306/sftwin_db",
        **engine_kwargs: object,
    ) -> None:
        self._engine: Engine = create_engine(db_url, **engine_kwargs)
        self._session_maker = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def get_session(self) -> Session:
        """독립적인 SQLAlchemy Session을 생성하여 반환한다."""
        return self._session_maker()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """세션 라이프사이클을 관리하는 컨텍스트 매니저."""
        session: Session = self.get_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """엔진 커넥션 풀을 해제한다."""
        self._engine.dispose()
