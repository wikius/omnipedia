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
            print(section.title)
            print("_______________________")

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

**Instructions:**

Establish grading criteria for each **section**, each **sentence** within those sections, and the **entire article** based on the provided requirements. Each requirement has a classification that determines its importance. Follow the steps below to ensure a thorough and accurate evaluation.

**Note:** If a section or sentence is empty, **do not evaluate** it.

---

### **1. Requirement Classifications**

1. **Imperative Standards (High Priority)**
   - **Must Always Include:** Requirements with `"when": "Always"`.
   - **Impact of Non-Compliance:** Greatly reduces the score.

2. **Best Practices (Medium Priority)**
   - **Impact of Non-Compliance:** Moderately affects the score.

3. **Flexible Guidelines (Low Priority)**
   - **Impact of Non-Compliance:** Minimally affects the score.

4. **Contextual Considerations**
   - **Impact of Non-Compliance:** Applies only if conditions are met.

5. **Supplementary Information**
   - **Impact of Non-Compliance:** Enhances quality but not required.

6. **Non-Applicable Elements**
   - **Do Not Evaluate.**

---

### **2. Evaluation Steps**

**Step 1: Evaluate Imperative Standards**

- **Identify:** Extract all **Imperative Standards** with `"when": "Always"`.
- **Map & Evaluate:** Link each to the relevant section or sentence.
- **Score:** Assign based on the grading scale.
- **Document:** Provide evidence and reasoning for each score.

**Step 2: Evaluate Other Requirements**

- **Identify Applicable Requirements:** Based on classification and context.
- **Map & Evaluate:** Link each to the relevant content.
- **Score:** Assign based on the grading scale.
- **Document:** Provide evidence and reasoning for each score.

---

### **3. Grading Scale**

- **1.0:** Complete adherence.
- **0.75:** Strong adherence with minor improvements needed.
- **0.5:** Partial adherence with room for improvement.
- **0.25:** Minimal adherence with significant gaps.
- **0.0:** No adherence.

*Use the sliding scale to capture varying degrees of adherence.*

---

### **4. Scoring Guidelines**

- **Imperative Standards:** Must fully comply.
- **Best Practices:** Partial compliance is acceptable.
- **Flexible Guidelines:** Non-compliance has minimal impact.
- **Contextual Considerations:** Score only if applicable.
- **Supplementary Information:** Enhances score but not required.
- **Non-Applicable Elements:** Do not assign a score.

---

### **5. Evaluation Process**

#### **Content Mapping**

- **Map Requirements:** Link each applicable requirement to specific parts of the content.
- **Ensure:** All mandatory requirements are accurately mapped.
- **Identify Gaps:** Note any missing or incomplete mappings for mandatory requirements.

#### **Detailed Evaluation**

- **Score Assignment:**
  - Assign a score from **0.0 to 1.0** based on the grading scale.
  - **Do not assign null**. If not applicable, do not grade it.
- **Provide Evidence:**
  - Offer specific examples from the content supporting the score.
- **Reasoning:**
  - Explain the rationale behind each score, considering the requirement's classification.
- **Confidence Rating:**
  - Assign a confidence level (**0 to 1**) indicating certainty in the score.
- **Special Considerations:**
  - Note any unique factors influencing the evaluation.

#### **Meta Notes**

- **Action:** Add observations or suggestions for improvement at the sentence or section level.
- **Method:** Use the `meta_notes` field for constructive feedback.
- **Example:** `"Meta Notes: Consider italicizing gene symbols for full adherence."`

---

### **6. Key Principles**

- **Mandatory Compliance:** Always evaluate all **Imperative Standards** with `"when": "Always"`.
- **Accurate Mapping:** Ensure every applicable requirement is correctly linked to the content.
- **Clear Documentation:** Provide evidence and reasoning for each score.
- **Consistency:** Follow the grading scale and scoring guidelines precisely.
- **Structured Output:** Adhere strictly to the JSON format to avoid validation errors.

---

### **7. Additional Evaluation Guidelines**

1. **Reflect on Content Clarity and Quality:**
   - Ensure the content maintains clarity and quality as per the style guide.

2. **Mapping and Observations:**
   - Map requirements to content meticulously.
   - Provide detailed observations and reasoning for each grade.

3. **Document Thought Process:**
   - Document analytical processes, observations, and key details for each level.

---

### **8. Output Format**

The output **must** match the exact format below:

```json
{
  "sections": [
    {
      "index": 0,
      "title": "Section Title",
      "sentence_evaluations": [
        {
          "index": 0,
          "sentence": "Sample sentence...",
          "requirement_evaluations": [
            {
              "requirement_id": "R7",
              "requirement_category": "Content",
              "classification": "Imperative Standards",
              "applicable": true,
              "applicability_reasoning": "Applicable because it refers to gene nomenclature.",
              "reasoning": "Gene name 'ALDOA' is correctly capitalized but not italicized.",
              "score": 0.75,
              "confidence": 0.9,
              "evidence": "Gene name 'ALDOA' is present but not formatted correctly.",
              "reasoning_detail": "Strong adherence with minor formatting issues."
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
          "reasoning": "The section starts with a clear definition of the protein.",
          "score": 1.0,
          "confidence": 0.95,
          "evidence": "Provides a comprehensive definition.",
          "reasoning_detail": "Fully meets the requirement."
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
        "reasoning": "The article title is lengthy and could be shortened.",
        "score": 0.5,
        "confidence": 0.85,
        "evidence": "Uses the UniProt protein name but is verbose.",
        "reasoning_detail": "Partial adherence; title brevity could be improved."
      }
    ],
    "meta_notes": "Overall, the article meets many standards but has room for improvement in title brevity."
  }
}
```

**Important:** Your response **must** be a complete `EvaluationOutput` object structured **exactly** as shown in the JSON format above. Any deviation from this format or omission of any evaluation components will cause validation errors.

**Ensure the Following:**

1. **Include All Sections:**
   - Every section with its evaluations must be present.

2. **Evaluate Every Sentence:**
   - Provide evaluations for all sentences within each section.

3. **Assess All Applicable Requirements:**
   - Especially evaluate all **Imperative Standards** with `"when": "Always"`.

4. **Complete Article Evaluation:**
   - The `article_evaluation` must include all relevant requirements.

**Remember:**

- **Mandatory Compliance:** All imperative standards must be met.
- **Accurate Mapping:** Link each requirement correctly to the content.
- **Detailed Documentation:** Provide evidence and reasoning for each score.
- **Consistent Scoring:** Follow the grading scale precisely.
- **Structured Output:** Adhere strictly to the JSON format.
"""


@ell.simple(model="o1-preview", client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
def evaluate_section(
    current_state: EvaluationOutput,
    section: Dict,
    requirements: List[Dict],
    i: int,
    total_sections: int,
):
    """Evaluate a single section of the article based on the given requirements."""
    print(section["title"])
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
    sections: List[Dict], requirements: List[Dict]
) -> EvaluationOutput:
    ell.init(store="./logdir", autocommit=True, verbose=False)

    evaluation = EvaluationOutput(
        sections=[],
        article_evaluation=ArticleEvaluation(
            requirement_evaluations=[], meta_notes=None
        ),
    )

    total_sections = len(sections)
    for i, section in enumerate(sections, start=1):
        # Skip empty sections
        if not section.get("content") and not section.get("sentences"):
            print(f"Skipping empty section {i}: {section.get('title', 'Untitled')}")
            continue

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
    with open("requirements.json") as reqs:
        requirements = json.load(reqs)

    # Load and process markdown file instead of JSON
    with open("APRT-wikipedia.json") as art:
        article = json.load(art)

    # Process the article sections
    evaluation_output = process_article_sections(article, requirements)

    # Save the final JSON to a file
    with open("evals/evaluation-APRT-wikipedia.json", "w") as outfile:
        json.dump(evaluation_output.model_dump(), outfile, indent=4)
