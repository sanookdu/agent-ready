"""Tests never read the user's provider authentication artifact."""

import pytest


@pytest.fixture(autouse=True)
def isolated_provider_auth(tmp_path, monkeypatch):
    config = tmp_path / "provider-config"
    config.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(config))
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        monkeypatch.delenv(name, raising=False)
