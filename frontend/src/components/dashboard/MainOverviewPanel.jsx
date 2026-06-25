import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

export default function MainOverviewPanel({ data }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-xl font-semibold text-foreground">Overview</h2>
        <p className="mt-2 text-sm text-muted-foreground">No case loaded.</p>
      </section>
    );
  }

  const confidence = data.model_prediction ?? 0;
  const isHighImpact = data.prediction_label ? data.prediction_label === "High Impact" : confidence >= 0.5;
  const displayPrediction = data.prediction_label || (isHighImpact ? "High Impact" : "Low Impact");
  const confidencePercentage = (isHighImpact ? confidence : (1 - confidence)) * 100;
  const humanImpactLevel = data.ground_truth !== null && data.ground_truth !== undefined
    ? (data.ground_truth >= 3 ? "High Impact" : "Low Impact")
    : null;
  const refGuidelinesUrl = 'https://www.ref.ac.uk/guidance/';

  const openRefGuidelines = () => {
    window.open(refGuidelinesUrl, '_blank', 'noopener,noreferrer');
  };

  const panelContent = (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-background/80 p-5 shadow-sm transition-shadow hover:bg-background hover:shadow-md">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">AI evaluation</span>
            <DashboardHelp text="Model's classification of the case's impact level and its confidence." />
          </div>

          <span className={`block text-xl font-semibold ${isHighImpact ? 'text-foreground' : 'text-muted-foreground'}`}>
            {displayPrediction}
          </span>

          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground">Confidence</span>
              <span className="text-sm font-semibold text-foreground">{confidencePercentage.toFixed(0)}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                style={{ width: `${confidencePercentage}%` }}
                className={`h-full rounded-full transition-all duration-500 ${isHighImpact ? 'bg-primary' : 'bg-secondary-foreground/30'}`}
              />
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-background/80 p-5 shadow-sm transition-shadow hover:bg-background hover:shadow-md">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Human rating</span>
            <DashboardHelp text="Human assessment of the case's impact level based on a 4-point scale, where 4 is highest impact." />
          </div>

          {humanImpactLevel ? (
            <>
              <span className={`block text-xl font-semibold ${humanImpactLevel === "High Impact" ? 'text-foreground' : 'text-muted-foreground'}`}>
                {humanImpactLevel}
              </span>
              <span className="mt-3 text-sm font-semibold text-muted-foreground">
                {data.ground_truth?.toFixed(1)} / 4.0 Stars
              </span>
            </>
          ) : (
            <span className="mt-3 text-sm italic text-muted-foreground">No human rating available for new cases</span>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-background/80 p-5 shadow-sm transition-shadow hover:bg-background hover:shadow-md">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Main summary</span>
            <DashboardHelp text="AI-generated limitation and improvement suggestions for the case based on model analysis." />
          </div>

          <button
            type="button"
            onClick={openRefGuidelines}
            className="inline-flex cursor-pointer items-center rounded-md border border-border bg-background px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            ref guidelines
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-md border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
            <span className="mb-2 block text-xs font-bold uppercase tracking-wide text-foreground">Limitations</span>
            AI-generated limitations will appear here in a future update.
          </div>

          <div className="rounded-md border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
            <span className="mb-2 block text-xs font-bold uppercase tracking-wide text-foreground">Improvements</span>
            AI-generated improvement suggestions will appear here in a future update.
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <DashboardPanelFrame title="Overview" helpText="High-level case assessment, human rating comparison, and AI-generated improvement suggestions." expandedChildren={panelContent}>
      {panelContent}
    </DashboardPanelFrame>
  );
}
