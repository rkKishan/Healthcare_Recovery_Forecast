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
