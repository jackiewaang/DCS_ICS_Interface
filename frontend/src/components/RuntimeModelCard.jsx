import { RotateCcw } from 'lucide-react';

export default function RuntimeModelCard({ icon: Icon, label, value, error, onRetry }) {
  const displayValue = error ? 'Could not load' : value || 'Unavailable';

  return (
    <div className="rounded-md border border-sidebar-border bg-sidebar-accent p-3">
      <div className="flex items-center gap-2 text-sidebar-foreground/70">
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span className="text-[10px] font-semibold uppercase tracking-wider">{label}</span>
      </div>
      <div className="mt-1.5 flex items-center gap-2">
        <p
          className={`min-w-0 flex-1 truncate text-xs font-medium ${error ? 'text-red-200' : 'text-sidebar-accent-foreground'}`}
          title={error || displayValue}
        >
          {displayValue}
        </p>
        {error && onRetry ? (
          <button type="button" onClick={onRetry} aria-label={`Retry loading ${label}`} title={error} className="cursor-pointer text-red-200 hover:text-white">
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
