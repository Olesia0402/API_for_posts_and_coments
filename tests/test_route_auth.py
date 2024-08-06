from unittest.mock import Mock, MagicMock

import pytest
from sqlalchemy import select

from src.database.models import User
from tests.conftest import TestingSessionLocal, test_user


user_data = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}

def test_signup(client, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.services.email.send_confirm_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user_data,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user_data.get("email")
    assert "id" in data["user"]


def test_user_exist(client, monkeypatch):
    with pytest.raises(Exception):
        mock_send_email = MagicMock()
        monkeypatch.setattr("src.services.email.send_confirm_email", mock_send_email)
        response = client.post(
            "/api/auth/signup",
            json=test_user,
        )
        assert response.status_code == 409, response.text
        data = response.json()
        assert data["detail"] == "Account already exists"

@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data

def test_wrong_email_login(client):
    with pytest.raises(Exception):
        response = client.post("api/auth/login",
                            data={"username": user_data.get("email"), "password": user_data.get("password")})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["detail"] == "Invalid email"


def test_not_confirmed_login(client):
    with pytest.raises(Exception):
        response = client.post("api/auth/login",
                            data={"username": user_data.get("email"), "password": user_data.get("password")})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["detail"] == "Email not confirmed"


def test_wrong_password_login(client):
    with pytest.raises(Exception):
        response = client.post("api/auth/login",
                            data={"username": user_data.get("email"), "password": "password"})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["detail"] == "Invalid password"


def test_validation_error_login(client):
    response = client.post("api/auth/login",
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_refresh_token(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    
    with pytest.raises(Exception):
        response = client.get("api/auth/refresh_token", headers={"Authorization": f"Bearer {user_data.get('refresh_token')}"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

def test_wrong_refresh_token(client):
    with pytest.raises(Exception):
        response = client.get("api/auth/refresh_token", headers={"Authorization": "Bearer token"})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["message"] == "Invalid refresh token"

@pytest.mark.asyncio
async def test_confirmed_email_user_confirmed(client, get_token): 
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    token = get_token
    response = client.get(f'api/auth/confirmed_email/{token}')
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"

@pytest.mark.asyncio
async def test_confirmed_email_user_not_confirmed(client, monkeypatch, get_token):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = False
            await session.commit()
    with pytest.raises(Exception):
        mock_send_email = Mock()
        monkeypatch.setattr("src.services.email.send_confirm_email", mock_send_email)
        token = get_token
        response = client.get(f'api/auth/confirmed_email/{token}')
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["message"] == "Email confirmed"


def test_confirmed_email_user_not_exist(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get(f'api/auth/confirmed_email/{token}')
        assert response.status_code == 400, response.text
        data = response.json()
        assert data["message"] == "Verification error"

@pytest.mark.asyncio
async def test_request_email_user_confirmed(client): 
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    response = client.post('api/auth/request_email', json={"email": user_data.get("email")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"

@pytest.mark.asyncio
async def test_request_email(client, monkeypatch):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = False
            await session.commit()

    mock_send_confirm_email = Mock()
    monkeypatch.setattr("src.services.email.send_confirm_email", mock_send_confirm_email)
    response = client.post('api/auth/request_email', json=user_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation."

@pytest.mark.asyncio
async def test_forget_password(client, monkeypatch): 
    mock_send_reset_email = Mock()
    monkeypatch.setattr("src.services.email.send_reset_email", mock_send_reset_email)
        
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
        
    request_data = {
        "username": current_user.username,
        "email": current_user.email,
        "password": user_data.get("password")}
    response = client.post('/api/auth/forget_password', json=request_data)    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for reset password."
    

@pytest.mark.asyncio
async def test_reset_password(client, monkeypatch, get_token): 
    mock_send_update_email = Mock()
    monkeypatch.setattr("src.services.email.send_update_email", mock_send_update_email)
    
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
    with pytest.raises(Exception):
        token = get_token
        response = client.post(f'api/auth/reset_password/{token}', json=user_data)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["message"] == "Password successfully reset. Check your email for confirmation."
        assert mock_send_update_email.called

def test_reset_password_token_not_valid(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post(f'api/auth/reset_password/{token}', json={"password": "new_password"})
        assert response.status_code == 400, response.text
        data = response.json()
        assert data["message"] == "Invalid token"

def test_reset_password_user_not_exist(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post(f'api/auth/reset_password/{token}', json={"password": "new_password"})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "User not found"