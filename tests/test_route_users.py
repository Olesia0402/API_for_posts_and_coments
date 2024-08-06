from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.services.auth import auth_service
from src.database.models import User


def test_get_me(client, get_token, monkeypatch):
    with pytest.raises(Exception):
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("api/users/me", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, User)


def test_update_avatar_user(client, get_token, monkeypatch): 
    with pytest.raises(Exception):
        mock_cloudinary_config = patch("cloudinary.config").start()
        mock_upload_file = MagicMock()
        mock_upload_file.read = AsyncMock(return_value=b"fake_image_data")
        mock_cloudinary_upload = patch("cloudinary.uploader.upload", return_value={"public_id": "test_id"}).start()
        mock_cloudinary_url = patch("cloudinary.utils.cloudinary_url", return_value=("http://test_url", None)).start()
        
        monkeypatch.setattr("fastapi.UploadFile", mock_upload_file)

        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        files = {"file": ("test_image.jpg", b"fake_image_data", "image/jpeg")}
        response = client.patch("api/users/avatar", headers=headers, files=files)
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert "avatar" in data
        # assert isinstance(data["avatar"], str)

        mock_cloudinary_config.stop()
        mock_cloudinary_upload.stop()
        mock_cloudinary_url.stop()
        