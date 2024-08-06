from sqlalchemy import Column, Integer, String, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now(), nullable=True)
    avatar = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False, nullable=True)
    refresh_token = Column(String(255), nullable=True)

    posts = relationship("Post", back_populates="user", lazy='selectin')
    comments = relationship("Comment", back_populates="user", lazy='selectin')


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    post_text = Column(String(), nullable=False)
    post_download = Column(String(), nullable=True)
    done = Column(Boolean, default=False)
    created_at = Column('created_at', DateTime, default=func.now(), nullable=True)
    update_at = Column('update_at', DateTime, default=func.now(), onupdate=func.now(), nullable=True)
    blocked = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="posts", lazy='selectin')
    comments = relationship("Comment", back_populates="post", lazy='selectin')


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    comment_text = Column(String(), nullable=False)
    done = Column(Boolean, default=False)
    created_at = Column('created_at', DateTime, default=func.now(), nullable=True)
    update_at = Column('update_at', DateTime, default=func.now(), onupdate=func.now(), nullable=True)
    blocked = Column(Boolean, default=False)
    auto_reply_flag = Column(Boolean, default=False)
    auto_reply_time = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    user = relationship("User", back_populates="comments", lazy='selectin')
    post = relationship("Post", back_populates="comments", lazy='selectin')
