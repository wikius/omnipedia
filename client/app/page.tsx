"use client";

import { useState } from "react";
import { ArticleRenderer } from "@/components/ArticleRenderer";
import { SidePanel } from "@/components/SidePanel";
import { HighlightToggle } from "@/components/HighlightToggle";
import { RequirementViewer } from "@/components/ReqsView";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EvaluationData, convertCacheToEvalData } from "@/lib/eval";
import { InfoBox } from "@/components/InfoBox";
import { getData } from "@/lib/loader";

export default function Page() {
  const [selectedText, setSelectedText] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<
    "section" | "sentence" | "article" | null
  >(null);
  const [isSidePanelOpen, setSidePanelOpen] = useState(false);
  const [highlightEnabled, setHighlightEnabled] = useState(true);
  const [showRequirements, setShowRequirements] = useState(false);
  const [focusedRequirement, setFocusedRequirement] = useState<string>();
  const [selectedEvaluation, setSelectedEvaluation] = useState<{
    type: "section" | "sentence" | "article" | null;
    data: EvaluationData | null;
    sectionIndex?: number;
    sentenceIndex?: number;
  }>({ type: null, data: null });
  const [selectedSource, setSelectedSource] = useState<
    "wikipedia" | "wikicrow"
  >("wikipedia");
  const [selectedArticle, setSelectedArticle] = useState<string>("ABCC11");

  // Get data using the loader
  const data = getData(selectedArticle);
  const error = !data;

  const handleElementClick = (
    text: string,
    type: "section" | "sentence",
    sectionIdx: number,
    sentenceIdx?: number
  ) => {
    if (!data || !data[selectedSource]?.evaluation) return;

    // Adjusting indices to match one-based indexing used in evaluation data
    const sectionDataIndex = sectionIdx + 1;
    const sentenceDataIndex =
      sentenceIdx !== undefined ? sentenceIdx + 1 : undefined;

    setSelectedText(text);
    setSelectedType(type);
    setSidePanelOpen(true);

    setSelectedEvaluation({
      type,
      data: convertCacheToEvalData(data[selectedSource].evaluation),
      sectionIndex: sectionDataIndex,
      sentenceIndex: sentenceDataIndex,
    });
  };

  if (error) return <div>Error loading data</div>;

  if (showRequirements) {
    return (
      <div className="min-h-screen">
        <div className="fixed top-4 right-4 z-50">
          <Button variant="outline" onClick={() => setShowRequirements(false)}>
            Back to Article
          </Button>
        </div>
        <RequirementViewer
          focusedId={focusedRequirement}
          onRequirementClick={(id) => setFocusedRequirement(id)}
        />
      </div>
    );
  }

  return (
    <div className="container ml-4 p-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-4">
          <HighlightToggle
            enabled={highlightEnabled}
            onToggle={() => setHighlightEnabled(!highlightEnabled)}
          />
          <Select
            value={selectedArticle}
            onValueChange={(value: string) => setSelectedArticle(value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select article" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ABCC11">ABCC11</SelectItem>
              <SelectItem value="APRT">APRT</SelectItem>
              <SelectItem value="B3GAT1">B3GAT1</SelectItem>
              <SelectItem value="GRIA2">GRIA2</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={selectedSource}
            onValueChange={(value: "wikipedia" | "wikicrow") =>
              setSelectedSource(value)
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="wikipedia">Wikipedia</SelectItem>
              <SelectItem value="wikicrow">WikiCrow</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            onClick={() => {
              setShowRequirements(!showRequirements);
              setSidePanelOpen(false);
            }}
          >
            {showRequirements ? "Hide Requirements" : "View Requirements"}
          </Button>
        </div>
      </div>

      <div className="flex gap-8 mt-8">
        <div className="w-[400px] shrink-0">
          <InfoBox />
        </div>

        <div className="flex-1">
          <div className="space-y-4">
            {data && (
              <ArticleRenderer
                articleData={data[selectedSource].article}
                evaluationData={convertCacheToEvalData(
                  data[selectedSource].evaluation
                )}
                highlightEnabled={highlightEnabled}
                onElementClick={handleElementClick}
              />
            )}
          </div>
        </div>
      </div>

      <SidePanel
        isOpen={isSidePanelOpen}
        onClose={() => setSidePanelOpen(false)}
        selectedText={selectedText}
        selectedType={selectedType}
        evaluationData={selectedEvaluation.data}
        sectionIndex={selectedEvaluation.sectionIndex}
        sentenceIndex={selectedEvaluation.sentenceIndex}
      />
    </div>
  );
}
