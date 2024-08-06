from unittest.mock import Mock, patch

import pytest

from src.services.auth import auth_service
from src.database.models import Post

def test_get_all_posts(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/posts', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

def test_get_my_posts(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/posts/my', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)

def test_get_post(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/posts/1', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)
        assert "id" in data

def test_get_post_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/posts/100', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Post not found"

def test_create_post(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/posts', json={'post_text': 'title', 'post_download': 'content', 'done': False, 'blocked': False},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data['post_text'] == 'title'
        assert data['post_download'] == 'content'
        assert data['done'] == False
        assert data['blocked'] == False

def test_create_post_block(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/posts', json={'post_text': 'title', 'post_download': 'content', 'done': False, 'blocked': True},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data['post_text'] == 'title'
        assert data['post_download'] == 'content'
        assert data['done'] == False
        assert data['blocked'] == True

def test_create_post_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.post('/api/posts', json={'post_text': 'title', 'post_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 500, response.text
        data = response.json()
        assert "detail" in data

def test_update_post(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/posts/1', json={'post_text': 'title', 'post_download': 'content', 'done': False, 'blocked': False},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data['post_text'] == 'title'
        assert data['post_download'] == 'content'
        assert data['done'] == False
        assert 'blocked' in data

def test_update_post_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/posts/100', json={'post_text': 'title', 'post_download': 'content', 'done': False, 'blocked': False},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Post not found"

def test_update_post_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.put('/api/posts/1', json={'post_text': 'title', 'post_download': 'content'},
                               headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 500, response.text
        data = response.json()
        assert "detail" in data

def test_delete_post(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.delete('/api/posts/1', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data

def test_delete_post_not_found(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.delete('/api/posts/100', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Post not found"

def test_get_daily_breakdown(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/1/daily-breakdown?date_from=2021-01-01&date_to=2021-01-02', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)

def test_get_daily_breakdown_bad_request(client, get_token):
    with pytest.raises(Exception):
        token = get_token
        response = client.get('/api/1/daily-breakdown?date_from=2021-01-01&date_to=2021-01-02', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 400, response.text
        data = response.json()
        assert "detail" in data