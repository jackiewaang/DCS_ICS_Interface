import { Terminal } from "lucide-react";

const PromptLab = () => (
  <div className="flex h-full items-center justify-center p-8 text-center">
    <div className="max-w-md space-y-4">
      <div className="mx-auto w-16 h-16 bg-secondary rounded-full flex items-center justify-center mb-4">
        <Terminal className="h-8 w-8 text-muted-foreground" />
      </div>
      <h2 className="text-2xl font-bold text-foreground">Prompt Engineering</h2>
      <p className="text-muted-foreground">
        Test and refine extraction prompts for the LLM pipeline to improve how entities and evidence are identified.
      </p>
      <p>Work in progress</p>
    </div>
  </div>
);

export default PromptLab;
