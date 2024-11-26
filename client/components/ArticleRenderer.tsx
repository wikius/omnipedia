import { EvaluationData } from "@/lib/eval";
import React from "react";
import { InteractiveText } from "./InteractiveElement";

interface ArticleSection {
  title: string;
  content: string;
  sentences: string[];
}

interface ArticleRendererProps {
  onElementClick?: (
    text: string,
    type: "section" | "sentence",
    section: number,
    sentence?: number
  ) => void;
  highlightEnabled?: boolean;
  articleData?: ArticleSection[];
  evaluationData?: EvaluationData;
}

export const ArticleRenderer = ({
  onElementClick = () => {},
  highlightEnabled = true,
  articleData = [],
  evaluationData,
}: ArticleRendererProps) => {
  return (
    <div className="container p-6 max-w-4xl mx-auto bg-white dark:bg-gray-900">
      {articleData.map((section, sectionIndex) => (
        <div key={sectionIndex} className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-4">
            <InteractiveText
              text={section.title}
              type="section"
              section={sectionIndex}
              evaluationData={evaluationData || null}
              onElementClick={onElementClick}
              highlightEnabled={highlightEnabled}
            />
          </h1>

          {/* Pre-split sentences */}
          <p className="leading-7 [&:not(:first-child)]:mt-6">
            {section.sentences.map((sentence, index) => (
              <InteractiveText
                key={index}
                text={sentence}
                type="sentence"
                section={sectionIndex}
                sentence={index}
                className="inline"
                evaluationData={evaluationData || null}
                onElementClick={onElementClick}
                highlightEnabled={highlightEnabled}
              />
            ))}
          </p>
        </div>
      ))}
    </div>
  );
};

export default ArticleRenderer;
