import { useState } from 'react';
import { Download } from 'lucide-react';
import CaseHeader from '@/components/CaseHeader';
import MainOverviewPanel from '@/components/dashboard/MainOverviewPanel';
import AIInsightsPanel from '@/components/dashboard/AIInsightsPanel';
import HeatmapPanel from '@/components/dashboard/HeatmapPanel';
import FeaturesPanel from '@/components/dashboard/FeaturesPanel';
import EntitiesPanel from '@/components/dashboard/EntitiesPanel';
import { Button } from '@/components/ui/button';
import useLLMInference from '@/hooks/useLLMInference';
import { exportAnalysisPdf } from '@/services/exportAnalysisPdf';

const TABS = [
  { id: 'main', label: 'Main' },
  { id: 'ai', label: 'AI Insights' },
  { id: 'heatmap', label: 'Heatmap' },
  { id: 'features', label: 'Features' },
  { id: 'entities', label: 'Entities' },
];

export default function InferenceResults({ data }) {
  const [activeTab, setActiveTab] = useState('main');
  const llmState = useLLMInference(data?.inference_id);
  const currentLlmState = llmState.inferenceId === data?.inference_id
    ? llmState
    : { inferenceId: data?.inference_id, result: null, status: 'loading', errorMessage: '' };

  if (!data) {
    return (
      <section className="flex h-full min-h-96 items-center justify-center rounded-lg border border-dashed border-border bg-card p-8 text-center shadow-sm">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Inference results
          </span>
          <p className="mt-2 text-sm text-muted-foreground">
            Run inference to display model output here.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted px-5 py-4">
        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Inference results
        </span>
        <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => exportAnalysisPdf(data, currentLlmState)}
            className="h-9 gap-2"
          >
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>

      <CaseHeader data={data} />

      <div className="px-5 pt-4">
        <div className="flex flex-wrap gap-2 border-b border-border bg-background pb-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`cursor-pointer border-0 border-b-2 bg-transparent px-4 py-2 text-sm font-semibold transition-all ${
                activeTab === tab.id
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:border-border hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <main className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        {activeTab === 'main' && <MainOverviewPanel data={data} />}
        {activeTab === 'ai' && <AIInsightsPanel data={data} llmState={currentLlmState} />}
        {activeTab === 'heatmap' && <HeatmapPanel data={data} />}
        {activeTab === 'features' && <FeaturesPanel data={data} />}
        {activeTab === 'entities' && <EntitiesPanel data={data} />}
      </main>
    </section>
  );
}
