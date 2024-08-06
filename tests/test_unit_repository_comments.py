import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import time
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Comment, User, Post
from src.repository.comments import (get_all_comments, get_my_comments_to_post, get_comment, create_comment,
                                    update_comment, update_comment, remove_comment, generate_relevant_response)
from src.schemas.schemas import CommentCreate

class TestComments(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1)
        self.post = Post(id=1, post_text='test', post_download='test',
                         done=False, created_at=None, update_at=None, blocked=False, user_id=1)

    async def test_get_all_comments(self):
        skip = 0
        limit = 10
        comments = [Comment(id=1, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1),
                    Comment(id=2, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1),
                    Comment(id=3, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1)]
        mocked_comments = MagicMock()
        mocked_comments.scalars.return_value.all.return_value = comments
        self.session.execute.return_value = mocked_comments
        result = await get_all_comments(skip=skip, limit=limit, post_id=self.post.id, db=self.session)
        self.assertEqual(result, comments)

    async def test_get_my_comments_to_post(self):
        skip = 0
        limit = 10
        comments = [Comment(id=1, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1),
                    Comment(id=2, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1),
                    Comment(id=3, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1)]
        mocked_comments = MagicMock()
        mocked_comments.scalars.return_value.all.return_value = comments
        self.session.execute.return_value = mocked_comments
        result = await get_my_comments_to_post(skip=skip, limit=limit, user=self.user, post_id=self.post.id, db=self.session)
        self.assertEqual(result, comments)

    async def test_get_comment(self):
        comment = Comment(id=1, comment_text='test', auto_reply_flag=False, post_id=1, user_id=1)
        mocked_comment = MagicMock()
        mocked_comment.scalar_one_or_none.return_value = comment
        self.session.execute.return_value = mocked_comment
        result = await get_comment(1, self.post.id, self.session)
        self.assertEqual(result, comment)

    async def test_create_comment(self):
        body = CommentCreate(comment_text='test', auto_reply_flag=False)
        result = await create_comment(body, self.post, self.user, self.session)
        self.assertIsInstance(result, Comment)
        self.assertEqual(result.comment_text, body.comment_text)
        self.assertEqual(result.auto_reply_flag, body.auto_reply_flag)

    async def test_update_comment(self):
        body = CommentCreate(comment_text='test', auto_reply_flag=False)
        result = await update_comment(1, body, self.post, self.user, self.session)
        self.assertIsInstance(result, Comment)
        self.assertEqual(result.comment_text, body.comment_text)
        self.assertEqual(result.auto_reply_flag, body.auto_reply_flag)

    async def test_remove_comment(self):
        mocked_post = MagicMock()
        mocked_post.scalar_one_or_none.return_value = Post(id=1, post_text='test', post_download='test',
                                                           done=False, created_at=None, update_at=None, blocked=False, user_id=1)
        self.session.execute.return_value = mocked_post
        result = await remove_comment(1, self.post, self.user, self.session)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()

        self.assertIsInstance(result, Post)

    def test_generate_response_for_help(self):
        response = generate_relevant_response("I need help with my account.")
        self.assertEqual(response, "Thanks for your question! We will help you soon.")

    def test_generate_response_for_issue(self):
        response = generate_relevant_response("There is an issue with my order.")
        self.assertEqual(response, "Sorry to hear about your issue. We are looking into it.")

    def test_generate_response_for_generic_comment(self):
        response = generate_relevant_response("This is a generic comment.")
        self.assertEqual(response, "Thank you for your comment!")
