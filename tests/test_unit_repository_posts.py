import unittest
from unittest.mock import AsyncMock, MagicMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Post, User
from src.repository.posts import get_all_posts, get_my_posts, get_post, create_post, update_post, remove_post
from src.schemas.schemas import PostCreate

class TestPosts(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1)

    async def test_get_all_posts(self):
        limit = 10
        offset = 0
        posts = [Post(id=1, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1),
                 Post(id=2, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1),
                 Post(id=3, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1)]
        mocked_posts = MagicMock()
        mocked_posts.scalars.return_value.all.return_value = posts
        self.session.execute.return_value = mocked_posts
        result = await get_all_posts(limit, offset, self.session)
        self.assertEqual(result, posts)

    async def test_get_my_posts(self):
        limit = 10
        offset = 0
        posts = [Post(id=1, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1),
                 Post(id=2, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1),
                 Post(id=3, post_text='test', post_download='test',
                      done=False, created_at=None, update_at=None, blocked=False, user_id=1)]
        mocked_posts = MagicMock()
        mocked_posts.scalars.return_value.all.return_value = posts
        self.session.execute.return_value = mocked_posts
        result = await get_my_posts(limit, offset, self.user, self.session)
        self.assertEqual(result, posts)

    async def test_get_post(self):
        post = Post(id=1, post_text='test', post_download='test',
                     done=False, created_at=None, update_at=None, blocked=False, user_id=1)
        mocked_post = MagicMock()
        mocked_post.scalar_one_or_none.return_value = post
        self.session.execute.return_value = mocked_post
        result = await get_post(1, self.session)
        self.assertEqual(result, post)

    async def test_create_post_valid_text(self):
        body = PostCreate(post_text="This is a clean post", post_download=None)
        
        post = await create_post(body, self.user, self.session)
        
        self.assertFalse(post.blocked)
        self.assertEqual(post.post_text, "This is a clean post")

    async def test_create_post_inappropriate_text(self):
        body = PostCreate(post_text="This contains a crap", post_download=None)
        
        post = await create_post(body, self.user, self.session)
        
        self.assertTrue(post.blocked)

    async def test_update_post(self):
        body = PostCreate(post_text='test', post_download='test')
        mocked_post = MagicMock()
        mocked_post.scalar_one_or_none.return_value = Post(id=1, post_text='test', post_download='test',
                                                           done=False, created_at=None, update_at=None, user_id=1)
        self.session.execute.return_value = mocked_post

        result = await update_post(1, body, self.user, self.session)

        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Post)
        self.assertEqual(result.post_text, body.post_text)
        self.assertEqual(result.post_download, body.post_download)


    async def test_remove_post(self):
        mocked_post = MagicMock()
        mocked_post.scalar_one_or_none.return_value = Post(id=1, post_text='test', post_download='test',
                                                           done=False, created_at=None, update_at=None, blocked=False, user_id=1)
        self.session.execute.return_value = mocked_post
        result = await remove_post(1, self.user, self.session)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()

        self.assertIsInstance(result, Post)