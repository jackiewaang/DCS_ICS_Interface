import { useEffect, useState } from 'react';
import { Download, Maximize2, Minimize2 } from 'lucide-react';
import CaseHeader from '@/components/CaseHeader';
import MainOverviewPanel from '@/components/dashboard/MainOverviewPanel';
import AIInsightsPanel from '@/components/dashboard/AIInsightsPanel';
import HeatmapPanel from '@/components/dashboard/HeatmapPanel';
import FeaturesPanel from '@/components/dashboard/FeaturesPanel';
import EntitiesPanel from '@/components/dashboard/EntitiesPanel';
import { Button } from '@/components/ui/button';
import ErrorAlert from '@/components/ui/ErrorAlert';
import useLLMFeedback from '@/hooks/useLLMFeedback';
import { exportAnalysisPdf } from '@/services/exportAnalysisPdf';
import { getUserErrorMessage } from '@/helper/error_messages';

const TABS = [
  { id: 'main', label: 'Main' },
  { id: 'ai', label: 'AI Insights' },
  { id: 'heatmap', label: 'Heatmap' },
  { id: 'features', label: 'Features' },
  { id: 'entities', label: 'Entities' },
];

export default function InferenceResults({ data, onResultUpdate }) {
  const [activeTab, setActiveTab] = useState('main');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [exportError, setExportError] = useState('');
  const savedLlmState = data?.llm_feedback;
  const hasSavedFeedback = ['completed', 'error'].includes(savedLlmState?.status);
  const generatedLlmState = useLLMFeedback(hasSavedFeedback ? null : data?.llm_input);
  const llmState = hasSavedFeedback ? savedLlmState : generatedLlmState;

  useEffect(() => {
    if (!data || hasSavedFeedback || !['completed', 'error'].includes(generatedLlmState.status)) {
      return;
    }

    onResultUpdate?.({
      ...data,
      llm_feedback: {
        result: generatedLlmState.result,
        status: generatedLlmState.status,
        errorMessage: generatedLlmState.errorMessage,
      },
    });
  }, [data, generatedLlmState, hasSavedFeedback, onResultUpdate]);

  useEffect(() => {
    if (!isFullscreen) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setIsFullscreen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const handleExport = () => {
    setExportError('');
    try {
      exportAnalysisPdf(data, llmState);
    } catch (error) {
      console.error('PDF export failed:', error);
      setExportError(getUserErrorMessage(error, 'The PDF could not be created. Please try again.'));
    }
  };

  if (!data) {
    return (
      <section className="flex h-full min-h-96 items-center justify-center rounded-lg border border-dashed border-border bg-white p-8 text-center shadow-sm">
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
    <section className={`flex min-h-0 flex-col overflow-hidden border border-border bg-white shadow-sm ${
      isFullscreen
        ? 'fixed inset-0 z-50 h-screen rounded-none'
        : 'h-full min-h-[36rem] rounded-lg'
    }`}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-white px-5 py-4">
        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Inference results
        </span>
        <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={() => setIsFullscreen((current) => !current)}
            aria-label={isFullscreen ? 'Exit fullscreen inference results' : 'View inference results fullscreen'}
            title={isFullscreen ? 'Exit fullscreen (Esc)' : 'View fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={handleExport}
            className="h-9 gap-2 cursor-pointer"
          >
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>

      {exportError ? (
        <div className="border-b border-border px-5 py-3">
          <ErrorAlert
            title="PDF export failed"
            message={exportError}
            onRetry={handleExport}
            onDismiss={() => setExportError('')}
          />
        </div>
      ) : null}

      <CaseHeader data={data} />

      <div className="px-5 pt-4">
        <div className="flex flex-wrap gap-2 border-b border-border bg-white pb-2">
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

      <main className="min-h-0 flex-1 overflow-y-auto bg-white px-5 py-5">
        {activeTab === 'main' && <MainOverviewPanel data={data} />}
        {activeTab === 'ai' && <AIInsightsPanel data={data} llmState={llmState} />}
        {activeTab === 'heatmap' && <HeatmapPanel data={data} />}
        {activeTab === 'features' && <FeaturesPanel data={data} />}
        {activeTab === 'entities' && <EntitiesPanel data={data} />}
      </main>
    </section>
  );
}
