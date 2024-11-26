from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from auth.jwt_bearer import JWTBearer
from config.config import initiate_database
from routes.admin import router as AdminRouter
# from routes.evaluate import router as EvaluateRouter
from routes.extract import router as ExtractRouter
from routes.requirements import router as RequirementsRouter
from dotenv import load_dotenv
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initiate_database()
    yield

app = FastAPI(lifespan=lifespan)  # Add lifespan here
token_listener = JWTBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app."}

app.include_router(AdminRouter, tags=["Administrator"], prefix="/admin")
app.include_router(ExtractRouter, tags=["Extract"], prefix="/api")
app.include_router(RequirementsRouter, tags=["Requirements"], prefix="/api")
# app.include_router(EvaluateRouter, tags=["Evaluate"], prefix="/api")
