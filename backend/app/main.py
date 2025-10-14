from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routes import router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS configuration for local development (frontend on 3000/3001)
allowed_origins = [
    os.environ.get("MYMITRA_WEB_ORIGIN", "http://localhost:3000"),
    "http://localhost:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
