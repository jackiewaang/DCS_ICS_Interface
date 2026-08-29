import { AlertCircle, RotateCcw, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ErrorAlert({ title = 'Something went wrong', message, onRetry, onDismiss, className = '' }) {
  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-destructive ${className}`.trim()}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">{title}</p>
        {message ? <p className="mt-1 text-sm leading-relaxed">{message}</p> : null}
      </div>
      {onRetry ? (
        <Button type="button" variant="outline" size="sm" onClick={onRetry} className="border-destructive/30 bg-white text-destructive hover:bg-destructive/10">
          <RotateCcw className="h-3.5 w-3.5" />
          Retry
        </Button>
      ) : null}
      {onDismiss ? (
        <Button type="button" variant="ghost" size="icon-sm" onClick={onDismiss} aria-label="Dismiss error" className="text-destructive hover:bg-destructive/10">
          <X className="h-4 w-4" />
        </Button>
      ) : null}
    </div>
  );
}
