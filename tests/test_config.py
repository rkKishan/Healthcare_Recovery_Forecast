"""
The production configuration guard.

A server that boots happily while signing tokens with a published placeholder
key is worse than one that refuses to start, because nothing surfaces the
problem until someone forges a token. These tests pin that behaviour.
"""

from __future__ import annotations

import pytest

from backend.config import INSECURE_SECRETS, Config, verify_production_config


def config_with(**overrides) -> type[Config]:
    return type("_Config", (Config,), overrides)


class TestProductionGuard:
    @pytest.mark.parametrize("placeholder", sorted(INSECURE_SECRETS))
    def test_placeholder_secret_refuses_to_start_in_production(self, placeholder):
        candidate = config_with(DEBUG=False, SECRET_KEY=placeholder)

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            verify_production_config(candidate)

    def test_a_real_secret_is_accepted_in_production(self):
        candidate = config_with(DEBUG=False, SECRET_KEY="f" * 64)
        verify_production_config(candidate)  # must not raise

    @pytest.mark.parametrize("placeholder", sorted(INSECURE_SECRETS))
    def test_development_is_left_alone(self, placeholder):
        """Placeholders stay convenient in debug mode -- that is the point."""
        candidate = config_with(DEBUG=True, SECRET_KEY=placeholder)
        verify_production_config(candidate)  # must not raise

    def test_the_error_says_how_to_fix_it(self):
        candidate = config_with(DEBUG=False, SECRET_KEY="dev-secret-change-me")

        with pytest.raises(RuntimeError) as excinfo:
            verify_production_config(candidate)

        assert "token_hex" in str(excinfo.value)

    def test_sqlite_in_production_warns_but_does_not_block(self, caplog):
        """The Docker demo runs SQLite with FLASK_DEBUG=false and must still boot."""
        candidate = config_with(
            DEBUG=False,
            SECRET_KEY="f" * 64,
            SQLALCHEMY_DATABASE_URI="sqlite:////tmp/app.db",
        )

        verify_production_config(candidate)
        assert any("SQLite" in message for message in caplog.messages)


class TestDatabaseUrlNormalisation:
    """
    A Postgres URL without a driver must not reach SQLAlchemy unchanged.

    Every managed provider hands out `postgresql://`, SQLAlchemy reads that
    as psycopg2, and this project ships psycopg 3 -- so the app died at
    db.init_app with ModuleNotFoundError after a build that looked healthy.
    """

    @staticmethod
    def _uri(value):
        import importlib
        import os

        import backend.config as config

        previous = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = value
        try:
            importlib.reload(config)
            return config.Config.SQLALCHEMY_DATABASE_URI
        finally:
            if previous is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous
            importlib.reload(config)

    def test_a_driverless_postgres_url_gets_psycopg(self):
        uri = self._uri("postgresql://u:p@host.neon.tech/neondb?sslmode=require")
        assert uri.startswith("postgresql+psycopg://")
        # The rest of the URL must survive intact -- credentials, host, query.
        assert uri.endswith("u:p@host.neon.tech/neondb?sslmode=require")

    def test_the_legacy_postgres_scheme_is_handled_too(self):
        assert self._uri("postgres://u:p@h/db").startswith("postgresql+psycopg://")

    def test_an_explicit_driver_is_left_alone(self):
        for url in (
            "postgresql+psycopg://u:p@h/db",
            "mysql+pymysql://u:p@h/db",
        ):
            assert self._uri(url) == url
