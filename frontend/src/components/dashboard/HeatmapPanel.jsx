import { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

function getHeatmapTone(normalizedScore) {
  if (normalizedScore < 0.2) return 'bg-slate-50 text-slate-700 border-slate-200';
  if (normalizedScore < 0.4) return 'bg-sky-100 text-slate-800 border-sky-200';
  if (normalizedScore < 0.6) return 'bg-cyan-200 text-slate-900 border-cyan-300';
  if (normalizedScore < 0.8) return 'bg-blue-400 text-white border-blue-500';
  if (normalizedScore < 0.92) return 'bg-indigo-600 text-white border-indigo-700';
  return 'bg-violet-800 text-white border-violet-900';
}

export default function HeatmapPanel({ data }) {
  const [heatmapView, setHeatmapView] = useState('top');
  const heatmap = useMemo(() => data?.heatmap || [], [data?.heatmap]);
  const hasMLData = Array.isArray(heatmap) && heatmap.length > 0;

  let panelContent;

  if (!hasMLData) {
    panelContent = (
      <div className="rounded-lg border border-border bg-muted/40 p-6 text-center">
        <p className="text-sm text-muted-foreground">
          Sentence-level attention analysis is not available for this model configuration.
        </p>
      </div>
    );
  } else {
    const maxWeight = Math.max(...heatmap.map((sentence) => sentence.attention_score));
    const minWeight = Math.min(...heatmap.map((sentence) => sentence.attention_score));
    const avgWeight = heatmap.reduce((sum, sentence) => sum + sentence.attention_score, 0) / heatmap.length;
    const range = maxWeight - minWeight || 1;
    const normalizedHeatmap = heatmap
      .map((sentence) => ({
        ...sentence,
        normalizedScore: (sentence.attention_score - minWeight) / range,
      }))
      .sort((left, right) => right.attention_score - left.attention_score);

    const visibleHeatmap =
      heatmapView === 'full'
        ? normalizedHeatmap
        : heatmapView === 'top'
          ? normalizedHeatmap.slice(0, 10)
          : [...normalizedHeatmap].reverse().slice(0, 10);

    const nextView = heatmapView === 'top' ? 'worst' : heatmapView === 'worst' ? 'full' : 'top';
    const nextViewLabel = heatmapView === 'top' ? 'Show worst 10' : heatmapView === 'worst' ? 'Show full heatmap' : 'Show top 10';
    const currentViewLabel = heatmapView === 'top' ? 'top 10 highest-attention sentences' : heatmapView === 'worst' ? 'worst 10 lowest-attention sentences' : 'the full attention heatmap';
    const toggleHint =
      heatmapView === 'top'
        ? 'Click to switch to the lowest-attention sentences.'
        : heatmapView === 'worst'
          ? 'Click to expand to the full ordered heatmap.'
          : 'Click to return to the top 10 highest-attention sentences.';

    panelContent = (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-[1.6fr_1fr] md:items-start">
          <div className="space-y-3">
          <div className="grid grid-cols-3 gap-2 border-b border-border/40 pb-2.5 text-center md:text-left">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">Peak Sentence Attention</span>
              <span className="font-mono text-sm font-bold text-foreground mt-0.5 block">{maxWeight.toFixed(4)}</span>
            </div>
            <div className="border-l border-border/60 pl-3">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">Mean Sentence Attention</span>
              <span className="font-mono text-sm font-bold text-foreground mt-0.5 block">{avgWeight.toFixed(4)}</span>
            </div>
            <div className="border-l border-border/60 pl-3">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">Currently Viewing</span>
              <span className="font-mono text-sm font-bold text-foreground mt-0.5 block">{currentViewLabel}</span>
            </div>
          </div>

          <div className="rounded-md border border-border/50 bg-muted/20 p-2 text-[11px] leading-relaxed text-muted-foreground/90">
            <div className="flex flex-col gap-1 sm:flex-row sm:gap-4">
              <div>
                <span className="font-bold text-foreground">Raw Weight Score:</span> The absolute distribution probability from the AttentionMIL layer. Higher scores denote primary text evidence.
              </div>
              <div className="sm:border-l sm:border-border/60 sm:pl-4">
                <span className="font-bold text-foreground">Salience:</span> Max-relative normalization score calculated as (Sentence Weight / Peak Weight) * 100. Maps internal document priority.
              </div>
            </div>
          </div>
        </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wide text-muted-foreground">
              <span>Attention Scale</span>
              <span>Low to High</span>
            </div>
            <div
              className="h-3 overflow-hidden rounded-full border border-border bg-muted"
              style={{ backgroundImage: 'linear-gradient(90deg, #f8fafc 0%, #dbeafe 18%, #bae6fd 36%, #7dd3fc 54%, #60a5fa 72%, #4f46e5 88%, #6d28d9 100%)' }}
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Low attention</span>
              <span>High attention</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            Showing {visibleHeatmap.length} of {heatmap.length} sentences ordered by attention weight. {toggleHint}
          </p>

          <button
            type="button"
            onClick={() => setHeatmapView(nextView)}
            className="cursor-pointer inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-accent"
          >
            {heatmapView === 'full' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {nextViewLabel}
          </button>
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-background/80 shadow-sm">
          <div className="h-152 overflow-y-auto p-4 custom-scrollbar bg-background/30">
            <div className="prose prose-sm max-w-none text-foreground select-text">
              <p className="text-sm leading-relaxed tracking-normal inline">
                {visibleHeatmap.map((sentence, idx) => {
                  const pct = (sentence.normalizedScore * 100).toFixed(0);
                  const rawScore = sentence.attention_score.toFixed(4);

                  const tooltipPositionClass = idx < 4
                    ? 'top-full mt-1'
                    : 'bottom-full mb-1';

                  return (
                    <span
                      key={`${sentence.sentence_text}-${idx}`}
                      className={`${getHeatmapTone(sentence.normalizedScore)} group relative mr-1 mb-1 inline-block cursor-help rounded border px-1 py-0.5 transition-all duration-200 hover:scale-[1.02] hover:z-50 hover:shadow-md`}
                    >
                      {sentence.sentence_text}

                    <span className={`${tooltipPositionClass} absolute pointer-events-none left-1/2 z-50 mb-2 hidden -translate-x-1/2 group-hover:flex`}>
                      <span className="whitespace-nowrap rounded bg-foreground px-2 py-1 text-xs text-background shadow-lg">
                        Weight: {rawScore} | Salience: {pct}%
                      </span>
                    </span>
                  </span>
                  );
  })}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <DashboardPanelFrame
      title="Attention Heatmap"
      helpText="Sentence-level attention summary and hoverable highlights for the selected case."
    >
      {panelContent}
    </DashboardPanelFrame>
  );
}
