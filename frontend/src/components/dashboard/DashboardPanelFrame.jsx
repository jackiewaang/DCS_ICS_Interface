import { useEffect, useState } from 'react';
import { CircleHelp, Maximize2, X } from 'lucide-react';

export function DashboardHelp({ text }) {
  return (
    <div className="group relative inline-flex items-center hover:z-50">
      <button
        type="button"
        aria-label="Show more information"
        className="inline-flex items-center text-muted-foreground transition-colors hover:text-foreground"
      >
        <CircleHelp className="h-4 w-4" />
      </button>
      <div className="pointer-events-none absolute left-1/2 top-full mt-2 w-72 -translate-x-1/2 rounded-lg border border-border bg-background px-3 py-2 text-xs leading-relaxed text-muted-foreground opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        {text}
      </div>
    </div>
  );
}

export function DashboardPanelFrame({ title, helpText, children, expandedChildren, headerActions = null, className = '' }) {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!isExpanded) {
      return undefined;
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsExpanded(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isExpanded]);

  return (
    <>
      <section className={`rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm ${className}`.trim()}>
        <div className="mb-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
            {helpText ? <DashboardHelp text={helpText} /> : null}
          </div>

          <div className="flex items-center gap-2">
            {headerActions}

            <button
              type="button"
              onClick={() => setIsExpanded(true)}
              aria-label={`Expand ${title} panel`}
              className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border bg-background text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        {children}
      </section>

      {isExpanded && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/75 px-4 py-6 backdrop-blur-sm">
          <div className="relative flex h-full max-h-[94vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
                {helpText ? <DashboardHelp text={helpText} /> : null}
              </div>

              <div className="flex items-center gap-2">
                {headerActions}

                <button
                  type="button"
                  onClick={() => setIsExpanded(false)}
                  aria-label={`Close expanded ${title} panel`}
                  className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border bg-background text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {expandedChildren || children}
            </div>
          </div>
        </div>
      )}
    </>
  );
}