"""Smoke tests for Vault client."""
from unittest.mock import MagicMock, patch

import pytest
from hvac.exceptions import InvalidRequest

from app.core.vault import VaultClient


@pytest.mark.unit
@patch("app.core.vault.hvac.Client")
def test_vault_client_is_connected_uses_hvac(mock_client_cls: MagicMock) -> None:
    mock_inst = MagicMock()
    mock_inst.is_authenticated.return_value = True
    mock_inst.secrets.kv.v2.read_secret_version.side_effect = InvalidRequest()
    mock_client_cls.return_value = mock_inst

    client = VaultClient()
    assert client.is_connected() is True
