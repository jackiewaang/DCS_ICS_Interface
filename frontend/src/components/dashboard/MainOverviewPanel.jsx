import { ENTITY_METRIC_KEYS } from '@/helper/metric_definitions';
import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

const FEATURE_BLACKLIST = new Set([
  'Number of organizations mentioned',
  'Number of named individuals',
  'Number of countries or regions mentioned',
  'TIME',
  'CARDINAL',
  'GPE',
  'DATE',
  'PERCENT',
  'LOC',
  'WORK_OF_ART',
  'LAW',
  'LANGUAGE',
  'FAC',
  'ORDINAL',
  'QUANTITY',
  'PRODUCT',
  'NORP',
  'EVENT',
]);

const ENTITY_CATEGORIES = [
  { id: 'ORG', aliases: ['orgs', 'ORG'], label: 'Organizations' },
  { id: 'MONEY', aliases: ['money', 'MONEY'], label: 'Economic impact' },
  { id: 'PERSON', aliases: ['people', 'PERSON'], label: 'Individuals' },
];

const ENTITY_METRIC_SET = new Set(ENTITY_METRIC_KEYS);

function formatSnippet(text, maxLength = 110) {
  if (!text) {
    return 'N/A';
  }

  const compact = String(text).replace(/\s+/g, ' ').trim();
  return compact.length > maxLength ? `${compact.slice(0, maxLength - 3)}...` : compact;
}

function getHeatmapHighlights(heatmap) {
  if (!Array.isArray(heatmap) || heatmap.length === 0) {
    return null;
  }

  const ordered = [...heatmap].sort((left, right) => Number(right.attention_score) - Number(left.attention_score));
  const topSentence = ordered[0];
  const worstSentence = ordered[ordered.length - 1];

  return {
    topSentence: {
      text: formatSnippet(topSentence?.sentence_text),
      score: Number(topSentence?.attention_score ?? 0).toFixed(4),
    },
    worstSentence: {
      text: formatSnippet(worstSentence?.sentence_text),
      score: Number(worstSentence?.attention_score ?? 0).toFixed(4),
    },
  };
}

function getFeatureHighlights(data) {
  const globalImportance = data?.global_importance || {};

  const rankedFeatures = Object.entries(globalImportance)
    .filter(([name]) => !FEATURE_BLACKLIST.has(name))
    .filter(([name]) => !ENTITY_METRIC_SET.has(name))
    .filter(([, value]) => Number.isFinite(Number(value)))
    .sort((left, right) => Number(right[1]) - Number(left[1]) || left[0].localeCompare(right[0]));

  if (!rankedFeatures.length) {
    return null;
  }

  const topFeature = rankedFeatures[0];
  const worstFeature = rankedFeatures[rankedFeatures.length - 1];

  return {
    topFeature: {
      name: topFeature[0],
      score: Number(topFeature[1]).toFixed(4),
    },
    worstFeature: {
      name: worstFeature[0],
      score: Number(worstFeature[1]).toFixed(4),
    },
  };
}

function getEntityHighlights(entities) {
  const categoryRows = ENTITY_CATEGORIES.map((category) => {
    const items = category.aliases.reduce((accumulator, alias) => {
      return accumulator.length > 0 ? accumulator : (entities?.[alias] || []);
    }, []);

    return {
      ...category,
      count: Array.isArray(items) ? items.length : 0,
    };
  });

  if (!categoryRows.some((row) => row.count > 0)) {
    return null;
  }

  const highest = [...categoryRows].sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))[0];
  const lowest = [...categoryRows].sort((left, right) => left.count - right.count || left.label.localeCompare(right.label))[0];

  return {
    highest: {
      label: highest.label,
      count: highest.count,
    },
    lowest: {
      label: lowest.label,
      count: lowest.count,
    },
  };
}

export default function MainOverviewPanel({ data }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-xl font-semibold text-foreground">Overview</h2>
        <p className="mt-2 text-sm text-muted-foreground">No case loaded.</p>
      </section>
    );
  }

  const predictionProbability = data.model_prediction ?? 0;
  const isHighImpact = data.prediction_label ? data.prediction_label === "High Impact" : predictionProbability >= 0.5;
  const displayPrediction = data.prediction_label || (isHighImpact ? "High Impact" : "Low Impact");
  const predictionProbabilityPercentage = predictionProbability * 100;
  const humanImpactLevel = data.ground_truth !== null && data.ground_truth !== undefined
    ? (data.ground_truth >= 3 ? "High Impact" : "Low Impact")
    : null;
  const heatmapHighlights = getHeatmapHighlights(data.heatmap);
  const featureHighlights = getFeatureHighlights(data);
  const entityHighlights = getEntityHighlights(data.entities);

  const humanRatingText = humanImpactLevel
    ? `Human rating is applicable and indicates ${humanImpactLevel}${data.ground_truth !== null && data.ground_truth !== undefined ? ` (${data.ground_truth?.toFixed(1)} / 4.0 stars)` : ''}.`
    : 'Human rating is not available for this case.';

  const summaryLeadBase = `This case is currently predicted as ${displayPrediction} with a ${predictionProbabilityPercentage.toFixed(0)}% prediction probability. ${humanRatingText}`;

  const panelContent = (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-background/80 p-5 shadow-sm transition-shadow hover:bg-background hover:shadow-md">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">AI evaluation</span>
            <DashboardHelp text="Model's classification of the case's impact level and the raw prediction probability." />
          </div>

          <span className={`block text-xl font-semibold ${isHighImpact ? 'text-foreground' : 'text-muted-foreground'}`}>
            {displayPrediction}
          </span>

          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground">Prediction probability</span>
              <span className="text-sm font-semibold text-foreground">{predictionProbabilityPercentage.toFixed(2)}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                style={{ width: `${predictionProbabilityPercentage}%` }}
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
            <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Main Summary</span>
            <DashboardHelp text="Prediction summary with cross-tab highlights from the attention heatmap, feature importance, and entity counts." />
          </div>
        </div>

        <div className="rounded-md border border-border bg-muted/30 px-4 py-4 text-sm leading-6 text-muted-foreground">
          <p>{summaryLeadBase} <br />
            
            {heatmapHighlights ? `The attention heatmap points to the sentence: "${heatmapHighlights.topSentence.text}" as the top-weighted sentence with attention weight ${heatmapHighlights.topSentence.score}, while the sentence "${heatmapHighlights.worstSentence.text}" sits at the lowest attention level with attention weight ${heatmapHighlights.worstSentence.score}.` : 'Sentence-level attention highlights are not available for this case.'} 
            <br />
            {featureHighlights ? `The feature view shows ${featureHighlights.topFeature.name} as the strongest feature at ${featureHighlights.topFeature.score}, with ${featureHighlights.worstFeature.name} as the weakest at ${featureHighlights.worstFeature.score}.` : 'Feature importance highlights are not available for this case.'} 
            <br />
            {entityHighlights ? `The entity view is led by the category ${entityHighlights.highest.label} with ${entityHighlights.highest.count} entities mentioned, while the category ${entityHighlights.lowest.label} has the fewest at ${entityHighlights.lowest.count} entities mentioned.` : 'Entity count highlights are not available for this case.'} <br />For more information, explore the other tabs.</p>
        </div>
      </div>
    </div>
  );

  return (
    <DashboardPanelFrame title="Overview" helpText="Prediction summary with attention, feature, and entity highlights across the other tabs.">
      {panelContent}
    </DashboardPanelFrame>
  );
}
