import json
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.future import select

from src.database.models import Post, User
from src.schemas.schemas import PostCreate

with open ("src/schemas/words_template.json") as file:
    WORDS = set(json.load(file)["words"])


async def get_all_posts(skip: int, limit: int, db: AsyncSession) -> List[Post]:
    """
    Retrieves a list of posts from the database, excluding any blocked posts.

    Args:
        skip (int): The number of posts to skip.
        limit (int): The maximum number of posts to retrieve.
        db (AsyncSession): The database session.

    Returns:
        List[Post]: A list of Post objects representing the retrieved posts.
    """
    stmt = select(Post).filter_by(blocked=False).offset(skip).limit(limit).options(selectinload(Post.comments))
    posts = await db.execute(stmt)
    return posts.scalars().all()


async def get_my_posts(skip: int, limit: int, user: User, db: AsyncSession) -> List[Post]:
    """
    Retrieves a list of posts made by a specific user from the database, excluding any blocked posts.

    Args:
        skip (int): The number of posts to skip.
        limit (int): The maximum number of posts to retrieve.
        user (User): The user whose posts are being retrieved.
        db (AsyncSession): The database session.

    Returns:
        List[Post]: A list of Post objects representing the retrieved posts.
    """
    stmt = select(Post).filter_by(user_id=user.id,
                                  blocked=False).offset(skip).limit(limit).options(selectinload(Post.comments))
    posts = await db.execute(stmt)
    return posts.scalars().all()


async def get_post(post_id: int, db: AsyncSession) -> Post:
    """
    Retrieves a post from the database based on the provided post ID, excluding any blocked posts.

    Args:
        post_id (int): The ID of the post to retrieve.
        db (AsyncSession): The database session.

    Returns:
        Post: The retrieved post, or None if no post is found.
    """
    stmt = select(Post).filter_by(id=post_id,
                                  blocked=False).options(selectinload(Post.comments))
    post = await db.execute(stmt)
    return post.scalar_one_or_none()


async def create_post(body: PostCreate, user: User, db: AsyncSession) -> Post:
    """
    Creates a new post in the database based on the provided data.

    Args:
        body (PostCreate): The post data to be created.
        user (User): The user who is creating the post.
        db (AsyncSession): The database session.

    Returns:
        Post: The newly created post.
    """
    blocked = False
    
    words = body.post_text.lower().split()
    bad_words_in_text = WORDS.intersection(words)
    if bad_words_in_text:
        blocked = True
    
    post = Post(post_text=body.post_text,
                post_download=body.post_download,
                user_id=user.id,
                blocked=blocked)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def update_post(post_id: int, body: PostCreate, user: User, db: AsyncSession) -> Post | None:
    """
    Updates a post in the database based on the provided post ID, post data, user, and database session.

    Args:
        post_id (int): The ID of the post to be updated.
        body (PostCreate): The updated post data.
        user (User): The user who made the post.
        db (AsyncSession): The database session.

    Returns:
        Post | None: The updated post, or None if the post does not exist.
    """
    stmt = select(Post).filter_by(id=post_id,
                                  user_id=user.id).options(selectinload(Post.comments))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post:
        v = body.post_text
        words = v.lower().split()
        bad_words_in_text = WORDS.intersection(words)
        if bad_words_in_text != None:
            blocked = True
        post = Post(post_text=body.post_text,
                post_download=body.post_download,
                user_id=user.id,
                blocked=blocked)
        await db.commit()
    return post


async def remove_post(post_id: int, user: User, db: AsyncSession) -> Post | None:
    """
    Removes a post from the database based on the provided post ID, user, and database session.

    Args:
        post_id (int): The ID of the post to be removed.
        user (User): The user who made the post.
        db (AsyncSession): The database session.

    Returns:
        Post | None: The removed post, or None if the post does not exist.
    """
    stmt = select(Post).filter_by(id=post_id,
                                  user_id=user.id).options(selectinload(Post.comments))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post:
        await db.delete(post)
        await db.commit()
    return post
