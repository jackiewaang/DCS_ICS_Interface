import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

function SectionTooltip({ text }) {
  return <DashboardHelp text={text} />;
}

function CriteriaBlock({ title, helpText, children, className = '' }) {
  return (
    <div className={className}>
      <div className="mb-2 flex items-center gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</span>
        <SectionTooltip text={helpText} />
      </div>
      {children}
    </div>
  );
}

function InsightSection({
  title,
  outreachText,
  significanceText,
  outreachTooltip,
  significanceTooltip,
}) {
  const sectionKey = title.toLowerCase();

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground">{title}</h3>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <CriteriaBlock
          title="Outreach"
          helpText={outreachTooltip}
          className="md:col-span-1 rounded-md bg-muted/40 border-l-2 border-muted-500 px-3 py-3"
        >
          <p className="text-xs sm:text-sm leading-relaxed text-foreground">{sectionKey} for outreach will appear here.</p>
          <p className="text-xs sm:text-sm leading-relaxed text-muted-foreground">{outreachText}</p>
        </CriteriaBlock>

        <CriteriaBlock
          title="Significance"
          helpText={significanceTooltip}
          className="md:col-span-2 rounded-md bg-muted/40 border-l-2 border-muted-500 px-3 py-3"
        >
          <p className="text-xs sm:text-sm leading-relaxed text-foreground">{sectionKey} for significance will appear here.</p>
          <p className="text-xs sm:text-sm leading-relaxed text-muted-foreground">{significanceText}</p>
        </CriteriaBlock>
      </div>

    </section>
  );
}

export default function AIInsightsPanel({ data }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-xl font-semibold text-foreground">AI Insights</h2>
        <p className="mt-2 text-sm text-muted-foreground">No case loaded.</p>
      </section>
    );
  }

  const limitationsOutreach = 'Reach is moderate because the limitation is primarily visible when the model has to generalize across uneven evidence coverage or scattered passages.';
  const limitationsSignificance = 'The limitation matters because it can affect how confidently the case should be interpreted and whether the prediction is stable enough for downstream use.';
  const improvementsOutreach = 'Reach is broader when the guidance is translated into a clearer evidence summary that can be reviewed quickly by users across the workflow.';
  const improvementsSignificance = 'The improvement is significant because it strengthens the final judgment and makes the recommendation more defensible.';

  const refGuidanceUrl = 'https://2029.ref.ac.uk/guidance/section-6-engagement-and-impact-guidance/';

  const headerActions = (
    <a
      href={refGuidanceUrl}
      target="_blank"
      rel="noreferrer noopener"
      className="inline-flex h-9 items-center rounded-md border border-border bg-background px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
    >
      ref2029 guide
    </a>
  );

  const panelContent = (
    <div className="space-y-8">
      <InsightSection
        title="Limitations"
        // outreachText={limitationsOutreach}
        // significanceText={limitationsSignificance}
        outreachTooltip="Outreach describes how far the limitation reaches across audiences, workflows, and use cases."
        significanceTooltip="Significance explains how strongly the limitation could affect interpretation and downstream decisions."
      />
      <InsightSection
        title="Improvements"
        // outreachText={improvementsOutreach}
        // significanceText={improvementsSignificance}
        outreachTooltip="Outreach describes how broadly the improvement would help readers, reviewers, and downstream decision-makers."
        significanceTooltip="Significance explains how much the improvement would strengthen review quality and decision confidence."
      />
    </div>
  );

  return (
    <DashboardPanelFrame
      title="Limitations and Improvements"
      helpText="AI-generated limitation and improvement feedbacks based on REF guidance."
      headerActions={headerActions}
      expandedChildren={panelContent}
    >
      {panelContent}
    </DashboardPanelFrame>
  );
}