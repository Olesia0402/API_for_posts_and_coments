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
    comments = await repository_comments.get_all_comments(skip, limit, post_id, db)
    return [comment for comment in comments if comment.blocked == False]

@router.get("/my", response_model=List[CommentResponse], description='No more than 20 requests per minute',
            dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def read_my_comments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
                           post_id: int = None, current_user: User = Depends(auth_service.get_current_user)):
    comments = await repository_comments.get_my_comments_to_post(skip, limit, post_id, current_user, db)
    return [comment for comment in comments if comment.blocked == False]

@router.get("/{comment_id}", response_model=CommentResponse)
async def read_comment(post_id: int, comment_id: int, db: AsyncSession = Depends(get_db)):
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
    try:
        comment = await repository_comments.create_comment(body, post_id, current_user, db)
        return comment
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(body: CommentCreate, comment_id: int, post_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
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
    comment = await repository_comments.remove_comment(post_id, comment_id, current_user, db)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


