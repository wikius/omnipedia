import re
import json
import os
from typing import List, Dict
import ell
from openai import OpenAI

def convert_wikitext_to_markdown(wikitext: str) -> str:
    """Convert wikitext to markdown without images."""
    ell.init(store="./logdir", autocommit=True, verbose=False)
    prompt = f"""
Your task is to convert the provided Wikitext chunk into perfectly formatted Markdown, excluding any images.

### Input Data:

{wikitext}
"""
    return prompt

def parse_markdown_to_sections(markdown_content: str) -> List[Dict]:
    """
    Parse markdown content into sections.
    Returns a list of dictionaries containing section title, content, level (depth of the section), and index.
    """
    sections = []
    current_section = {"title": "", "content": [], "level": 0}
    current_index = 1

    lines = markdown_content.split("\n")

    for line in lines:
        if line.strip().startswith("#"):
            if current_section["title"]:
                sections.append(
                    {
                        "title": current_section["title"],
                        "content": "\n".join(current_section["content"]).strip(),
                        "level": current_section["level"],
                        "index": current_index,
                    }
                )
                current_index += 1
            level = len(re.match(r"^#+", line.strip()).group())
            current_section = {
                "title": line.strip("#").strip(),
                "content": [],
                "level": level,
            }
        else:
            current_section["content"].append(line)

    if current_section["title"]:
        sections.append(
            {
                "title": current_section["title"],
                "content": "\n".join(current_section["content"]).strip(),
                "level": current_section["level"],
                "index": current_index,
            }
        )

    return sections

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using basic rules."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def convert_wikitext(wikitext_content: str) -> List[Dict]:
    """
    Convert wikitext content to structured JSON with sections and sentences.
    Returns a list of dictionaries containing section information and sentences.
    """
    # Convert wikitext to markdown
    markdown_content = convert_wikitext_to_markdown(wikitext_content)
    
    # Parse markdown into sections
    sections = parse_markdown_to_sections(markdown_content)

    # Split section content into sentences
    for section in sections:
        if section["content"]:
            section["sentences"] = split_into_sentences(section["content"])
        else:
            section["sentences"] = []
        
        # Remove the content field as we now have sentences
        del section["content"]

    return sections

if __name__ == "__main__":
    # Example wikitext content
    wikitext_content = "# Heading\nThis is a sample wikitext content.\n## Subheading\nThis is a subheading."
    sections = convert_wikitext(wikitext_content)

    with open("output.json", "w") as f:
        json.dump(sections, f, indent=4)
