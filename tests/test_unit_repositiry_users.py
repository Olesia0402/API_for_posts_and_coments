import unittest
from unittest.mock import AsyncMock, MagicMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import get_user_by_email, create_user, confirmed_email, update_token, update_avatar
from src.schemas.schemas import UserModel, UserDb, UserResponse, TokenModel


class TestUsersRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        user = User(id=1, username='John5', email='j@j.com', password='123456',
                    created_at=None, avatar=None, confirmed=False, refresh_token='23456')
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_email('j@j.com', self.session)
        self.assertEqual(result, user)
    
    async def test_create_user(self):
        body = UserModel(username='John5', email='j@j.com', password='123456')
        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)

    async def test_confirmed_email(self):
        user = User(id=1, username='John5', email='j@j.com', password='123456',
                    created_at=None, avatar=None, confirmed=False, refresh_token='23456')
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await confirmed_email('j@j.com', self.session)
        self.session.commit.assert_called_once()

    async def test_update_token(self):
        user = User(id=1, username='John5', email='j@j.com', password='123456',
                    created_at=None, avatar=None, confirmed=False, refresh_token='23456')
        token = 'new_refresh_token'
        result = await update_token(user, token, self.session)
        self.session.commit.assert_called_once()

    async def test_update_avatar(self):
        user = User(id=1, username='John5', email='j@j.com', password='123456',
                    created_at=None, avatar=None, confirmed=False, refresh_token='23456')
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await update_avatar(user.email, 'https://example.com', self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.avatar, 'https://example.com')

        