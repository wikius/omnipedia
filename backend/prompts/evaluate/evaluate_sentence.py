from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from openai import OpenAI
import ell
import json
import os
from dotenv import load_dotenv


load_dotenv()


# Define data models
class RequirementEvaluation(BaseModel):
    requirement_id: str
    requirement_category: str
    applicable: bool
    applicability_reasoning: Optional[str]
    score: Optional[float]
    confidence: Optional[float]
    evidence: Optional[str]
    reasoning: Optional[str]
    overlap_notes: Optional[str]


class SentenceEvaluation(BaseModel):
    sentence: str
    requirement_evaluations: List[RequirementEvaluation]
    meta_notes: Optional[str]


class SectionEvaluation(BaseModel):
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
Your task is to establish grading criteria for each section, sentence (when applicable), and the entire article based on the given requirements. Each requirement has a classification that determines its importance in the evaluation. Follow the multi-step process below to ensure a thorough and accurate evaluation.

**Note**: If the content of the section or sentence is empty, there is no need to evaluate it. **Do not evaluate.**

---

**Requirement Classifications and Weighting**

Each requirement is classified to indicate its importance:

1. **Imperative Standards** (High Priority)
   - Non-negotiable requirements that must be included to ensure compliance.
   - **Weighting**: High. Non-compliance significantly lowers the score.

2. **Best Practices** (Medium Priority)
   - Strongly recommended guidelines that may be adjusted based on context.
   - **Weighting**: Medium. Non-compliance moderately affects the score.

3. **Flexible Guidelines** (Low Priority)
   - Optional guidelines that can be applied depending on the article's context.
   - **Weighting**: Low. Non-compliance has minimal impact on the score.

4. **Contextual Considerations**
   - Requirements that apply under specific conditions.
   - **Weighting**: Apply only if conditions are met.

5. **Supplementary Information**
   - Additional, non-essential information that enhances the article.
   - **Weighting**: Minimal impact. Enhances quality but not required.

6. **Non-Applicable Elements**
   - Requirements that do not apply to the current article or content.
   - **Weighting**: Do not evaluate these requirements.

---

**Initial Assessment Phase**

**Step 1: Applicability Assessment**
1. **Classify and Evaluate Requirements**:
   - For each level (section, sentence, article), identify applicable requirements.
   - Add the index to each level.
   - Assess applicability based on the classification and context.
   - Document reasoning for including or excluding each requirement.

2. **Document Relevance**:
   - Clearly state why each requirement is or isn't applicable.
   - Highlight any edge cases or unclear applicability.
   - **Proceed with Grading**:
     - Only grade the requirements that are applicable to the specific level.

---

**Grading Scale Definition**

- **0.0**: No adherence to the requirement.
- **0.25**: Minimal adherence with significant gaps.
- **0.5**: Partial adherence with notable room for improvement.
- **0.75**: Strong adherence with minor improvements possible.
- **1.0**: Complete adherence to the requirement.

**Scoring Adjustments Based on Classification**

When assigning scores, consider the requirement's classification:

- **Imperative Standards**: Aim for full compliance. Non-compliance significantly lowers the score.
- **Best Practices**: Partial compliance is acceptable. Score reflects the degree of adherence.
- **Flexible Guidelines**: Non-compliance has minimal impact. Score reflects whether the guideline was applied effectively.
- **Contextual Considerations**: Only score if the requirement is applicable.
- **Supplementary Information**: Enhances the score but is not required for compliance.
- **Non-Applicable Elements**: Do not assign a score.

---

**Evaluation Process (Per Level)**

1. **Content Mapping**:
   - **Map Requirements to Content**:
     - Link each applicable requirement to specific parts of the content at the corresponding level.
   - **Identify Gaps**:
     - Note any missing or incomplete mappings.
   - **Detect Overlaps**:
     - Identify any content overlap with other sections or sentences.

2. **Detailed Evaluation**:
   - **Score Assignment**:
     - For each applicable requirement, assign a score based on the grading scale.
     - **Important**: Do not assign null to anything. The only acceptable scores are from 0.0 to 1.0.
     - If not applicable, do not grade it.
   - **Provide Evidence**:
     - Offer specific examples or evidence from the content that support the assigned score.
   - **Reasoning**:
     - Explain the rationale behind each score, considering the requirement's classification.
   - **Confidence Rating**:
     - Assign a confidence level (0 to 1) indicating how certain you are that the content meets the requirement.
   - **Special Considerations**:
     - Note any unique factors influencing the evaluation.

---

**Key Principles**

- **Applicability First**: Always assess applicability before grading.
- **Classification Awareness**: Adjust your evaluation based on the requirement's classification.
- **Use the Full Sliding Scale**: Utilize the entire range for nuanced evaluation.
- **Specific Evidence**: Provide concrete examples for all scores.
- **Clear Reasoning**: Ensure that reasoning is transparent and easy to follow.
- **Context Awareness**: Consider the context of each level during evaluation.
- **Meaningful Overlaps**: Recognize and document significant overlaps without penalizing justified repetitions.

---

**Additional Evaluation Guidelines**

1. **Grading Scale Refinement**:
   - Emphasize the sliding nature of the grading scale to capture varying degrees of adherence.
2. **Content Complexity and Clarity**:
   - Reflect on whether the content maintains clarity and quality as per the style guide.
3. **Mapping and Observations**:
   - Map requirements to content meticulously.
   - Provide detailed observations and reasoning for each grade.
4. **Handling Overlaps and Redundancies**:
   - Assess whether overlapping information serves a meaningful purpose or is redundant.
5. **Thought Process Documentation**:
   - Document analytical processes, observations, and key details for each level.

**Output Format**

Your evaluation should be saved in the following structured JSON format:

```json
{
  "sections": [
    {
      "title": "Section Title",
      "index": "Section Index",
      "sentence_evaluations": [
        {
          "sentence": "The gene ALDOA is regulated...",
          "index": "Sentence Index",
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
"""


@ell.simple(model="o1-mini", client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
def evaluate_section(
    current_state: EvaluationOutput,
    section: Dict,
    requirements: List[Dict],
    i: int,
    total_sections: int,
):
    """Evaluate a single section of the article based on the given requirements."""
    return [
        ell.user(f"""You are an expert in evaluating article content based on style guide requirements. Your task is to perform a detailed evaluation of the given section, including sentence-level (when applicable) and article-level evaluations, following the multi-step process outlined below.

                    {instructions}

                    **Current State of Evaluation:**
                    {current_state.model_dump_json(indent=2)}

                    **Section ({i}/{total_sections}):**
                    {json.dumps(section, indent=2)}

                    **Requirements:**
                    {json.dumps(requirements, indent=2)}

                    **Remember to output only the JSON in the specified format, without any additional text.**
                    """)
    ]


def process_article_sections(
    sections: List[Dict], requirements: List[Dict]
) -> EvaluationOutput:
    ell.init(store="./logdir", autocommit=True, verbose=True)
    # Initialize current_state with an empty article_evaluation including meta_notes
    current_state = EvaluationOutput(
        sections=[],
        article_evaluation=ArticleEvaluation(
            requirement_evaluations=[], meta_notes=None
        ),
    )
    total_sections = len(sections)
    for i, section in enumerate(sections, start=1):
        # Evaluate the current section
        raw_output = evaluate_section(
            current_state, section, requirements, i, total_sections
        )
        # Clean the output (remove any potential backticks)
        json_output = raw_output.replace("```json", "").replace("```", "").strip()
        try:
            # Parse the output into an EvaluationOutput
            new_evaluation = EvaluationOutput.parse_raw(json_output)
            # Update the current state with new evaluations
            current_state.update(new_evaluation)
        except Exception as e:
            print(f"Error parsing JSON in section {i}: {e}")
            print(f"Raw output:\n{json_output}\n")

    return current_state


if __name__ == "__main__":
    # Replace with your actual sections and requirements
    with open("backend/prompts/requirements.json") as reqs:
        requirements = json.load(reqs)
    with open("backend/prompts/wikicrow-article.json") as article:
        sections = json.load(article)

    # Process the article sections
    evaluation_output = process_article_sections(sections, requirements)
    # Save the final JSON to a file
    with open("evaluation-wikicrow.json", "w") as outfile:
        json.dump(evaluation_output.model_dump(), outfile, indent=4)
