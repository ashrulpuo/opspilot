"""Smoke tests for Salt API client."""
from unittest.mock import MagicMock, patch

import pytest

from app.core.salt import SaltClient


@pytest.mark.unit
@patch("app.core.salt.httpx.post")
def test_salt_client_not_authenticated_when_login_fails(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 401
    client = SaltClient()
    assert client.is_authenticated() is False
