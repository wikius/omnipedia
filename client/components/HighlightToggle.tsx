// components/HighlightToggle.tsx
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

interface HighlightToggleProps {
  enabled: boolean;
  onToggle: () => void;
}

export const HighlightToggle: React.FC<HighlightToggleProps> = ({
  enabled,
  onToggle,
}) => {
  return (
    <div className="flex items-center space-x-2">
      <Switch
        id="highlight-mode"
        checked={enabled}
        onCheckedChange={onToggle}
      />
      <Label htmlFor="highlight-mode">
        {enabled ? "Disable Highlights" : "Enable Highlights"}
      </Label>
    </div>
  );
};
