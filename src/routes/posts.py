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
    """
    Retrieves a list of posts from the database.

    Args:
        skip (int): The number of posts to skip. Defaults to 0.
        limit (int): The maximum number of posts to retrieve. Defaults to 100.
        db (AsyncSession): The database session. Defaults to the result of the `get_db` function.

    Returns:
        List[PostResponse]: A list of PostResponse objects representing the retrieved posts.

    Raises:
        None

    Notes:
        - The function is decorated with `@router.get` to define a GET endpoint for the `/` path.
        - The endpoint returns a list of PostResponse objects.
        - The function is rate-limited to no more than 10 requests per minute.
        - The `skip` and `limit` parameters are used to paginate the results.
    """
    posts = await repository_posts.get_all_posts(skip, limit, db)
    return posts


@router.get("/my", response_model=List[PostResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_my_posts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a list of posts made by the current user from the database.

    Args:
        skip (int): The number of posts to skip. Defaults to 0.
        limit (int): The maximum number of posts to retrieve. Defaults to 100.
        db (AsyncSession): The database session. Defaults to the result of the `get_db` function.
        current_user (User): The current user. Defaults to the result of the `get_current_user` function.

    Returns:
        List[PostResponse]: A list of PostResponse objects representing the retrieved posts.

    Raises:
        None

    Notes:
        - The function is decorated with `@router.get` to define a GET endpoint for the `/my` path.
        - The endpoint returns a list of PostResponse objects.
        - The function is rate-limited to no more than 10 requests per minute.
        - The `skip` and `limit` parameters are used to paginate the results.
    """
    posts = await repository_posts.get_my_posts(skip, limit, current_user, db)
    return posts


@router.get("/{post_id}", response_model=PostResponse)
async def read_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a specific post by its ID from the database.

    Args:
        post_id (int): The ID of the post to retrieve.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.

    Returns:
        PostResponse: The retrieved post, or raises an HTTPException if the post is not found.

    Raises:
        HTTPException: If the post is not found.
    """
    post = await repository_posts.get_post(post_id, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, description='No more than 2 posts per 5 minutes',
             dependencies=[Depends(RateLimiter(times=2, seconds=300))])
async def create_post(body: PostCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    """
    Create a new post.

    Args:
        body (PostCreate): The data for the new post.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.
        current_user (User, optional): The current user creating the post. Defaults to the result of the `auth_service.get_current_user` function.

    Returns:
        PostResponse: The newly created post.

    Raises:
        HTTPException: If an error occurs during post creation.

    Notes:
        - The function is decorated with `@router.post` to define a POST endpoint for the `/` path.
        - The endpoint returns a `PostResponse` object representing the newly created post.
        - The function is rate-limited to no more than 2 posts per 5 minutes.
        - If the post contains inappropriate language, the function returns a string message indicating that the post has been blocked.
        - If an error occurs during post creation, the function raises an `HTTPException` with a status code of `500` and a detail message indicating the error.
    """
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
    """
    Updates a post with the given post ID.

    Args:
        body (PostCreate): The updated post data.
        post_id (int): The ID of the post to be updated.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.
        current_user (User, optional): The current user updating the post. Defaults to the result of the `auth_service.get_current_user` function.

    Returns:
        PostResponse: The updated post.

    Raises:
        HTTPException: If the post is not found or an error occurs during the update.
    """
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
    """
    Delete a post by its ID.

    Args:
        post_id (int): The ID of the post to be deleted.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.
        current_user (User, optional): The current user deleting the post. Defaults to the result of the `auth_service.get_current_user` function.

    Returns:
        PostResponse: The deleted post.

    Raises:
        HTTPException: If the post is not found.
    """
    post = await repository_posts.remove_post(post_id, current_user, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("/{post_id}/comments-daily-breakdown", response_model=Dict)
async def get_daily_breakdown(post_id: int, date_from: datetime, date_to: datetime,
                              db: AsyncSession = Depends(get_db)):
    """
    Retrieves a daily breakdown of comments for a specific post within a given date range.

    Parameters:
        post_id (int): The ID of the post.
        date_from (datetime): The start date of the range.
        date_to (datetime): The end date of the range.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.

    Returns:
        Dict: A dictionary containing the daily breakdown of comments. The keys are the dates in the format "YYYY-MM-DD" and the values are dictionaries with the following keys:
            - total_count_of_comments (int): The total number of comments for that date.
            - blocked_count_of_comments (int): The number of blocked comments for that date.
            - unblocked_count_of_comments (int): The number of unblocked comments for that date.

    Raises:
        HTTPException: If the `date_from` is later than `date_to`.
    """
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