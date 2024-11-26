from typing import List, Dict
import re
import json


def parse_markdown_to_sections(markdown_content: str) -> List[Dict]:
    """
    Parse markdown content into sections.
    Returns a list of dictionaries containing section title, content, level (depth of the section), and index.
    """
    # Split the content into sections based on headers
    sections = []
    current_section = {"title": "", "content": [], "level": 0}
    current_index = 1

    # Split content into lines
    lines = markdown_content.split("\n")

    for line in lines:
        # Check if line is a header (starts with #)
        if line.strip().startswith("#"):
            # If we have a previous section, save it
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
            # Start new section
            # Count #s to determine level
            level = len(re.match(r"^#+", line.strip()).group())
            # Remove #s and whitespace from title
            current_section = {
                "title": line.strip("#").strip(),
                "content": [],
                "level": level,
            }
        else:
            # Add content line to current section
            current_section["content"].append(line)

    # Add the last section if it exists
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
    """
    Split text into sentences using basic rules.
    """
    # Simple sentence splitting - can be enhanced based on needs
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


if __name__ == "__main__":
    with open("article.md") as f:
        md = f.read()
    sections = parse_markdown_to_sections(md)
    print(sections)

    for section in sections:
        if section["content"]:
            section["sentences"] = split_into_sentences(section["content"])
        else:
            section["sentences"] = []

    with open("APRT.json", "w") as a:
        json.dump(sections, a, indent=4)
