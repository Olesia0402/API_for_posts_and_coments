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
    stmt = select(Post).filter_by(blocked=False).offset(skip).limit(limit).options(selectinload(Post.comments))
    posts = await db.execute(stmt)
    return posts.scalars().all()


async def get_my_posts(skip: int, limit: int, user: User, db: AsyncSession) -> List[Post]:
    stmt = select(Post).filter_by(user_id=user.id, blocked=False).offset(skip).limit(limit).options(selectinload(Post.comments))
    posts = await db.execute(stmt)
    return posts.scalars().all()


async def get_post(post_id: int, db: AsyncSession) -> Post:
    stmt = select(Post).filter_by(id=post_id, blocked=False).options(selectinload(Post.comments))
    post = await db.execute(stmt)
    return post.scalar_one_or_none()


async def create_post(body: PostCreate, user: User, db: AsyncSession) -> Post:
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
    stmt = select(Post).filter_by(id=post_id, user_id=user.id).options(selectinload(Post.comments))
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
    stmt = select(Post).filter_by(id=post_id, user_id=user.id).options(selectinload(Post.comments))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post:
        await db.delete(post)
        await db.commit()
    return post
