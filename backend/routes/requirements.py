import logging
from fastapi import APIRouter, HTTPException
from database.database import *
from models.requirements import RequirementsDocument

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@router.get("/requirements/{request_id}")
async def get_requirements(request_id: str):
    try:
        if not request_id or not isinstance(request_id, str):
            logger.error(f"Invalid request ID format: {request_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid request ID format"
            )

        doc = await RequirementsDocument.find_one({"request_id": request_id})
        if not doc:
            logger.warning(f"Requirements not found for request_id: {request_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Requirements not found for request_id: {request_id}"
            )

        if not hasattr(doc, 'requirements') or not doc.requirements:
            logger.error(f"Requirements document {request_id} has no requirements data")
            raise HTTPException(
                status_code=422,
                detail="Requirements document exists but contains no data"
            )

        logger.info(f"Successfully retrieved requirements for request_id: {request_id}")
        return {
            "status": "success",
            "data": doc.requirements,
            "request_id": request_id
        }

    except HTTPException as he:
        logger.error(f"HTTP error for request {request_id}: {str(he)}")
        raise he

    except AttributeError as ae:
        # Handle cases where document structure is invalid
        error_msg = f"Invalid document structure for request {request_id}: {str(ae)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Unexpected error retrieving requirements for request {request_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)  # This will log the full stack trace
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/requirements")
async def get_requirements():
    try:

        docs = await RequirementsDocument.find_all().to_list()
        
        if not docs:
            logger.warning("No requirements documents found")
            return {
                "status": "success",
                "data": [],
                "count": 0
            }

        requirements_list = [
            {
                "title": doc.title,
                "request_id": doc.request_id,
                "requirements": doc.requirements
            }
            for doc in docs
            if hasattr(doc, 'requirements') and doc.requirements
        ]

        logger.info(f"Successfully retrieved {len(requirements_list)} requirements documents")
        
        return {
            "status": "success",
            "data": requirements_list,
            "count": len(requirements_list)
        }

    except Exception as e:
        error_msg = f"Unexpected error retrieving all requirements: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)
