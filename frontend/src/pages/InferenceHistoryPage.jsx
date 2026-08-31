import { AlertCircle, CheckCircle2, Clock3, History, Loader2 } from 'lucide-react';
import InferenceResults from '@/components/InferenceResults';

function formatDate(value) {
  if (!value) return 'This session';

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'This session' : date.toLocaleString();
}

function LlmStatus({ status, isSelected }) {
  const tone = isSelected ? 'text-primary-foreground/75' : 'text-muted-foreground';

  if (status === 'running') {
    return <span className={`mt-2 flex items-center gap-1.5 text-[11px] ${tone}`}><Loader2 className="h-3 w-3 animate-spin" />AI insights generating</span>;
  }
  if (status === 'completed') {
    return <span className={`mt-2 flex items-center gap-1.5 text-[11px] ${tone}`}><CheckCircle2 className="h-3 w-3" />AI insights ready</span>;
  }
  if (status === 'error') {
    return <span className={`mt-2 flex items-center gap-1.5 text-[11px] ${tone}`}><AlertCircle className="h-3 w-3" />AI insights failed</span>;
  }
  return null;
}

export default function InferenceHistoryPage({ history, selectedId, onSelect }) {
  const selectedResult = history.find((item) => item.inference_id === selectedId) || history[0] || null;

  return (
    <div className="flex h-full min-h-0 flex-col gap-5 p-6 md:p-8">
      <header className="flex shrink-0 flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem]">
              Inference History
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Results generated during the current browser session.
            </p>
          </div>
        </div>
        <aside className="max-w-2xl rounded-md border border-border bg-white px-4 py-3 text-xs leading-relaxed text-muted-foreground lg:ml-auto">
          <p>
            Analysis results are not stored as database cases and are cleared from the browser when the page is refreshed. Submitted text, model outputs, and usage activity are logged for research analysis using a randomly generated session identifier rather than your name or other direct identifiers.
          </p>
          <p className="mt-2 font-medium text-foreground">
            Avoid keeping too many results in one session, as browser memory usage will increase. Export important results as PDFs before refreshing the page.
          </p>
        </aside>
      </header>

      <div className="grid min-h-0 flex-1 grid-rows-[18rem_minmax(0,1fr)] gap-5 xl:grid-cols-[19rem_minmax(0,1fr)] xl:grid-rows-1">
        <aside className="flex min-h-48 flex-col overflow-hidden rounded-lg border border-border bg-white shadow-sm">
          <div className="border-b border-border px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">
              Saved results · {history.length}
            </p>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-2">
            {history.length === 0 ? (
              <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                Run an inference to add it here.
              </div>
            ) : (
              <div className="space-y-2">
                {history.map((result) => {
                  const isSelected = result.inference_id === selectedResult?.inference_id;
                  return (
                    <button
                      key={result.inference_id}
                      type="button"
                      onClick={() => onSelect(result.inference_id)}
                      className={`w-full cursor-pointer rounded-md border px-3 py-3 text-left transition-colors ${
                        isSelected
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border bg-white text-foreground hover:bg-muted/50'
                      }`}
                    >
                      <p className="truncate text-sm font-semibold">{result.title || 'Untitled inference'}</p>
                      <p className={`mt-1 truncate text-xs ${isSelected ? 'text-primary-foreground/75' : 'text-muted-foreground'}`}>
                        {result.model_name || 'Selected model'}
                      </p>
                      <p className={`mt-2 flex items-center gap-1.5 text-[11px] ${isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                        <Clock3 className="h-3 w-3" />
                        {formatDate(result.created_at)}
                      </p>
                      <LlmStatus status={result.llm_feedback?.status} isSelected={isSelected} />
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        <div className="min-h-0">
          <InferenceResults data={selectedResult} />
        </div>
      </div>
    </div>
  );
}
