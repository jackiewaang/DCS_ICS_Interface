import { useMemo, useState } from 'react';
import { ArrowDownAZ, ArrowDownWideNarrow, ChevronDown, ChevronUp } from 'lucide-react';
import { ENTITY_METRIC_KEYS, METRIC_DEFINITIONS, getDefaultDefinition } from '@/helper/metric_definitions';
import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

const BLACKLISTED = [
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
  'EVENT'
];

const ENTITY_METRIC_SET = new Set(ENTITY_METRIC_KEYS);

function toFiniteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function getValueLabel(value, format) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'N/A';
  }

  const numericValue = toFiniteNumber(value);
  if (!format) {
    return numericValue === null ? String(value) : String(numericValue);
  }

  if (numericValue === null) {
    return String(value);
  }

  return format(numericValue);
}

function getObservedRange(rows, key) {
  if (!rows.length) {
    return 'N/A';
  }

  const values = rows.map((row) => Number(row[key])).filter((value) => Number.isFinite(value));

  if (!values.length) {
    return 'N/A';
  }

  const min = Math.min(...values);
  const max = Math.max(...values);

  return `${min.toFixed(4)} - ${max.toFixed(4)}`;
}

function getFeatureRows(data, sortMode) {
  const features = data?.features || {};
  const attributions = data?.feature_attributions || {};
  const globalImportance = data?.global_importance || {};
  const featureNames = Array.from(new Set([
    ...Object.keys(globalImportance),
    ...Object.keys(features),
  ]));

  const rows = featureNames
    .filter((name) => !BLACKLISTED.includes(name))
    .filter((name) => !ENTITY_METRIC_SET.has(name))
    .map((featureName) => {
      const featureKey = Object.keys(features).find(
        (key) => key.toLowerCase().replace(/_/g, ' ') === featureName.toLowerCase().replace(/_/g, ' ')
      );

      const value = features[featureKey];
      const definition = METRIC_DEFINITIONS[featureName] || getDefaultDefinition(featureName);
      const localRaw = toFiniteNumber(attributions[featureName] ?? attributions[`${featureName}_AbsAttribution`]) ?? 0;
      const globalRaw = toFiniteNumber(globalImportance[featureName]) ?? 0;
      const numericValue = toFiniteNumber(value);

      return {
        name: featureName,
        value,
        localRaw,
        globalRaw,
        definition,
        description: definition.description || definition.category || 'Model Feature',
        interpretation: definition.getExplanation && numericValue !== null ? definition.getExplanation(numericValue) : 'A weighted feature used by the AI model.',
        bestRange: definition.bestRange || definition.range || 'N/A',
      };
    })
    .filter((item) => item.value !== undefined);

  rows.sort((left, right) => {
    const primary = sortMode === 'local' ? right.localRaw - left.localRaw : right.globalRaw - left.globalRaw;
    if (primary !== 0) {
      return primary;
    }

    return left.name.localeCompare(right.name);
  });

  return rows;
}

export default function FeaturesPanel({ data }) {
  const [sortMode, setSortMode] = useState('global');

  const panelContent = useMemo(() => {
    const features = data?.features || {};

    if (!Object.keys(features).length) {
      return (
        <div className="rounded-lg border border-border bg-muted/40 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Linguistic features are not enabled for this model. The analysis relies on semantic embeddings only.
          </p>
        </div>
      );
    }

    const rows = getFeatureRows(data, sortMode);
    const localWeightRange = getObservedRange(rows, 'localRaw');
    const globalWeightRange = getObservedRange(rows, 'globalRaw');

    return (
      <div className="space-y-5">
        <div className="rounded-lg border border-border bg-muted/20 p-3 text-xs leading-relaxed text-muted-foreground">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:divide-x sm:divide-border/60">
          
          {/* Local Weight Definition */}
          <div className="space-y-1">
            <span className="font-bold text-foreground block uppercase tracking-wider text-xs">
              Feature Local Weight
            </span>
            <p className="text-muted-foreground/90">
            Case-specific feature attribution weight for the model's prediction on this document. 
            </p>
            <span className="font-mono text-xs text-muted-foreground/70 block mt-1">
              Observed Range: {localWeightRange}
            </span>
          </div>

          {/* Global Weight Definition */}
          <div className="space-y-1 sm:pl-4">
            <span className="font-bold text-foreground block uppercase tracking-wider text-xs">
              Feature Global Weight
            </span>
            <p className="text-muted-foreground/90">
              Macro-level feature attribution weight across the entire training dataset.
            </p>
            <span className="font-mono text-xs text-muted-foreground/70 block mt-1">
              Observed Range: {globalWeightRange}
            </span>
          </div>

        </div>
      </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-muted-foreground">
            Sorted by <span className="font-semibold text-foreground">{sortMode === 'local' ? 'local weight' : 'global weight'}</span>.
          </div>

          <button
            type="button"
            onClick={() => setSortMode((current) => (current === 'global' ? 'local' : 'global'))}
            className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-accent"
          >
            {sortMode === 'global' ? <ArrowDownWideNarrow className="h-4 w-4" /> : <ArrowDownAZ className="h-4 w-4" />}
            Sort by {sortMode === 'global' ? 'Local Weight' : 'Global Weight'}
          </button>
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-background/80 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3">Feature</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Interpretation</th>
                  <th className="px-4 py-3">Range</th>
                  <th className="px-4 py-3">Best Range</th>
                  <th className="px-4 py-3">Value</th>
                  <th className="px-4 py-3">Local Weight</th>
                  <th className="px-4 py-3">Global Weight</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  return (
                    <tr key={row.name} className="border-b border-border last:border-b-0 align-top">
                      <td className="px-4 py-4">
                        <div className="flex items-start gap-2">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-foreground">{row.name}</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-sm text-muted-foreground">{row.description}</td>
                      <td className="px-4 py-4 text-sm text-muted-foreground">{row.interpretation}</td>
                      <td className="px-4 py-4 text-sm text-muted-foreground">{row.definition.range || 'N/A'}</td>
                      <td className="px-4 py-4 text-sm text-muted-foreground">{row.bestRange}</td>
                      <td className="px-4 py-4 text-sm font-semibold text-foreground tabular-nums">{getValueLabel(row.value, row.definition.format)}</td>
                      <td className="px-4 py-4 text-sm font-semibold text-foreground tabular-nums">{row.localRaw.toFixed(4)}</td>
                      <td className="px-4 py-4 text-sm font-semibold text-foreground tabular-nums">{row.globalRaw.toFixed(4)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }, [data, sortMode]);

  return (
    <DashboardPanelFrame
      title="Features"
      helpText="Features extracted from the document and their importance weights for the model's classification decision. "
      expandedChildren={panelContent}
    >
      {panelContent}
    </DashboardPanelFrame>
  );
}
