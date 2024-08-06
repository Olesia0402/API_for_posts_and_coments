import json
from time import sleep
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.models import Comment, Post, User
from src.schemas.schemas import CommentCreate, CommentResponse
from config import settings

with open ("src/schemas/words_template.json") as file:
    WORDS = set(json.load(file)["words"])


async def get_all_comments(skip: int, limit: int,
                           post_id: int, db: AsyncSession) -> List[Comment]:
    """
    Retrieves a list of comments for a given post.

    Args:
        skip (int): The number of comments to skip.
        limit (int): The maximum number of comments to retrieve.
        post_id (int): The ID of the post.
        db (AsyncSession): The database session.

    Returns:
        List[Comment]: A list of Comment objects representing the retrieved comments.
    """
    
    stmt = select(Comment).filter_by(post_id=post_id,
                                     blocked=False).offset(skip).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def get_my_comments_to_post(skip: int, limit: int,
                                  post_id: int, user: User, db: AsyncSession) -> List[Comment]:
    """
    Retrieves a list of comments made by a user for a specific post.

    Args:
        skip (int): The number of comments to skip.
        limit (int): The maximum number of comments to retrieve.
        post_id (int): The ID of the post.
        user (User): The user who made the comments.
        db (AsyncSession): The database session.

    Returns:
        List[Comment]: A list of Comment objects representing the retrieved comments.
    """
    stmt = select(Comment).filter_by(post_id=post_id,
                                     user_id=user.id, blocked=False).offset(skip).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def get_comment(post_id: int, comment_id: int,
                      db: AsyncSession) -> Comment | None:
    """
    Retrieves a comment from the database based on the provided post ID and comment ID.

    Args:
        post_id (int): The ID of the post.
        comment_id (int): The ID of the comment.
        db (AsyncSession): The database session.

    Returns:
        Comment | None: The retrieved comment, or None if no comment is found.
    """
    stmt = select(Comment).filter_by(post_id=post_id,
                                     id=comment_id, blocked=False)
    comment = await db.execute(stmt)
    return comment.scalar_one_or_none()

async def create_comment(body: CommentCreate, post_id: int,
                         user: User, db: AsyncSession) -> Comment:
    """
    Creates a new comment for a specific post.

    Args:
        body (CommentCreate): The comment data.
        post_id (int): The ID of the post.
        user (User): The user who made the comment.
        db (AsyncSession): The database session.

    Returns:
        Comment: The newly created comment.
    """
    blocked = False
    v = body.comment_text
    words = v.lower().split()
    bad_words_in_text = WORDS.intersection(words)
    if bad_words_in_text:
        blocked = True
    comment = Comment(
        post_id=post_id,
        user_id=user.id,
        **body.model_dump(exclude_unset=True),
        blocked=blocked
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    if comment.auto_reply_flag == True:
        sleep(comment.auto_reply_time)
        reply_text = generate_relevant_response(comment.comment_text)
        await create_comment(CommentCreate(comment_text=reply_text,
                                           auto_reply_flag=False), post_id, user, db)
    return comment

async def update_comment(comment_id: int, body: CommentCreate,
                         post: Post, user: User, db: AsyncSession) -> Comment | None:
    """
    Updates a comment in the database with the provided comment ID, comment data, post, user, and database session.

    Args:
        comment_id (int): The ID of the comment to be updated.
        body (CommentCreate): The updated comment data.
        post (Post): The post associated with the comment.
        user (User): The user who made the comment.
        db (AsyncSession): The database session.

    Returns:
        Comment | None: The updated comment, or None if the comment does not exist.
    """
    stmt = select(Comment).filter_by(id=comment_id,
                                     post_id=post.id, user_id=user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        comment = Comment(
            post_id=post.id,
            user_id=user.id,
            **body.model_dump(exclude_unset=True)
        )
        await db.commit()
    return comment

async def remove_comment(comment_id: int, post: Post,
                         user: User, db: AsyncSession) -> Comment | None:
    """
    Removes a comment from the database based on the provided comment ID, post, user, and database session.

    Args:
        comment_id (int): The ID of the comment to be removed.
        post (Post): The post associated with the comment.
        user (User): The user who made the comment.
        db (AsyncSession): The database session.

    Returns:
        Comment | None: The removed comment, or None if the comment does not exist.
    """
    stmt = select(Comment).filter_by(id=comment_id,
                                     post_id=post.id, user_id=user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment

def generate_relevant_response(comment_text: str) -> str:
    """
    Generates a relevant response based on the content of the given comment.

    Args:
        comment_text (str): The text of the comment.

    Returns:
        str: The relevant response. Possible values are:
            - "Thanks for your question! We will help you soon." if the comment contains the word "help".
            - "Sorry to hear about your issue. We are looking into it." if the comment contains the word "issue".
            - "Thank you for your comment!" for any other comment.
    """
    if 'help' in comment_text.lower():
        return "Thanks for your question! We will help you soon."
    elif 'issue' in comment_text.lower():
        return "Sorry to hear about your issue. We are looking into it."
    else:
        return "Thank you for your comment!"
    