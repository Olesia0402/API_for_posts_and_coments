from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User
from src.schemas.schemas import CommentCreate, CommentResponse
from src.repository import comments as repository_comments
from src.services.auth import auth_service

router = APIRouter(prefix='/posts/{post_id}', tags=["comments"])

@router.get("/", response_model=List[CommentResponse], description='No more than 20 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_comments(skip: int = 0, limit: int = 100, post_id: int = None, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a list of comments for a given post.

    Args:
        skip (int): The number of comments to skip. Defaults to 0.
        limit (int): The maximum number of comments to retrieve. Defaults to 100.
        post_id (int, optional): The ID of the post. Defaults to None.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.

    Returns:
        List[CommentResponse]: A list of CommentResponse objects representing the retrieved comments.
            Only the comments that are not blocked are included in the list.

    Raises:
        None

    Notes:
        - The function is decorated with `@router.get` to define a GET endpoint for the `/` path.
        - The endpoint returns a list of CommentResponse objects.
        - The function is rate-limited to no more than 20 requests per minute.
        - The `skip` and `limit` parameters are used to paginate the results.
        - The `post_id` parameter is used to filter the comments by post ID.
        - The `db` parameter is used to provide the database session.
    """
    comments = await repository_comments.get_all_comments(skip, limit, post_id, db)
    return [comment for comment in comments if comment.blocked == False]

@router.get("/my", response_model=List[CommentResponse], description='No more than 20 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_my_comments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
                           post_id: int = None, current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a list of comments for a given post.

    Args:
        skip (int): The number of comments to skip. Defaults to 0.
        limit (int): The maximum number of comments to retrieve. Defaults to 100.
        db (AsyncSession): The database session. Defaults to the result of the `get_db` function.
        post_id (int): The ID of the post. Defaults to None.
        current_user (User): The current user. Defaults to the result of the `get_current_user` function.

    Returns:
        List[CommentResponse]: A list of CommentResponse objects representing the retrieved comments.
            Only the comments that are not blocked are included in the list.

    Notes:
        - The function is decorated with `@router.get` to define a GET endpoint for the `/my` path.
        - The endpoint returns a list of CommentResponse objects.
        - The function is rate-limited to no more than 20 requests per minute.
    """
    comments = await repository_comments.get_my_comments_to_post(skip, limit, post_id, current_user, db)
    return [comment for comment in comments if comment.blocked == False]

@router.get("/{comment_id}", response_model=CommentResponse)
async def read_comment(post_id: int, comment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a specific comment by its ID.

    Args:
        post_id (int): The ID of the post that the comment belongs to.
        comment_id (int): The ID of the comment to retrieve.
        db (AsyncSession): The database session. Defaults to the result of the `get_db` function.

    Returns:
        CommentResponse: The retrieved comment, or raises an HTTPException if the comment is not found or has been blocked.
    """
    comment = await repository_comments.get_comment(post_id, comment_id, db)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    elif comment.blocked == True:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment has been blocked")
    return comment

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, 
             description='No more than 2 posts per 5 minutes',
             dependencies=[Depends(RateLimiter(times=2, seconds=300))])
async def create_comment(body: CommentCreate, post_id: int, 
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Creates a new comment associated with a specific post.

    Args:
        body (CommentCreate): The data for the new comment.
        post_id (int): The ID of the post the comment is related to.
        db (AsyncSession): The database session. Defaults to the result of the `get_db` function.
        current_user (User): The current user creating the comment.

    Returns:
        CommentResponse: The newly created comment.

    Raises:
        HTTPException: If an error occurs during comment creation.
    """
    try:
        comment = await repository_comments.create_comment(body, post_id, current_user, db)
        return comment
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(body: CommentCreate, comment_id: int, post_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Updates a comment with the given comment ID and post ID.

    Args:
        body (CommentCreate): The updated comment data.
        comment_id (int): The ID of the comment to be updated.
        post_id (int): The ID of the post the comment is related to.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.
        current_user (User, optional): The current user updating the comment. Defaults to the result of the `auth_service.get_current_user` function.

    Returns:
        CommentResponse: The updated comment.

    Raises:
        HTTPException: If the comment is not found or an error occurs during the update.
    """
    try:  
        comment = await repository_comments.update_comment(post_id, comment_id, body, current_user, db)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return comment
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{comment_id}", response_model=CommentResponse)
async def remove_comment(post_id: int, comment_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Delete a comment by its ID and post ID.

    Args:
        post_id (int): The ID of the post that the comment belongs to.
        comment_id (int): The ID of the comment to be deleted.
        db (AsyncSession, optional): The database session. Defaults to the result of the `get_db` function.
        current_user (User, optional): The current user deleting the comment. Defaults to the result of the `auth_service.get_current_user` function.

    Returns:
        CommentResponse: The deleted comment.

    Raises:
        HTTPException: If the comment is not found.
    """
    comment = await repository_comments.remove_comment(post_id, comment_id, current_user, db)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


