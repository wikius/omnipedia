import ABCC11WikicrowArticle from "@/lib/data/ABCC11/wikicrow/article.json";
import ABCC11WikicrowEvaluation from "@/lib/data/ABCC11/wikicrow/evaluation.json";
import ABCC11WikipediaArticle from "@/lib/data/ABCC11/wikipedia/article.json";
import ABCC11WikipediaEvaluation from "@/lib/data/ABCC11/wikipedia/evaluation.json";

import APRTWikicrowArticle from "@/lib/data/APRT/wikicrow/article.json";
import APRTWikicrowEvaluation from "@/lib/data/APRT/wikicrow/evaluation.json";
import APRTWikipediaArticle from "@/lib/data/APRT/wikipedia/article.json";
import APRTWikipediaEvaluation from "@/lib/data/APRT/wikipedia/evaluation.json";

import B3GAT1WikicrowArticle from "@/lib/data/B3GAT1/wikicrow/article.json";
import B3GAT1WikicrowEvaluation from "@/lib/data/B3GAT1/wikicrow/evaluation.json";
import B3GAT1WikipediaArticle from "@/lib/data/B3GAT1/wikipedia/article.json";
import B3GAT1WikipediaEvaluation from "@/lib/data/B3GAT1/wikipedia/evaluation.json";

import GRIA2WikicrowArticle from "@/lib/data/GRIA2/wikicrow/article.json";
import GRIA2WikicrowEvaluation from "@/lib/data/GRIA2/wikicrow/evaluation.json";
import GRIA2WikipediaArticle from "@/lib/data/GRIA2/wikipedia/article.json";
import GRIA2WikipediaEvaluation from "@/lib/data/GRIA2/wikipedia/evaluation.json";

export interface ArticleSection {
  title: string;
  content: string;
  level: number;
  index: number;
  sentences: string[];
}

export type Article = ArticleSection[];

export interface RequirementEvaluation {
  requirement_id: string;
  requirement_category: string;
  classification: string;
  applicable: boolean;
  applicability_reasoning: string;
  score: number | null; // 0-1 or null
  confidence: number | null; // 0-1 or null
  evidence: string;
  reasoning: string;
}

export interface SentenceEvaluation {
  index: number;
  sentence: string;
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string | null;
}

export interface SectionEvaluation {
  index: number;
  title: string;
  sentence_evaluations: SentenceEvaluation[];
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string | null;
}

export interface ArticleEvaluation {
  requirement_evaluations: RequirementEvaluation[];
  meta_notes: string | null;
}

export interface Evaluation {
  sections: SectionEvaluation[];
  article_evaluation: ArticleEvaluation;
}

export interface SourceData {
  article: Article;
  evaluation: Evaluation;
}

export interface DataSet {
  wikicrow: SourceData;
  wikipedia: SourceData;
}

export interface AllData {
  [key: string]: DataSet;
}

// Initialize the cache
export const dataCache: AllData = {
  ABCC11: {
    wikicrow: {
      article: ABCC11WikicrowArticle,
      evaluation: ABCC11WikicrowEvaluation,
    },
    wikipedia: {
      article: ABCC11WikipediaArticle,
      evaluation: ABCC11WikipediaEvaluation,
    },
  },
  APRT: {
    wikicrow: {
      article: APRTWikicrowArticle,
      evaluation: APRTWikicrowEvaluation,
    },
    wikipedia: {
      article: APRTWikipediaArticle,
      evaluation: APRTWikipediaEvaluation,
    },
  },
  B3GAT1: {
    wikicrow: {
      article: B3GAT1WikicrowArticle,
      evaluation: B3GAT1WikicrowEvaluation,
    },
    wikipedia: {
      article: B3GAT1WikipediaArticle,
      evaluation: B3GAT1WikipediaEvaluation,
    },
  },
  GRIA2: {
    wikicrow: {
      article: GRIA2WikicrowArticle,
      evaluation: GRIA2WikicrowEvaluation,
    },
    wikipedia: {
      article: GRIA2WikipediaArticle,
      evaluation: GRIA2WikipediaEvaluation,
    },
  },
};
