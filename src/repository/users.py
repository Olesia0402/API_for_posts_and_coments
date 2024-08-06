from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.models import User
from src.schemas.schemas import UserModel


async def get_user_by_email(email: str, db: AsyncSession) -> User:
    """
    Retrieves a user from the database based on their email address.

    Args:
        email (str): The email address of the user to retrieve.
        db (AsyncSession): The database session to use for querying.

    Returns:
        User | None: The user object if found, None otherwise.
    """

    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession) -> User:
    """
    Creates a new user in the database with the provided user data and database session.

    Args:
        body (UserModel): The user data to create.
        db (AsyncSession): The database session to use for creating the user.

    Returns:
        User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirms the email address of a user in the database.

    Args:
        email (str): The email address of the user to confirm.
        db (AsyncSession): The database session to use for updating the user.

    Returns:
        None
    """
    user = await get_user_by_email(email, db)
    if user:
        user.confirmed = True
        await db.commit()

    
async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """
    Updates the refresh token of a user in the database.

    Args:
        user (User): The user object to update.
        token (str | None): The new refresh token to set.
        db (AsyncSession): The database session to use for updating the user.

    Returns:
        None
    """
    user.refresh_token = token
    await db.commit()

async def update_avatar(email, url: str, db: AsyncSession) -> User:
    """
    Updates the avatar of a user in the database.

    Args:
        email (str): The email address of the user to update.
        url (str): The new avatar URL to set.
        db (AsyncSession): The database session to use for updating the user.

    Returns:
        User
    """
    user = await get_user_by_email(email, db)
    if user:
        user.avatar = url
        await db.commit()
        await db.refresh(user)
        return user
    