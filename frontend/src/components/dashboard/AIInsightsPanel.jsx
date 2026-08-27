import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';
import useLLMInference from '@/hooks/useLLMInference';

const INSIGHT_CATEGORIES = [
  {
    key: 'significance_limitations',
    title: 'Significance Limitations',
    description: 'Risks that could weaken the interpretation or defensibility of the claimed impact.',
  },
  {
    key: 'significance_improvements',
    title: 'Significance Improvements',
    description: 'Changes that would make the impact claim more compelling and decision-ready.',
  },
  {
    key: 'outreach_limitations',
    title: 'Outreach Limitations',
    description: 'Gaps that make the breadth, uptake, or beneficiary coverage harder to assess.',
  },
  {
    key: 'outreach_improvements',
    title: 'Outreach Improvements',
    description: 'Changes that would make reach and audience adoption easier to evaluate.',
  },
];

function SectionTooltip({ text }) {
  return <DashboardHelp text={text} />;
}

function StatusBanner({ status, errorMessage }) {
  const isRunning = status === 'loading' || status === 'running';
  const isError = status === 'error';
  const isNotFound = status === 'not_found';

  return (
    <div
      className={`flex items-start gap-3 rounded-md border px-4 py-3 text-sm ${
        isError
          ? 'border-destructive/30 bg-destructive/5 text-destructive'
          : 'border-border bg-muted/35 text-muted-foreground'
      }`}
    >
      {isRunning ? <Loader2 className="mt-0.5 h-4 w-4 animate-spin" /> : null}
      {isError || isNotFound ? <AlertCircle className="mt-0.5 h-4 w-4" /> : null}
      <div className="space-y-1">
        <p className="font-semibold text-foreground">
          {isRunning && 'Generating AI insights'}
          {isNotFound && 'No AI insight generated for this case'}
          {isError && 'AI insight generation failed'}
        </p>
        <p className="leading-relaxed">
          {isRunning && 'The panel is polling the LLM inference endpoint for the generated review responses.'}
          {isNotFound && 'This inference does not have an associated LLM insight result.'}
          {isError && (errorMessage || 'The LLM service returned an error while generating the review.')}
        </p>
      </div>
    </div>
  );
}

function InsightCard({ title, description, items }) {
  const responses = Array.isArray(items) ? items.filter(Boolean) : [];

  return (
    <article className="flex min-h-48 flex-col rounded-md border border-border bg-background p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
        </div>
        <CheckCircle2 className="h-4 w-4 shrink-0 text-muted-foreground" />
      </div>

      {responses.length > 0 ? (
        <ul className="space-y-3 text-sm leading-relaxed text-foreground">
          {responses.map((response, index) => (
            <li key={`${title}-${index}`} className="border-l-2 border-accent/70 pl-3">
              {response}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm leading-relaxed text-muted-foreground">No generated response was returned for this category.</p>
      )}
    </article>
  );
}

export default function AIInsightsPanel({ data, llmState: providedLlmState }) {
  const inferenceId = data?.inference_id;
  const internalLlmState = useLLMInference(providedLlmState ? null : inferenceId);
  const llmState = providedLlmState || internalLlmState;

  if (!data) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-xl font-semibold text-foreground">AI Insights</h2>
        <p className="mt-2 text-sm text-muted-foreground">No case loaded.</p>
      </section>
    );
  }

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

  const llmResult = llmState.inferenceId === inferenceId ? llmState.result : null;
  const status = inferenceId
    ? llmState.inferenceId === inferenceId ? llmState.status : 'loading'
    : 'idle';
  const errorMessage = llmState.inferenceId === inferenceId ? llmState.errorMessage : '';
  const isCompleted = status === 'completed';
  const panelContent = (
    <div className="space-y-8">
      {!isCompleted ? (
        <StatusBanner status={status} errorMessage={errorMessage} />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {INSIGHT_CATEGORIES.map((category) => (
            <InsightCard
              key={category.key}
              title={category.title}
              description={category.description}
              items={llmResult?.[category.key]}
            />
          ))}
        </div>
      )}
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
