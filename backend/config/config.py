from typing import Optional
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
import models as models
import os

class Settings(BaseSettings):
    # database configurations
    MONGODB_URI: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    MONGO_INITDB_ROOT_USERNAME: Optional[str] = None
    MONGO_INITDB_ROOT_PASSWORD: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # JWT
    secret_key: str = "secret"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env.dev"
        from_attributes = True

settings = Settings()

async def initiate_database():
    # Get credentials from environment or use defaults
    username = settings.MONGO_INITDB_ROOT_USERNAME or "root"
    password = settings.MONGO_INITDB_ROOT_PASSWORD or "example"
    
    # Use the MONGODB_URI from environment if available, otherwise construct it
    if settings.MONGODB_URI:
        mongodb_uri = settings.MONGODB_URI
    else:
        # When running locally, use localhost
        mongodb_uri = f"mongodb://{username}:{password}@localhost:27017/omnipedia?authSource=admin"
    
    print(f"Connecting to MongoDB with URI: {mongodb_uri}")  # Debug print
    
    client = AsyncIOMotorClient(mongodb_uri)
    
    # Initialize beanie with all document models
    await init_beanie(
        database=client.get_default_database(),
        document_models=models.__all__
    )