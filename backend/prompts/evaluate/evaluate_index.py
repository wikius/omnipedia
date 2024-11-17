from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from openai import OpenAI
import ell
import json
import os
from dotenv import load_dotenv
import re

load_dotenv()


# Define data models (with indices)
class RequirementEvaluation(BaseModel):
    requirement_id: str
    requirement_category: str
    classification: str  # Added 'classification'
    applicable: bool
    applicability_reasoning: Optional[str]
    score: Optional[float]
    confidence: Optional[float]
    evidence: Optional[str]
    reasoning: Optional[str]
    overlap_notes: Optional[str]


class SentenceEvaluation(BaseModel):
    index: int  # New field for sentence index
    sentence: str
    requirement_evaluations: List[RequirementEvaluation]
    meta_notes: Optional[str]


class SectionEvaluation(BaseModel):
    index: int  # New field for section index
    title: str
    sentence_evaluations: Optional[List[SentenceEvaluation]]
    requirement_evaluations: List[RequirementEvaluation]
    meta_notes: Optional[str]


class ArticleEvaluation(BaseModel):
    requirement_evaluations: List[RequirementEvaluation]
    meta_notes: Optional[str]


class EvaluationOutput(BaseModel):
    sections: List[SectionEvaluation]
    article_evaluation: Optional[ArticleEvaluation]

    def update(self, other: "EvaluationOutput") -> "EvaluationOutput":
        """Updates the current evaluation with another, merging sections and requirement evaluations."""
        existing_section_titles = {section.title for section in self.sections}
        for section in other.sections:
            if section.title not in existing_section_titles:
                self.sections.append(section)
            else:
                # Merge requirement evaluations for the same section
                existing_section = next(
                    s for s in self.sections if s.title == section.title
                )
                existing_req_ids = {
                    req.requirement_id
                    for req in existing_section.requirement_evaluations
                }
                for req_eval in section.requirement_evaluations:
                    if req_eval.requirement_id not in existing_req_ids:
                        existing_section.requirement_evaluations.append(req_eval)
                # Merge sentence evaluations
                if section.sentence_evaluations:
                    if not existing_section.sentence_evaluations:
                        existing_section.sentence_evaluations = []
                    existing_section.sentence_evaluations.extend(
                        section.sentence_evaluations
                    )
        # Update article-level evaluation
        if other.article_evaluation:
            if not self.article_evaluation:
                self.article_evaluation = other.article_evaluation
            else:
                existing_req_ids = {
                    req.requirement_id
                    for req in self.article_evaluation.requirement_evaluations
                }
                for req_eval in other.article_evaluation.requirement_evaluations:
                    if req_eval.requirement_id not in existing_req_ids:
                        self.article_evaluation.requirement_evaluations.append(req_eval)
        return self


instructions = """
Your objective is to establish grading criteria for each **section** (identified by its index), each **sentence** within those sections (identified by their indices, when applicable), and the **entire article** based on the provided requirements. Each requirement is classified to indicate its importance in the evaluation process. Follow the multi-step procedure below to conduct a comprehensive and precise evaluation.

**Important**: If a section or sentence contains no content, **do not evaluate** it.

---

#### **Requirement Classifications and Weighting**

Each requirement is categorized to reflect its significance in the evaluation:

1. **Imperative Standards** _(High Priority)_

   - **Description**: Essential requirements that must be met to ensure compliance.
   - **Weighting**: **High**. Failing to meet these significantly reduces the score.

2. **Best Practices** _(Medium Priority)_

   - **Description**: Strongly recommended guidelines that can be adapted based on context.
   - **Weighting**: **Medium**. Non-compliance moderately affects the score.

3. **Flexible Guidelines** _(Low Priority)_

   - **Description**: Optional guidelines applicable depending on the article's context.
   - **Weighting**: **Low**. Non-compliance has minimal impact on the score.

4. **Contextual Considerations**

   - **Description**: Requirements applicable only under specific conditions.
   - **Weighting**: **Apply only if conditions are met**.

5. **Supplementary Information**

   - **Description**: Additional, non-essential information that enhances the article.
   - **Weighting**: **Minimal impact**. Enhances quality but is not required.

6. **Non-Applicable Elements**
   - **Description**: Requirements that do not pertain to the current article or content.
   - **Weighting**: **Do not evaluate** these requirements.

---

#### **Initial Assessment Phase**

##### **Step 1: Applicability Assessment**

1. **Classify and Evaluate Requirements**

   - **Action**: For each level (**section**, **sentence**, **article**), determine which requirements apply.
   - **Method**:
     - Review each requirement's classification.
     - Assess whether the content meets the specific conditions for applicability.
   - **Example**:
     - `"Requirement R7 applies to Section 2, Sentence 3 because it pertains to gene nomenclature."`

2. **Document Relevance**

   - **Action**: Clearly explain why each requirement **is** or **isn't** applicable.
   - **Method**:
     - Provide reasoning for inclusion or exclusion of each requirement.
     - Highlight any edge cases or ambiguous applicability.
   - **Example**:
     - `"Requirement R12 is not applicable to Section 4 as it pertains to viral proteins, which are not discussed in this article."`

3. **Proceed with Grading**
   - **Action**: Only evaluate and assign scores to requirements that are applicable.
   - **Method**: Focus your grading efforts on relevant requirements based on the applicability assessment.
   - **Example**:
     - `"Proceed to grade Requirement R5 for Section 1, Sentence 2 as it is applicable."`

---

#### **Grading Scale Definition**

Assign scores based on the following scale:

- **0.0**: No adherence to the requirement.
- **0.25**: Minimal adherence with significant gaps.
- **0.5**: Partial adherence with notable room for improvement.
- **0.75**: Strong adherence with minor improvements possible.
- **1.0**: Complete adherence to the requirement.

---

#### **Scoring Adjustments Based on Classification**

When assigning scores, consider the classification of each requirement:

- **Imperative Standards**:
  - **Expectation**: Full compliance.
  - **Impact**: Non-compliance significantly lowers the score.
- **Best Practices**:
  - **Expectation**: Partial compliance is acceptable.
  - **Impact**: Score reflects the degree of adherence.
- **Flexible Guidelines**:
  - **Expectation**: Guidelines applied effectively if possible.
  - **Impact**: Non-compliance has minimal impact on the score.
- **Contextual Considerations**:
  - **Expectation**: Score only if the requirement is applicable.
- **Supplementary Information**:
  - **Expectation**: Enhances the score but is not required.
- **Non-Applicable Elements**:
  - **Expectation**: Do not assign a score.

---

#### **Detailed Evaluation Process**

1. **Content Mapping**

   - **Map Requirements to Content**
     - **Action**: Associate each applicable requirement with specific parts of the content.
     - **Method**: Use section indices and sentence numbers to identify where each requirement is addressed.
     - **Example**:
       - `"Requirement R7 is addressed in Section 1, Sentence 1."`

2. **Detailed Evaluation**

   a. **Score Assignment**

   - **Action**: Assign a score to each applicable requirement based on the grading scale.
   - **Method**:
     - Evaluate how well the content meets each requirement.
     - **Important**: Only assign scores between **0.0** and **1.0**. Do **not** use null.
     - Do not grade requirements that are not applicable.
   - **Example**:
     - `"Requirement R15 receives a score of 0.75 for Section 3, Sentence 2 due to the inclusion of an Infobox GNF protein."`

   b. **Provide Evidence**

   - **Action**: Present specific examples or excerpts from the content that justify the assigned score.
   - **Method**: Quote or reference the exact part of the content that supports the evaluation.
   - **Example**:
     - `"Evidence: The sentence includes an Infobox GNF protein, fulfilling Requirement R15."`

   c. **Reasoning**

   - **Action**: Explain the rationale behind each assigned score, considering the requirement's classification.
   - **Method**: Link the score to how well the content meets the requirement's criteria.
   - **Example**:
     - `"Reasoning: The Infobox is present but lacks detailed information, partially meeting Requirement R15."`

   d. **Confidence Rating**

   - **Action**: Indicate your certainty regarding the accuracy of the score.
   - **Method**: Assign a confidence level between **0** and **1**.
   - **Example**:
     - `"Confidence Rating: 0.9"`

3. **Meta Notes**
   - **Action**: Add additional observations or suggestions for improvement at the sentence or section level.
   - **Method**: Use the `meta_notes` field to provide constructive feedback.
   - **Example**:
     - `"Meta Notes: Consider italicizing gene symbols to fully comply with Requirement R5."`

---

### **OUTPUT:**

After completing the evaluation, structure your results using the following JSON format:

```json
{
  "sections": [
    {
      "index": 1,
      "title": "Section Title",
      "sentence_evaluations": [
        {
          "index": 1,
          "sentence": "The gene ALDOA is regulated...",
          "requirement_evaluations": [
            {
              "requirement_id": "R7",
              "requirement_category": "Content",
              "classification": "Imperative Standards",
              "applicable": true,
              "applicability_reasoning": "Applicable because it refers to gene nomenclature.",
              "score": 0.75,
              "confidence": 0.9,
              "evidence": "Gene name 'ALDOA' is correctly capitalized but not italicized.",
              "reasoning": "Strong adherence with minor formatting issues, which is important for imperative standards.",
              "overlap_notes": "No overlaps with other sentences."
            }
          ],
          "meta_notes": "Consider italicizing gene symbols for full adherence."
        }
      ],
      "requirement_evaluations": [
        {
          "requirement_id": "R1",
          "requirement_category": "Structure",
          "classification": "Imperative Standards",
          "applicable": true,
          "applicability_reasoning": "Section defines the article scope.",
          "score": 1.0,
          "confidence": 0.95,
          "evidence": "The section starts with a clear definition of the protein.",
          "reasoning": "Fully meets the requirement by providing a comprehensive definition.",
          "overlap_notes": "No significant overlaps detected."
        }
      ],
      "meta_notes": "The section is well-defined but could improve by addressing sentence-level formatting."
    }
  ],
  "article_evaluation": {
    "requirement_evaluations": [
      {
        "requirement_id": "R3",
        "requirement_category": "Content",
        "classification": "Best Practices",
        "applicable": true,
        "applicability_reasoning": "Applies to the article title.",
        "score": 0.5,
        "confidence": 0.85,
        "evidence": "The article title is lengthy and could be shortened.",
        "reasoning": "Partial adherence; the UniProt protein name is used but is verbose, which is acceptable for best practices.",
        "overlap_notes": "N/A"
      }
    ],
    "meta_notes": "Overall, the article meets many standards but has room for improvement in title brevity."
  }
}
```

"""


def parse_markdown_to_sections(markdown_content: str) -> List[Dict]:
    """
    Parse markdown content into sections with indices.
    Returns a list of dictionaries containing section index, title, and content.
    """
    sections = []
    current_section = {"index": 0, "title": "", "content": []}
    section_counter = 0

    lines = markdown_content.split("\n")

    for line in lines:
        if line.strip().startswith("#"):
            if current_section["title"]:
                sections.append(
                    {
                        "index": section_counter,
                        "title": current_section["title"],
                        "content": "\n".join(current_section["content"]).strip(),
                    }
                )
            section_counter += 1
            current_section = {
                "index": section_counter,
                "title": line.strip("#").strip(),
                "content": [],
            }
        else:
            current_section["content"].append(line)

    # Add the last section if it exists
    if current_section["title"]:
        sections.append(
            {
                "index": section_counter,
                "title": current_section["title"],
                "content": "\n".join(current_section["content"]).strip(),
            }
        )

    return sections


def split_into_sentences(text: str) -> List[Dict]:
    """
    Split text into sentences with indices using basic rules.
    Returns a list of dictionaries containing sentence index and sentence text.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [
        {"index": idx + 1, "sentence": s.strip()}
        for idx, s in enumerate(sentences)
        if s.strip()
    ]


@ell.simple(model="o1-preview", client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
def evaluate_section(
    current_state: EvaluationOutput,
    section: Dict,
    requirements: List[Dict],
    i: int,
    total_sections: int,
):
    """Evaluate a single section of the article based on the given requirements."""
    # Add sentence-level content to the section with indices
    if section["content"]:
        section["sentences"] = split_into_sentences(section["content"])
    else:
        section["sentences"] = []

    return [
        ell.user(f"""You are an expert in evaluating article content based on style guide requirements. Your task is to perform a detailed evaluation of the given section, including sentence-level (when applicable) and article-level evaluations, following the multi-step process outlined below.

                    {instructions}

                    **Current State of Evaluation:**
                    {current_state.model_dump_json(indent=2)}

                    **Section ({i}/{total_sections}, Index: {section['index']}):**
                    {json.dumps(section, indent=2)}

                    **Requirements:**
                    {json.dumps(requirements, indent=2)}

                    **Remember to output only the JSON in the specified format, including the indices, without any additional text.**
                    """)
    ]


def process_article_sections(
    markdown_content: str, requirements: List[Dict]
) -> EvaluationOutput:
    ell.init(store="./logdir", autocommit=True, verbose=True)

    # Parse markdown into sections with indices
    sections = parse_markdown_to_sections(markdown_content)
    evaluation = EvaluationOutput(
        sections=[],
        article_evaluation=ArticleEvaluation(
            requirement_evaluations=[], meta_notes=None
        ),
    )

    total_sections = len(sections)
    for i, section in enumerate(sections, start=1):
        # Evaluate the current section
        raw_output = evaluate_section(
            evaluation, section, requirements, i, total_sections
        )
        # Clean the output (remove any potential backticks)
        json_output = raw_output.replace("```json", "").replace("```", "").strip()
        try:
            # Parse the output into an EvaluationOutput
            new_evaluation = EvaluationOutput.model_validate_json(json_output)
            # Update the current state with new evaluations
            evaluation.update(new_evaluation)
        except Exception as e:
            print(f"Error parsing JSON in section {i}: {e}")
            print(f"Raw output:\n{json_output}\n")

    return evaluation


if __name__ == "__main__":
    # Load requirements
    with open("backend/prompts/requirements.json") as reqs:
        requirements = json.load(reqs)

    # Load and process markdown file instead of JSON
    with open("article.md", "r", encoding="utf-8") as md_file:
        markdown_content = md_file.read()

    # Process the article sections
    evaluation_output = process_article_sections(markdown_content, requirements)

    # Save the final JSON to a file
    with open("evaluation-output-index.json", "w") as outfile:
        json.dump(evaluation_output.model_dump(), outfile, indent=4)
