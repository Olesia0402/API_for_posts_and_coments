from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_confirm_email, send_reset_email, send_update_email

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks,
                 request: Request, db: AsyncSession = Depends(get_db)):
    """
    The signup function creates a new user in the database.
    It takes in three parameters, body, background_tasks, and request. The body parameter is a
    Pydantic model that contains the data for the new user. The background_tasks parameter is a
    BackgroundTasks object that allows us to add tasks to be run in the background. The request
    parameter is a Request object that contains information about the incoming request. The db
    parameter is a database session object that we will use to add the new user to the database.

    :param body: UserModel: Get the data from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base URL of the application
    :param db: AsyncSession: Start a database session
    :return: A dictionary with a user and a detail	
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_confirm_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user. It takes in an email and password, and
    returns an access token if the user is authenticated successfully.
    :param body: OAuth2PasswordRequestForm: Get the username and password from the request
    :param db: AsyncSession: Pass the database session to the repository
    :return: The access token
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token. It takes in an access token
    and a refresh token, and returns a new access token if the refresh token is valid.
    :param credentials: HTTPAuthorizationCredentials: Get the access token from the request
    :param db: AsyncSession: Pass the database session to the repository
    :return: The access token
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email. It takes in a token and
    returns a message if the token is valid.
    :param token: str: Pass in the token that was sent to the user
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed == True:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}

@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send a confirmation email to the user's email address.
    It takes in a RequestEmail object, which contains the user's email address, and sends
    a confirmation email to that address. The function also takes in a BackgroundTasks object,
    which is used to send the email in the background. The request object is also passed in
    to the function.
    :param body: RequestEmail: Pass in the email address of the user
    :param background_tasks: BackgroundTasks: Send the email in the background
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_confirm_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}

@router.post("/forget_password")
async def forget_password(background_tasks: BackgroundTasks, user: UserModel, request: Request,
                            db: AsyncSession = Depends(get_db)):
    """
    The forget_password function is used to send a reset password email to the user's email address.
    It takes in a background_tasks parameter, which is used to send the email in the background.
    The user parameter is a UserModel object, which contains the email address of the user. The
    request object is also passed in to the function.
    :param background_tasks: BackgroundTasks: Send the email in the background
    :param user: UserModel: Get the email of the user
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    user_in_db = await repository_users.get_user_by_email(user.email, db)    
    if user_in_db:
        background_tasks.add_task(send_reset_email, user_in_db.email, user_in_db.username, request.base_url)
    return {"message": "Check your email for reset password."}
    

@router.post("/reset_password/{token:str}")
async def reset_password(token: str, body: UserModel, background_tasks: BackgroundTasks, request: Request,
                         db: AsyncSession = Depends(get_db)):
    """
    The reset_password function is used to reset the password of a user. It takes in a token and
    a body, and returns a message if the token is valid.
    :param token: str: Get the token from the request
    :param body: UserModel: Get the password from the request body
    :param background_tasks: BackgroundTasks: Send the email in the background
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Pass the database session to the repository
    :return: A message
    """
    email = await auth_service.get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = await repository_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password = auth_service.get_password_hash(body.password)
    updated_user = await repository_users.update_password(user, db)
    background_tasks.add_task(send_update_email, user.email, user.username, request.base_url)
    return {"user": updated_user, "detail": "Password successfully reset. Check your email for confirmation."}