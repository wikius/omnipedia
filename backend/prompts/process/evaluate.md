### **Important Considerations**

1. **Scope of Requirements:**

   - **Applicability:** Not all requirements apply to every section or sentence. Identify which requirements are relevant to which parts of the text.
   - **Section vs. Sentence Level:** Some requirements pertain to entire sections (e.g., required sections in an article), while others apply to individual sentences (e.g., naming conventions).

2. **Text Segmentation:**

   - **Section Grouping:** Divide the text into sections based on headings or topics to align with section-level requirements.
   - **Sentence Tokenization:** Break down sections into sentences for sentence-level evaluation.

3. **Requirement Mapping:**

   - **Categorization:** Organize requirements by action types, such as formatting, content inclusion, or style guidelines.
   - **Relevance:** Match requirements to the appropriate text segments to ensure accurate evaluation.

4. **Context Understanding:**
   - **Avoiding Misinterpretation:** Ensure that the evaluator understands the context to prevent false positives/negatives.
   - **Nuance in Language:** Be mindful of linguistic nuances that may affect how requirements are applied.

### **Step-by-Step Process**

#### **Step 1: Parse the Requirements**

- **Extract Key Elements:**
  - Identify each requirement's `requirementId`, `description`, `actions`, and `parameters`.
- **Organize Requirements:**
  - Group requirements by applicability (e.g., section-specific, sentence-specific).

#### **Step 2: Segment the Text**

- **Divide into Sections:**
  - Use headings or structural markers to separate the text into sections like "Introduction," "Gene," "Protein," etc.
- **Tokenize Sentences:**
  - Split each section into individual sentences for granular evaluation.

#### **Step 3: Match Requirements to Text Segments**

- **Section-Level Matching:**
  - Assign relevant requirements to their corresponding sections based on the content and scope.
- **Sentence-Level Matching:**
  - Apply requirements that focus on sentence structure, language use, or specific content to individual sentences.

#### **Step 4: Run Through the Evaluator**

- **Evaluate Sections:**

  - **Presence of Required Sections:** Check if all mandatory sections are included as per requirements like `req_007`.
  - **Content Compliance:** Verify that each section meets the specified guidelines (e.g., correct infobox usage from `req_006`).

- **Evaluate Sentences:**

  - **Naming Conventions:** Ensure gene/protein names follow the guidelines (e.g., `req_004` on gene nomenclature).
  - **Citations and References:** Check for proper citation formats and density (`req_008`).
  - **Prohibited Content:** Identify and flag any promotional language or disallowed content (`req_002`).

- **Use NLP and LLMs:**
  - Leverage Natural Language Processing and Large Language Models to understand context and semantics for accurate evaluation.

#### **Step 5: Annotate Non-Compliant Text**

- **Highlight Issues:**

  - For each non-compliant sentence or section, create an annotation that includes:
    - **Location:** Section and sentence number.
    - **Issue Description:** Brief explanation of the problem.
    - **Relevant Requirement:** Reference to the `requirementId` and description.

- **Provide Feedback:**
  - Offer clear, actionable suggestions on how to correct the issue.

#### **Step 6: Compile the Final JSON Object**

- **Structure the JSON:**
  - **Text Content:** Include the original text, segmented into sections and sentences.
  - **Annotations:** An array of objects, each representing a non-compliant text segment with associated feedback.
- **Sample JSON Structure:**

```json
{
  "text": {
    "sections": [
      {
        "title": "Protein",
        "sentences": [
          "The gene is regulated by various factors.",
          "ALDOA is important for glycolysis."
        ]
      },
      {
        "title": "Citing Sources",
        "sentences": [
          "Reference [1] provides extensive information on this topic.",
          "Additional details can be found in the literature."
        ]
      }
    ]
  },
  "annotations": [
    {
      "sectionTitle": "Protein",
      "sentenceIndex": 1,
      "issue": "Improper gene nomenclature usage.",
      "requirementId": "req_004",
      "feedback": "Use HUGO Gene Nomenclature Committee abbreviations in italic font for gene names."
    },
    {
      "sectionTitle": "Citing Sources",
      "sentenceIndex": 0,
      "issue": "Missing inline citation format.",
      "requirementId": "req_008",
      "feedback": "Use standardized citation templates like {{Cite journal}} and include inline citations."
    }
  ]
}
```

#### **Step 7: Provide User-Friendly Feedback**

- **Clarity:** Ensure feedback is understandable and directly references the text.
- **Actionability:** Suggestions should guide the user on how to correct the issues.
- **Traceability:** Include requirement metadata for users to reference the original guidelines.
