import React, { useState, useMemo, useCallback } from "react";
import {
  ChevronRight,
  ChevronDown,
  Search,
  X,
  AlertCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import requirementsData from "@/lib/data/requirements.json";

export interface Requirement {
  id: string;
  description: string;
  reference: string;
  category: string;
  classification: string;
  where: string;
  when: string;
}

export interface RequirementEvaluation {
  requirement_id: string;
  requirement_category: string;
  classification: string;
  applicable: boolean;
  applicability_reasoning: string;
  score: number;
  confidence: number;
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

interface RequirementViewerProps {
  focusedId?: string;
  onRequirementClick?: (id: string) => void;
  isLoading?: boolean;
  error?: string;
  evaluations?: RequirementEvaluation[];
}

interface CategoryProps {
  category: string;
  classifications: {
    [classification: string]: Requirement[];
  };
  expandedCategories: { [key: string]: boolean };
  toggleCategory: (category: string) => void;
  expandedClassifications: { [key: string]: boolean };
  toggleClassification: (category: string, classification: string) => void;
  expandedRequirements: { [key: string]: boolean };
  toggleRequirement: (id: string) => void;
  focusedId?: string;
  searchTerm: string;
  evaluations?: RequirementEvaluation[];
}

interface RequirementGroup {
  description: string;
  category: string;
  requirements: Requirement[];
}

interface RequirementsData {
  groups: RequirementGroup[];
}

const getClassificationColor = (classification: string): string => {
  const colors = {
    "Imperative Standards": "bg-red-100 text-red-800",
    "Best Practices": "bg-blue-100 text-blue-800",
    "Flexible Guidelines": "bg-green-100 text-green-800",
  };
  return (
    colors[classification as keyof typeof colors] || "bg-gray-100 text-gray-800"
  );
};

const RequirementCard: React.FC<{
  requirement: Requirement;
  isExpanded: boolean;
  onToggle: () => void;
  isFocused: boolean;
  evaluations?: RequirementEvaluation[];
}> = ({ requirement, isExpanded, onToggle, isFocused, evaluations }) => {
  const evaluation = evaluations?.[0];

  return (
    <Card
      className={cn(
        "border-l-4 transition-all hover:shadow-sm",
        isFocused ? "border-l-blue-500 shadow-md" : "border-l-transparent",
        isExpanded && "shadow-sm"
      )}
    >
      <CollapsibleTrigger className="w-full" onClick={onToggle}>
        <CardHeader className="py-3 hover:bg-gray-50/80 transition-colors">
          <div className="flex items-center gap-3">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )}
            <div className="flex items-start gap-3 flex-1">
              <Badge
                variant="outline"
                className={cn(
                  "w-12 shrink-0",
                  isFocused && "bg-blue-50 border-blue-200"
                )}
              >
                #{requirement.id}
              </Badge>
              <span className="text-sm font-medium text-left">
                {requirement.description}
              </span>
            </div>
          </div>
        </CardHeader>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <CardContent className="space-y-4 pt-0">
          <div className="text-sm text-gray-600 bg-gray-50/50 p-3 rounded-md">
            {requirement.reference}
          </div>

          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-xs">
                Where: {requirement.where}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                When: {requirement.when}
              </Badge>
            </div>

            {evaluation && (
              <div className="border rounded-md p-3 space-y-3 bg-gray-50/50">
                <h4 className="text-sm font-medium text-gray-900">
                  Evaluation Results
                </h4>
                <div className="flex flex-wrap gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      evaluation.applicable
                        ? "bg-green-50 border-green-200 text-green-700"
                        : "bg-red-50 border-red-200 text-red-700"
                    )}
                  >
                    {evaluation.applicable ? "Applicable" : "Not Applicable"}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      evaluation.score >= 0.7
                        ? "bg-green-50 border-green-200 text-green-700"
                        : evaluation.score >= 0.4
                        ? "bg-yellow-50 border-yellow-200 text-yellow-700"
                        : "bg-red-50 border-red-200 text-red-700"
                    )}
                  >
                    Score: {(evaluation.score * 100).toFixed(0)}%
                  </Badge>
                  <Badge
                    variant="outline"
                    className="text-xs bg-blue-50 border-blue-200 text-blue-700"
                  >
                    Confidence: {(evaluation.confidence * 100).toFixed(0)}%
                  </Badge>
                </div>
                {evaluation.reasoning && (
                  <p className="text-sm text-gray-600">
                    {evaluation.reasoning}
                  </p>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </CollapsibleContent>
    </Card>
  );
};

const CategorySection: React.FC<CategoryProps> = ({
  category,
  classifications,
  expandedCategories,
  toggleCategory,
  expandedClassifications,
  toggleClassification,
  expandedRequirements,
  toggleRequirement,
  focusedId,
  searchTerm,
  evaluations,
}) => {
  const filteredClassifications = useMemo(() => {
    if (!searchTerm) return classifications;

    const filtered: typeof classifications = {};
    Object.entries(classifications).forEach(
      ([classification, requirements]) => {
        const matchingReqs = requirements.filter(
          (req) =>
            req.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
            req.reference.toLowerCase().includes(searchTerm.toLowerCase())
        );
        if (matchingReqs.length > 0) {
          filtered[classification] = matchingReqs;
        }
      }
    );
    return filtered;
  }, [classifications, searchTerm]);

  if (Object.keys(filteredClassifications).length === 0) return null;

  return (
    <Card className="w-full">
      <Collapsible
        open={expandedCategories[category]}
        onOpenChange={() => toggleCategory(category)}
      >
        <CollapsibleTrigger className="w-full">
          <CardHeader className="hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-2">
              {expandedCategories[category] ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <CardTitle>{category}</CardTitle>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="space-y-4">
            {Object.entries(filteredClassifications).map(
              ([classification, requirements]) => (
                <Collapsible
                  key={classification}
                  open={
                    expandedClassifications[`${category}-${classification}`]
                  }
                  onOpenChange={() =>
                    toggleClassification(category, classification)
                  }
                >
                  <CollapsibleTrigger className="w-full">
                    <div className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded transition-colors">
                      {expandedClassifications[
                        `${category}-${classification}`
                      ] ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                      <Badge className={getClassificationColor(classification)}>
                        {classification}
                      </Badge>
                      <span className="text-sm text-gray-500">
                        ({requirements.length} requirements)
                      </span>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <div className="pl-6 space-y-3">
                      {requirements.map((req) => (
                        <Collapsible
                          key={req.id}
                          open={expandedRequirements[req.id]}
                        >
                          <RequirementCard
                            requirement={req}
                            isExpanded={expandedRequirements[req.id]}
                            onToggle={() => toggleRequirement(req.id)}
                            isFocused={focusedId === req.id}
                            evaluations={evaluations?.filter(
                              (evaluation) =>
                                evaluation.requirement_id === req.id
                            )}
                          />
                        </Collapsible>
                      ))}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              )
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

const LoadingSkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="animate-pulse">
        <div className="h-12 bg-gray-100 rounded-lg mb-2"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-100 rounded w-3/4"></div>
          <div className="h-4 bg-gray-100 rounded w-1/2"></div>
        </div>
      </div>
    ))}
  </div>
);

const EmptyState = ({ searchTerm }: { searchTerm: string }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <AlertCircle className="w-12 h-12 text-gray-400 mb-4" />
    <h3 className="text-lg font-medium text-gray-900 mb-2">
      No requirements found
    </h3>
    {searchTerm ? (
      <p className="text-gray-500">
        No requirements match your search "{searchTerm}". Try adjusting your
        search terms.
      </p>
    ) : (
      <p className="text-gray-500">
        Start by selecting a category or searching for specific requirements.
      </p>
    )}
  </div>
);

export const RequirementViewer: React.FC<RequirementViewerProps> = ({
  focusedId,
  onRequirementClick,
  isLoading,
  error,
  evaluations,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<{
    [key: string]: boolean;
  }>({});
  const [expandedClassifications, setExpandedClassifications] = useState<{
    [key: string]: boolean;
  }>({});
  const [expandedRequirements, setExpandedRequirements] = useState<{
    [key: string]: boolean;
  }>({});

  const requirementsDataTyped = requirementsData as RequirementsData;

  const processedData = useMemo(() => {
    const categorizedReqs: {
      [category: string]: { [classification: string]: Requirement[] };
    } = {};

    requirementsDataTyped.groups.forEach((group) => {
      group.requirements.forEach((req) => {
        if (!categorizedReqs[req.category]) {
          categorizedReqs[req.category] = {};
        }
        if (!categorizedReqs[req.category][req.classification]) {
          categorizedReqs[req.category][req.classification] = [];
        }
        categorizedReqs[req.category][req.classification].push(req);
      });
    });

    return {
      groups: categorizedReqs,
    };
  }, [requirementsDataTyped]);

  const stats = useMemo(() => {
    const totalReqs = Object.values(processedData.groups).reduce(
      (acc, category) =>
        acc +
        Object.values(category).reduce(
          (sum, classification) => sum + classification.length,
          0
        ),
      0
    );
    const totalCategories = Object.keys(processedData.groups).length;
    return { totalReqs, totalCategories };
  }, [processedData]);

  const toggleCategory = useCallback((category: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  }, []);

  const toggleClassification = useCallback(
    (category: string, classification: string) => {
      const key = `${category}-${classification}`;
      setExpandedClassifications((prev) => ({
        ...prev,
        [key]: !prev[key],
      }));
    },
    []
  );

  const toggleRequirement = useCallback(
    (id: string) => {
      setExpandedRequirements((prev) => ({
        ...prev,
        [id]: !prev[id],
      }));
      onRequirementClick?.(id);
    },
    [onRequirementClick]
  );

  if (isLoading) {
    return (
      <div className="p-4">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-500 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-screen">
      <div className="p-4 space-y-6">
        <div className="sticky top-0 bg-white/80 backdrop-blur-sm z-10 pb-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Requirements
              </h2>
              <p className="text-sm text-gray-500">
                {stats.totalReqs} requirements across {stats.totalCategories}{" "}
                categories
              </p>
            </div>
          </div>

          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              type="text"
              placeholder="Search requirements..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-8 transition-shadow focus:shadow-md"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="absolute right-2 top-2.5 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {Object.keys(processedData.groups).length === 0 ? (
          <EmptyState searchTerm={searchTerm} />
        ) : (
          Object.entries(processedData.groups).map(
            ([category, classifications]) => (
              <CategorySection
                key={category}
                category={category}
                classifications={classifications}
                expandedCategories={expandedCategories}
                toggleCategory={toggleCategory}
                expandedClassifications={expandedClassifications}
                toggleClassification={toggleClassification}
                expandedRequirements={expandedRequirements}
                toggleRequirement={toggleRequirement}
                focusedId={focusedId}
                searchTerm={searchTerm}
                evaluations={evaluations}
              />
            )
          )
        )}
      </div>
    </ScrollArea>
  );
};
