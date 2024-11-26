import React from "react";
import {
  EvaluationData,
  getSectionAggregateScore,
  getSentenceAggregateScore,
} from "@/lib/eval";

const stripMarkdown = (text: string): string => {
  // Remove bold/italic markers
  text = text.replace(/\*\*([^*]+)\*\*/g, "$1");
  text = text.replace(/\*([^*]+)\*/g, "$1");

  // Remove links - extract just the text part
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

  // Remove bullet points and replace with plain text
  text = text.replace(/^[\s]*[-*+][\s]+/gm, "• ");

  return text.trim();
};

export const InteractiveText: React.FC<{
  text: string;
  type: "section" | "sentence";
  section: number;
  sentence?: number;
  evaluationData: EvaluationData | null; // Added to access evaluation data
  highlightEnabled: boolean;
  className?: string;
  onElementClick: (
    text: string,
    type: "section" | "sentence",
    section: number,
    sentence?: number
  ) => void;
}> = ({
  text,
  type,
  section,
  sentence,
  evaluationData,
  highlightEnabled,
  className,
  onElementClick,
}) => {
  // Calculate the compliance score for the section or sentence
  let score = 0;
  if (evaluationData && highlightEnabled) {
    if (type === "section") {
      // Convert zero-based index to one-based for evaluation utilities
      score = getSectionAggregateScore(evaluationData, section + 1);
    } else if (type === "sentence" && sentence !== undefined) {
      // Convert zero-based index to one-based for evaluation utilities
      score = getSentenceAggregateScore(
        evaluationData,
        section + 1,
        sentence + 1
      );
    }
  }

  // Determine highlight classes based on the score
  const getScoreHighlightClass = (score: number) => {
    if (score >= 0.8) {
      // High score: highlight green
      return "bg-green-100 dark:bg-green-900";
    } else if (score >= 0.5) {
      // Medium score: highlight yellow
      return "bg-yellow-100 dark:bg-yellow-900";
    } else if (score > 0) {
      // Low score: highlight red
      return "bg-red-100 dark:bg-red-900";
    }
    // If score is 0 or highlight not enabled, no highlight
    return "";
  };

  // Compute the highlight class if highlighting is enabled and we have a score
  const highlightClass =
    highlightEnabled && evaluationData ? getScoreHighlightClass(score) : "";

  return (
    <span
      onClick={() => onElementClick(text, type, section, sentence)}
      className={`cursor-pointer ${className || ""} ${highlightClass} ${
        highlightEnabled ? "hover:bg-gray-200 dark:hover:bg-gray-700" : ""
      } font-medium text-gray-900 dark:text-gray-100 px-1 rounded transition-colors duration-200`}
    >
      {stripMarkdown(text)}
      {type === "sentence" ? " " : ""}
    </span>
  );
};
