// types.ts
export interface RequirementEvaluation {
  requirement_id: string;
  requirement_category: string;
  applicable: boolean;
  applicability_reasoning: string;
  score: number;
  confidence: number;
  evidence: string;
  reasoning: string;
  overlap_notes: string;
}

export interface SentenceEvaluation {
  sentence: string;
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string;
}

export interface SectionEvaluation {
  title: string;
  sentence_evaluations: SentenceEvaluation[];
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string;
}

export interface ArticleEvaluation {
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string;
}

export interface Evaluation {
  sections: SectionEvaluation[];
  article_evaluation: ArticleEvaluation;
}

export interface Requirement {
  id: string;
  description: string;
  reference: string;
  category: string;
  classification: string;
  where: string;
  when: string;
  level: string;
}

export interface RequirementGroup {
  description: string;
  category: string;
  requirements: Requirement[];
}

export interface RequirementsDocument {
  groups: RequirementGroup[];
}
