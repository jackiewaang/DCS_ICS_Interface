import { CircleHelp } from 'lucide-react';

export function DashboardHelp({ text }) {
  return (
    <div className="group relative inline-flex items-center hover:z-50">
      <button
        type="button"
        aria-label="Show more information"
        className="inline-flex cursor-pointer items-center text-muted-foreground transition-colors hover:text-foreground"
      >
        <CircleHelp className="h-4 w-4" />
      </button>
      <div className="pointer-events-none absolute left-1/2 top-full mt-2 w-72 -translate-x-1/2 rounded-lg border border-border bg-background px-3 py-2 text-xs leading-relaxed text-muted-foreground opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        {text}
      </div>
    </div>
  );
}

export function DashboardPanelFrame({ title, helpText, children, headerActions = null, className = '' }) {
  return (
    <section className={`rounded-xl border border-border bg-white p-6 text-card-foreground shadow-sm ${className}`.trim()}>
      <div className="mb-5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
          {helpText ? <DashboardHelp text={helpText} /> : null}
        </div>

        {headerActions ? (
          <div className="flex items-center gap-2">
            {headerActions}
          </div>
        ) : null}
      </div>

      {children}
    </section>
  );
}
