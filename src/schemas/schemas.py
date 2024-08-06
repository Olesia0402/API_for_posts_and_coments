from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime | None
    avatar: str
    confirmed: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CommentBase(BaseModel):
    comment_text: str
    done: bool = False

class CommentCreate(CommentBase):
    auto_reply_flag: bool = False
    auto_reply_time: Optional[int] = None

class CommentResponse(CommentBase):
    id: int
    blocked: bool
    created_at: datetime
    update_at: Optional[datetime] = None
    user_id: int
    post_id: int

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    post_text: str
    post_download: Optional[str] = None
    done: bool = False

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    blocked: bool
    created_at: Optional[datetime]
    update_at: Optional[datetime] = None
    user_id: int
    comments: Optional[List[CommentResponse]] = []

    class Config:
        from_attributes = True
        

class RequestEmail(BaseModel):
    email: EmailStr
