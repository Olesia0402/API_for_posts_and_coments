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
    
    stmt = select(Comment).filter_by(post_id=post_id, blocked=False).offset(skip).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def get_my_comments_to_post(skip: int, limit: int,
                                  post_id: int, user: User, db: AsyncSession) -> List[Comment]:
    stmt = select(Comment).filter_by(post_id=post_id, user_id=user.id, blocked=False).offset(skip).limit(limit)
    comments = await db.execute(stmt)
    return comments.scalars().all()


async def get_comment(post_id: int, comment_id: int,
                      db: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter_by(post_id=post_id, id=comment_id, blocked=False)
    comment = await db.execute(stmt)
    return comment.scalar_one_or_none()

async def create_comment(body: CommentCreate, post_id: int,
                         user: User, db: AsyncSession) -> Comment:
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
        await create_comment(CommentCreate(comment_text=reply_text, auto_reply_flag=False), post_id, user, db)

    return comment

async def update_comment(comment_id: int, body: CommentCreate,
                         post: Post, user: User, db: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter_by(id=comment_id, post_id=post.id, user_id=user.id)
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
    stmt = select(Comment).filter_by(id=comment_id, post_id=post.id, user_id=user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment

def generate_relevant_response(comment_text: str) -> str:
    if 'help' in comment_text.lower():
        return "Thanks for your question! We will help you soon."
    elif 'issue' in comment_text.lower():
        return "Sorry to hear about your issue. We are looking into it."
    else:
        return "Thank you for your comment!"
    