import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";

export const InfoBox = () => {
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="w-5 h-5" />
          Interactive Article Guide
        </CardTitle>
        <CardDescription>
          Understanding how to interact with the article elements
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert className="bg-muted">
          <AlertDescription>
            This article features interactive elements that reveal evaluation
            results at different levels. Clicking different parts of the article
            will display relevant evaluation details in the side panel.
          </AlertDescription>
        </Alert>

        <div className="space-y-4">
          <div>
            <h3 className="font-medium mb-2">Interactive Elements:</h3>
            <ul className="space-y-2 ml-4">
              <li className="text-sm">
                <span className="font-medium">Section Headers:</span> Click any
                section header (like &quot;ABCC11&quot; or &quot;Function&quot;)
                to see section-level evaluation results
              </li>
              <li className="text-sm">
                <span className="font-medium">Individual Sentences:</span> Each
                sentence is clickable and shows specific evaluation results for
                that sentence
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-medium mb-2">Controls:</h3>
            <ul className="space-y-2 ml-4">
              <li className="text-sm">
                <span className="font-medium">Highlight Toggle:</span> Use the
                switch in the top-right to show/hide evaluation highlights
              </li>
              <li className="text-sm">
                <span className="font-medium">Side Panel:</span> Automatically
                opens when clicking any element, showing relevant evaluation
                details
              </li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
