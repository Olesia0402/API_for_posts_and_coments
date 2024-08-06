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
    return {"message": "Hello World"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
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