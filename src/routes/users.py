from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from config import settings
from src.schemas.schemas import UserDb

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    
    """
    The read_users_me function is a GET endpoint that returns the current user's information.

    :param current_user: User: Get the current user
    :return: The current_user object
    :doc-author: Trelent
    """
    
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: AsyncSession = Depends(get_db)):
    
    """
    The update_avatar_user function updates the avatar of a user.

    :param file: UploadFile: Upload the file to cloudinary
    :param current_user: User: Get the current user from the database
    :param db: AsyncSession: Get the database session
    :return: The user with the updated avatar
    :doc-author: Trelent
    """
    
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )

    contents = await file.read()
    r = cloudinary.uploader.upload(contents, public_id=f"user_{current_user.id}_avatar")
    url, options = cloudinary_url(r['public_id'], width=100, height=150, crop="fill")
    
    user = await repository_users.update_avatar(current_user.email, url, db)
    return user