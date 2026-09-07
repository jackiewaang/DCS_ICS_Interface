import { useState } from 'react';
import { Download, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ErrorAlert from '@/components/ui/ErrorAlert';
import { exportGemmaPdf } from '@/services/exportGemmaPdf';
import { getUserErrorMessage } from '@/helper/error_messages';

function formatDuration(milliseconds) {
  if (!Number.isFinite(milliseconds)) return 'Not available';
  return `${(milliseconds / 1000).toFixed(1)} seconds`;
}

export default function GemmaResults({ data }) {
  const [exportError, setExportError] = useState('');

  if (!data) {
    return (
      <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-border bg-card p-8 text-center">
        <div>
          <Sparkles className="mx-auto h-8 w-8 text-muted-foreground" />
          <h2 className="mt-4 text-lg font-semibold text-foreground">No Gemma assessment yet</h2>
          <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
            Extract or enter the case-study sections, then run the fine-tuned model.
          </p>
        </div>
      </section>
    );
  }

  const handleExport = () => {
    setExportError('');
    try {
      exportGemmaPdf(data);
    } catch (error) {
      console.error('Gemma PDF export failed:', error);
      setExportError(getUserErrorMessage(error, 'The PDF could not be created. Please try again.'));
    }
  };

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card p-5 shadow-sm">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">Gemma assessment</p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">{data.title || 'Untitled inference'}</h2>
          <p className="mt-1 text-xs text-muted-foreground">Inference time: {formatDuration(data.inference_time_ms)}</p>
        </div>
        <Button type="button" variant="outline" onClick={handleExport} className="h-9 gap-2 cursor-pointer">
          <Download className="h-4 w-4" />
          Export PDF
        </Button>
      </div>

      {exportError ? (
        <ErrorAlert
          title="PDF export failed"
          message={exportError}
          onRetry={handleExport}
          onDismiss={() => setExportError('')}
        />
      ) : null}

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Predicted REF GPA
        </p>
        <div className="mt-3 flex items-end gap-3">
          <p className="text-5xl font-semibold tracking-tight text-primary">
            {Number(data.score).toFixed(2)}
          </p>
          <p className="pb-1 text-sm text-muted-foreground">out of 4.00</p>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">{data.model_name}</p>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 border-b border-border pb-4">
          <Sparkles className="h-5 w-5 text-accent" />
          <h2 className="text-lg font-semibold text-foreground">Diagnostic comments</h2>
        </div>
        <div className="mt-5 whitespace-pre-wrap text-sm leading-7 text-foreground">
          {data.comments}
        </div>
      </div>
    </section>
  );
}
