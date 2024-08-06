import pandas as pd

from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.db import get_db
from src.database.models import User, Comment
from src.schemas.schemas import PostCreate, PostResponse
from src.repository import posts as repository_posts
from src.services.auth import auth_service


router = APIRouter(prefix='/posts', tags=["posts"])


@router.get("/", response_model=List[PostResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_posts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    posts = await repository_posts.get_all_posts(skip, limit, db)
    return posts


@router.get("/my", response_model=List[PostResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_my_posts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    posts = await repository_posts.get_my_posts(skip, limit, current_user, db)
    return posts


@router.get("/{post_id}", response_model=PostResponse)
async def read_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await repository_posts.get_post(post_id, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, description='No more than 2 posts per 5 minutes',
             dependencies=[Depends(RateLimiter(times=2, seconds=300))])
async def create_post(body: PostCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    try:
        post = await repository_posts.create_post(body, current_user, db)
        if post.blocked == True:
            return f"Text contains inappropriate language. The post has been blocked."
        return post
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(body: PostCreate, post_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    try:        
        post = await repository_posts.update_post(post_id, body, current_user, db)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return post
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{post_id}", response_model=PostResponse)
async def remove_post(post_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    post = await repository_posts.remove_post(post_id, current_user, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("/{post_id}/comments-daily-breakdown", response_model=Dict)
async def get_daily_breakdown(post_id: int, date_from: datetime, date_to: datetime,
                              db: AsyncSession = Depends(get_db)):
    if date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date from must be earlier than date to")
        
    list_of_dates = pd.date_range(date_from.date(), date_to.date()).tolist()
    result = dict()

    for date in list_of_dates:
        stmt = select(Comment).filter_by(post_id=post_id)
        comments = await db.execute(stmt)
        comments = comments.scalars().all()
        comments = [comment for comment in comments if (comment.created_at >= date) and (comment.created_at < date + timedelta(days=1))]
        result[date.strftime("%Y-%m-%d")] = {'total_count_of_comments': len(comments),
                        'blocked_count_of_comments': len([comment for comment in comments if comment.blocked == True]),
                        'unblocked_count_of_comments': len([comment for comment in comments if comment.blocked == False])}

    return result