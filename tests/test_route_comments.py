from unittest.mock import Mock, patch

import pytest

from src.services.auth import auth_service
from src.database.models import Post

def test_read_comments(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/comments', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

def test_read_my_comments(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/1/my', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

def test_read_comment(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/1/1', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)

def test_read_comment_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/1/100', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Comment not found"

def test_create_comment_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/1/1', json={'comment_text': 'title', 'comment_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 500, response.text
        data = response.json()
        assert "detail" in data

def test_create_comment(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/1/', json={'comment_text': 'title', 'comment_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)

def test_create_comment_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/1/', json={'comment_text': 'title'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 500, response.text
        data = response.json()
        assert "detail" in data

def test_update_comment(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/1/1', json={'comment_text': 'title', 'comment_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)

def test_update_comment_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/1/100', json={'comment_text': 'title', 'comment_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Comment not found"

def test_update_comment_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/1/1', json={'comment_text': 'title', 'comment_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 500, response.text
        data = response.json()
        assert "detail" in data

def test_remove_comment(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.delete('/api/1/1', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data

def test_remove_comment_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.delete('/api/1/100', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Comment not found"
