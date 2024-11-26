from pydantic import BaseModel
from typing import List, Dict
import json
import re
import os
import logging
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create file handler for debug logging
file_handler = logging.FileHandler('requirements_extraction.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

load_dotenv()

class Requirement(BaseModel):
    id: str = Field(description="Unique identifier in the format 'R{id}'")
    description: str = Field(description="Brief description of the requirement")
    reference: str = Field(description="Exact quote from the style guide")
    category: str = Field(description="Requirement type")
    classification: str = Field(description="Classification of the requirement")
    where: str = Field(description="Where the requirement should be applied")
    when: str = Field(description="When the requirement should be applied")
    level: str = Field(
        description="Level of the requirement (sentence-level, section-level, article-level)"
    )


class Group(BaseModel):
    description: str = Field(description="Description of the group")
    category: str = Field(
        description="Category of the group (e.g., 'Language Usage', 'Formatting', etc.)"
    )
    requirements: List[Requirement] = Field(default_factory=list)


class RequirementsDocument(BaseModel):
    groups: List[Group] = Field(default_factory=list)

    def update(self, other: "RequirementsDocument") -> "RequirementsDocument":
        """Updates the current document with another, merging groups and requirements."""
        existing_categories = {group.category for group in self.groups}

        for new_group in other.groups:
            if new_group.category not in existing_categories:
                # Add new group
                self.groups.append(new_group)
            else:
                # Update existing group
                existing_group = next(
                    g for g in self.groups if g.category == new_group.category
                )
                existing_descriptions = {
                    req.description for req in existing_group.requirements
                }

                # Add new requirements if they are not duplicates
                for req in new_group.requirements:
                    if req.description not in existing_descriptions:
                        existing_group.requirements.append(req)

                # Update description if needed
                if new_group.description:
                    existing_group.description = new_group.description

        return self


# Define the async function to extract requirements
async def extract_requirements_from_chunk(
    current_state: RequirementsDocument, chunk: str, i: int, total_chunks: int
):
    """Extract requirements from a chunk of the style guide."""
    logger.info(f"Processing chunk {i}/{total_chunks}")
    logger.debug(f"Chunk content length: {len(chunk)} characters")
    
    try:
        # Initialize the ChatOpenAI model
        chat = ChatOpenAI(
            model_name="o1-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.debug("ChatOpenAI model initialized")
        
        # Create the prompt template
        prompt = f"""Your task is to extract all requirements from a given style guide chunk and present them in a structured JSON format. Follow the steps below to ensure comprehensive and accurate extraction:

1. **Thoroughly Review the Style Guide Chunk**: Carefully read the provided chunk to understand its scope, target audience, and specific guidelines. TAKE YOUR TIME.

2. **Identify Sections and Subsections**: Note any sections or subsections in the chunk to organize the extraction process.

3. **Extract ALL Prescriptive Guidelines**:
   - **Locate Prescriptive Statements**: Find **ALL** statements that provide rules, guidelines, or recommended practices. Look for imperative language such as 'must', 'should', 'always', 'never', 'prefer', and 'avoid'.
   - **Capture Exact Wording**: For each prescriptive statement, note the exact phrasing used in the style guide.

4. **Remove Duplicates and Irrelevant Information**:
   - **Identify Duplicates**: Compare the extracted requirements to eliminate any duplicates or near-duplicates.
   - **Exclude Unnecessary or Slightly Relevant Items**: Discard any requirements that are not essential or only slightly relevant to the main guidelines.

5. **Document Each Requirement in Detail**:
   - **Unique Identifier**: Assign a unique ID to each requirement, numbering them sequentially starting from 1 up to the total number of requirements (e.g., 1, 2, 3, ...).
   - **Description**: Provide a concise summary of what the requirement entails.
   - **Reference**: Include the exact quote from the style guide that defines the requirement.
   - **Category**: Classify the requirement into a type such as "Content", "Formatting", "Language Usage", "Citations", "Infoboxes", or "Structure".
   - **Level**: Determine whether the requirement is "sentence-level", "section-level", or "article-level".

6. **Classify Each Requirement**:
   - **Classification**: Label each requirement as one of the following:
     - **Imperative Standards**: Non-negotiable requirements that must be included to ensure compliance.
     - **Best Practices**: Strongly recommended guidelines that may be adjusted based on context.
     - **Flexible Guidelines**: Optional guidelines that can be applied depending on the article's context.
     - **Contextual Considerations**: Requirements that apply under specific conditions (e.g., certain article types or content).
     - **Supplementary Information**: Additional, non-essential information that enhances the article.
     - **Non-Applicable Elements**: Requirements that do not apply to the current article or content.

7. **Review Each Requirement**:
   - **Where**: Determine where the requirement should be applied within an article (e.g., lead section, content section, infobox).
   - **When**: Establish when the requirement should be applied, based on the article's specific content and context.

8. **Organize Requirements into Groups**: Categorize the requirements under relevant groups based on their nature (e.g., Content, Formatting).

9. **Ensure Sequential Numbering**: Number the requirements starting from 1, ensuring that each requirement has a unique and sequential ID.

10. **Format the Output as Structured JSON**:
    - **Structure**: The JSON should have a top-level key named "groups", with each group containing:
        {{
            "description": "A brief description of what this group of requirements covers",
            "category": "The main category this group belongs to",
            "requirements": [array of requirement objects]
        }}
    - **Requirement Object**: Each requirement should follow this structure:
        {{
            "id": "{{number}}",
            "description": "Brief description of the requirement",
            "reference": "Exact quote from the style guide",
            "category": "Requirement type",
            "classification": "Classification of the requirement",
            "where": "Where the requirement should be applied",
            "when": "When the requirement should be applied",
            "level": "Level of the requirement (sentence-level, section-level, article-level)"
        }}

11. **Ensure Completeness and Accuracy**: After extraction, review the JSON to confirm that all requirements from the style guide chunk are included, correctly categorized, and numbered sequentially.

12. **Output Only the JSON**: The final response should contain only the JSON structure with all extracted requirements. Do not include any additional text or explanations.

Current State of Requirements Document:
{current_state.model_dump_json(indent=2)}

Chunk ({i}/{total_chunks}):
{chunk}

Do not include any explanations or text outside of the JSON output."""

        messages = [HumanMessage(content=prompt)]
        logger.debug("Sending request to OpenAI API")
        
        # Make the async call to the model
        response = await chat.agenerate([messages])
        logger.debug("Received response from OpenAI API")
        
        return response.generations[0][0].text
    except Exception as e:
        logger.error(f"Error in extract_requirements_from_chunk: {str(e)}", exc_info=True)
        raise

async def get_title(text: str) -> str:
    try:        
        chat = ChatOpenAI(
            model_name="o1-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        messages = [HumanMessage(content="Given the following text, return the title of the article. Do not include any explanations or text outside of the title. " + text)]
        logger.debug("Sending request to OpenAI API")
        
        # Make the async call to the model
        response = await chat.agenerate([messages])
        logger.debug("Received response from OpenAI API")
        return response.generations[0][0].text
    
    except Exception as e:
        logger.error(f"Error in get_title: {str(e)}", exc_info=True)
        raise
    

# Function to split the text into manageable chunks
def split_content(requirements_text: str, max_chunk_size=6000) -> List[str]:
    """Split the style guide text into chunks not exceeding max_chunk_size."""
    logger.info(f"Splitting content with max chunk size: {max_chunk_size}")
    logger.debug(f"Input text length: {len(requirements_text)} characters")
    
    try:
        paragraphs = re.split(r"\n\s*\n", requirements_text)
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        logger.info(f"Content split into {len(chunks)} chunks")
        logger.debug(f"Chunk sizes: {[len(chunk) for chunk in chunks]}")
        return chunks
    except Exception as e:
        logger.error(f"Error in split_content: {str(e)}", exc_info=True)
        raise

# Main function to process the text and extract requirements
async def process_requirements(requirements_text: str) -> RequirementsDocument:
    logger.info("Starting requirements processing")
    logger.debug(f"Input text length: {len(requirements_text)} characters")
    
    try:
        title = await get_title(requirements_text)
        
        chunks = split_content(requirements_text)
        current_state = RequirementsDocument()
        total_chunks = len(chunks)
        logger.info(f"Processing {total_chunks} chunks")
        
        for i, chunk in enumerate(chunks, start=1):
            logger.info(f"Processing chunk {i}/{total_chunks}")
            
            # Extract requirements from the current chunk
            raw_output = await extract_requirements_from_chunk(
                current_state, chunk, i, total_chunks
            )
            logger.debug(f"Raw output length from chunk {i}: {len(raw_output)}")
            
            # Clean the output (remove any potential backticks)
            json_output = raw_output.replace("```json", "").replace("```", "").strip()
            
            try:
                # Parse the output into a RequirementsDocument
                logger.debug(f"Attempting to parse JSON output from chunk {i}")
                new_requirements = RequirementsDocument.model_validate_json(json_output)
                logger.debug(f"Successfully parsed JSON from chunk {i}")
                
                # Update the current state with new requirements
                logger.debug(f"Updating current state with requirements from chunk {i}")
                current_state.update(new_requirements)
                logger.debug(f"Current state updated with chunk {i}")
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Error parsing JSON in chunk {i}: {e}")
                logger.debug(f"Raw output that caused error:\n{json_output}\n")
            except Exception as e:
                logger.error(f"Unexpected error in chunk {i}: {e}", exc_info=True)
                logger.debug(f"Raw output that caused error:\n{json_output}\n")

        # After processing all chunks, renumber the requirements sequentially
        logger.info("Renumbering requirements")
        requirement_counter = 1
        for group in current_state.groups:
            for req in group.requirements:
                req.id = str(requirement_counter)
                requirement_counter += 1
        
        logger.info(f"Requirements processing complete. Total requirements: {requirement_counter - 1}")
        return title, current_state.model_dump()
        
    except Exception as e:
        logger.error("Error in process_requirements", exc_info=True)
        raise
