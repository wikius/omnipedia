import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from database.database import *
from prompts.extract.extract_deduped import process_requirements
from prompts.extract.format import convert_wikitext
from utils.wikitext import fetch_wikitext
from pydantic import BaseModel
from typing import Optional
from models.requirements import RequirementsDocument
import uuid

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

router = APIRouter()


class StyleGuideInput(BaseModel):
    content: Optional[str] = None
    url: Optional[str] = None

    @property
    def input_content(self) -> str:
        if self.url is not None:
            return self.url
        if self.content is not None:
            return self.content
        raise ValueError("Either url or content must be provided")

    @property
    def is_url(self) -> bool:
        return self.url is not None or (self.content is not None and str(self.content).startswith(("http://", "https://")))


@router.post("/extract")
async def extract_requirements(data: StyleGuideInput, background_tasks: BackgroundTasks):
    try:
        # Validate input
        try:
            content = data.input_content
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=str(e)
            )

        # Check if it's a URL
        if data.is_url:
            # Check if we already have this URL in the database
            existing_doc = await RequirementsDocument.find_one({"url": content})
            if existing_doc:
                logger.info(f"Found existing requirements for URL: {content}")
                return {
                    "status_code": 200,
                    "response_type": "success",
                    "description": "Retrieved existing requirements",
                    "data": {
                        "request_id": existing_doc.request_id
                    },
                }

        # Generate UUID for new request
        request_id = str(uuid.uuid4())
        
        # Add the processing task to background tasks
        background_tasks.add_task(process_and_save_requirements, data, request_id)
        
        logger.info(f"Request accepted for processing with request_id: {request_id}")
        return {
            "status_code": 202,
            "response_type": "success",
            "description": "Request accepted for processing",
            "data": {
                "request_id": request_id
            },
        }
    except HTTPException as he:
        logger.error(f"HTTP error in request: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_and_save_requirements(data: StyleGuideInput, request_id: str):
    try:
        style_guide_content = None
        content = data.input_content
        url = data.url or (content if data.is_url else None)
        
        if data.is_url:
            try:
                wikitext_content = fetch_wikitext(content)
                if not wikitext_content:
                    raise ValueError("No content retrieved from URL")
                style_guide_content = wikitext_content
            except Exception as url_error:
                logger.error(f"Error fetching content from URL: {str(url_error)}")
                raise ValueError(f"Failed to fetch content from URL: {str(url_error)}")
        else:
            style_guide_content = content

        if not style_guide_content:
            raise ValueError("No content to process")

        title, requirements_data = await process_requirements(style_guide_content)
        
        # Create a document that matches the RequirementsDocument model
        doc = RequirementsDocument(
            request_id=request_id,
            requirements=requirements_data,
            status="completed",
            url=url,
            title=title
        )
        
        # Save requirements to database
        await doc.insert()
        logger.info(f"Successfully saved requirements to database for request_id: {request_id}")
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
        # Update document with error status if possible
        try:
            error_doc = RequirementsDocument(
                request_id=request_id,
                requirements={},
                status="error",
                url=url
            )
            await error_doc.insert()
        except Exception as db_error:
            logger.error(f"Failed to save error status for request {request_id}: {str(db_error)}")
