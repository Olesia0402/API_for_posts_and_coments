import uvicorn
import os
from pathlib import Path
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import comments, posts, auth, users
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    r = await Redis(
        host=settings.REDIS_DOMAIN,
        port=settings.REDIS_PORT,
        db=0
    )
    await FastAPILimiter.init(r)

    yield

app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:3000",
    "localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = Path(__file__).parent

app.include_router(auth.router, prefix='/api')
app.include_router(posts.router, prefix='/api')
app.include_router(comments.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.get("/")
def read_root():
    """
    A function that handles the GET request to the root URL ("/"). It returns a JSON response
    with a message "Hello World".

    Returns:
        dict: A dictionary containing a message "Hello World".
    """
    return {"message": "Hello World"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Health checker endpoint for the API.

    This endpoint is used to check the health of the API and the database connection.
    It makes a request to the database to execute a simple query and checks if the result is not None.
    If the result is None, it raises an HTTPException with a status code of 500 and a detail message indicating that the database is not configured correctly.
    If the result is not None, it returns a JSON response with a message welcoming the user to FastAPI.

    Parameters:
    - db (AsyncSession): An asynchronous session object representing the database connection. It is obtained from the get_db dependency.

    Returns:
    - dict: A dictionary containing a message welcoming the user to FastAPI.

    Raises:
    - HTTPException: If there is an error connecting to the database, an HTTPException is raised with a status code of 500 and a detail message indicating the error.

    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")