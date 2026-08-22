import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from plugins.aas_persistence.session.database_session_factory import (
    DatabaseSessionFactory,
)


def test_session_factory_uses_default_env_fallback():
    with (
        patch.dict(os.environ, {}, clear=True),
        patch(
            "plugins.aas_persistence.session.database_session_factory.create_engine"
        ) as mock_create_engine,
    ):
        factory = DatabaseSessionFactory()

        expected_url = "mysql+pymysql://sftwin_admin:SecureAdminPassword123!@localhost:3306/sftwin_db"
        mock_create_engine.assert_called_once_with(expected_url)


def test_session_factory_prefers_database_url_env():
    custom_db_url = "mysql+pymysql://custom_user:custom_pass@db-cluster:3306/custom_db"
    with (
        patch.dict(os.environ, {"DATABASE_URL": custom_db_url}, clear=True),
        patch(
            "plugins.aas_persistence.session.database_session_factory.create_engine"
        ) as mock_create_engine,
    ):
        factory = DatabaseSessionFactory()

        mock_create_engine.assert_called_once_with(custom_db_url)


def test_session_factory_prefers_explicit_argument():
    arg_db_url = "mysql+pymysql://arg_user:arg_pass@localhost:3306/arg_db"
    with (
        patch.dict(os.environ, {"DATABASE_URL": "mysql://env_url"}, clear=True),
        patch(
            "plugins.aas_persistence.session.database_session_factory.create_engine"
        ) as mock_create_engine,
    ):
        factory = DatabaseSessionFactory(db_url=arg_db_url)

        mock_create_engine.assert_called_once_with(arg_db_url)


def test_session_scope_lifecycle():
    with patch(
        "plugins.aas_persistence.session.database_session_factory.create_engine"
    ):
        factory = DatabaseSessionFactory()
        mock_session = MagicMock(spec=Session)
        factory._session_maker = MagicMock(return_value=mock_session)

        # 1. 정상 종료 시 close 검증
        with factory.session_scope() as session:
            assert session == mock_session

        assert mock_session.close.call_count == 1
        assert mock_session.rollback.call_count == 0

        # 2. 예외 발생 시 rollback 및 close 검증
        mock_session.reset_mock()
        with pytest.raises(ValueError), factory.session_scope():
            raise ValueError("Test error inside session scope")

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1
