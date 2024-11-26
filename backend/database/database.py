from typing import List, Union
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from models.admin import Admin
from models.student import Student
from models.requirements import RequirementsDocument
import os

admin_collection = Admin
student_collection = Student


async def init_db():
    # Get MongoDB URI from environment variable
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/omnipedia")
    
    # Create Motor client
    client = AsyncIOMotorClient(mongodb_uri)
    
    # Initialize beanie with the document models
    await init_beanie(
        database=client.get_default_database(),
        document_models=[RequirementsDocument]
    )


async def add_admin(new_admin: Admin) -> Admin:
    admin = await new_admin.create()
    return admin
