import { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { decodeHTML } from '@/helper/utils';
import { METRIC_DEFINITIONS, getDefaultDefinition } from '@/helper/metric_definitions';
import { DashboardPanelFrame, DashboardHelp } from '@/components/dashboard/DashboardPanelFrame';

const CATEGORIES = [
  { id: 'ORG', aliases: ['orgs', 'ORG'], featureAliases: ['ORG', 'Number of organizations mentioned'], label: 'Mentioned Organizations (ORG)' },
  { id: 'GPE_LOC', aliases: ['GPE', 'LOC'], featureAliases: ['Number of countries or regions mentioned', 'GPE', 'LOC'], label: 'Countries / Regions (GPE + LOC)' },
  { id: 'PERSON', aliases: ['people', 'PERSON'], featureAliases: ['PERSON', 'Number of named individuals'], label: 'Mentioned Individuals (PERSON)' },
];

function findFeatureKey(features, featureName) {
  return Object.keys(features).find(
    (key) => key.toLowerCase().replace(/_/g, ' ') === featureName.toLowerCase().replace(/_/g, ' ')
  );
}

function getCategoryItems(entities, category) {
  const rawItems = category.aliases.flatMap((alias) => entities?.[alias] || []);

  return Array.from(new Set(rawItems.map((item) => decodeHTML(String(item)).trim()))).filter(Boolean);
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

function EntitiesContent({ data, activeCategory, setActiveCategory }) {
  const features = useMemo(() => data?.features || {}, [data?.features]);
  const attributions = useMemo(() => data?.feature_attributions || {}, [data?.feature_attributions]);
  const globalImportance = useMemo(() => data?.global_importance || {}, [data?.global_importance]);
  const entities = useMemo(() => data?.entities || {}, [data?.entities]);

  const categoryRows = useMemo(() => {
    return CATEGORIES.map((category) => {
      const items = getCategoryItems(entities, category);
      const featureKey = category.featureAliases.map((alias) => findFeatureKey(features, alias)).find(Boolean);
      const definition = METRIC_DEFINITIONS[category.id]
        || METRIC_DEFINITIONS[featureKey]
        || getDefaultDefinition(category.label);
      const localRaw = category.featureAliases.reduce((value, alias) => (
        value ?? attributions[alias] ?? attributions[`${alias}_AbsAttribution`]
      ), undefined) ?? 0;
      const globalRaw = category.featureAliases.reduce((value, alias) => (
        value ?? globalImportance[alias]
      ), undefined) || 0;

      return {
        ...category,
        items,
        count: items.length,
        description: definition.description,
        localRaw,
        globalRaw,
        // range: definition.range || 'N/A',
        // bestRange: definition.bestRange || 'N/A',
        interpretation: definition.getExplanation ? definition.getExplanation(Number(featureKey ? features[featureKey] : items.length)) : 'Entity evidence used by the model.',
      };
    });
  }, [attributions, entities, features, globalImportance]);

  const activeRow = categoryRows.find((row) => row.id === activeCategory) || null;
  const localWeightRange = getObservedRange(categoryRows, 'localRaw');
  const globalWeightRange = getObservedRange(categoryRows, 'globalRaw');

  return (
    <div className="space-y-5">
      {/* <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">

        The table below summarises the entities extracted from the document using Named Entity Recognition (NER) grouped into relevant categories. The counts indicate how many unique entities were detected in each category, providing a quick overview of key individuals, organisations and economic impacts.
      </p> */}

      <div className="overflow-x-auto rounded-lg border border-border bg-background/80 shadow-sm">
        <table className="w-full min-w-[72rem] border-collapse text-left">
          <thead>
            <tr className="border-b border-border bg-muted/30 text-xs font-bold uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3">NER Category</th>
              <th className="px-4 py-3">Unique Counts</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Interpretation</th>
              {/* <th className="px-4 py-3">Range</th> */}
              {/* <th className="px-4 py-3">Best Range</th> */}
              <th className="px-4 py-3">Local Weight</th>
              <th className="px-4 py-3">Global Weight</th>
              <th className="px-4 py-3">Display List</th>
            </tr>
          </thead>
          <tbody>
            {categoryRows.map((row) => {
              const isActive = activeCategory === row.id;

              return (
                <tr key={row.id} className="border-b border-border last:border-b-0 hover:relative hover:z-10">
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">{row.label}</span>
                      <DashboardHelp text={`${row.description}`} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Observed local range: {localWeightRange}</p>
                    <p className="mt-1 text-xs text-muted-foreground">Observed global range: {globalWeightRange}</p>
                  </td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.count}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.description}</td>
                  <td className="px-4 py-4 text-sm text-muted-foreground">{row.interpretation}</td>
                  {/* <td className="px-4 py-4 text-sm text-muted-foreground">{row.range}</td> */}
                  {/* <td className="px-4 py-4 text-sm text-muted-foreground">{row.bestRange}</td> */}
                  <td className="px-4 py-4 text-sm font-semibold text-foreground tabular-nums">{row.localRaw.toFixed(4)}</td>
                  <td className="px-4 py-4 text-sm font-semibold text-foreground tabular-nums">{row.globalRaw.toFixed(4)}</td>
                  <td className="px-4 py-4">
                    <button
                      type="button"
                      onClick={() => setActiveCategory(isActive ? null : row.id)}
                      className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-accent"
                    >
                      {isActive ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      {isActive ? 'Hide list' : 'Show list'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="rounded-lg border border-border bg-background/80 p-5 shadow-sm">
        {activeRow ? (
          <>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  {activeRow.label}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Showing {activeRow.count} unique entities for this category.
                </p>
              </div>
              <span className="rounded-full border border-border bg-muted/40 px-3 py-1 text-xs font-semibold text-muted-foreground">
                {activeRow.count} items
              </span>
            </div>

            {activeRow.items.length > 0 ? (
              <ul className="grid gap-2 md:grid-cols-2">
                {activeRow.items.map((item, index) => (
                  <li key={`${activeRow.id}-${index}`} className="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm text-foreground">
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm italic text-muted-foreground">No evidence detected for this category.</p>
            )}
          </>
        ) : (
          <p className="text-sm text-muted-foreground">
            Select a category from the table above to reveal its entity list.
          </p>
        )}
      </div>
    </div>
  );
}

export default function EntitiesPanel({ data }) {
  const [activeCategory, setActiveCategory] = useState('ORG');

  return (
    <DashboardPanelFrame
      title="Entities"
      helpText="Entities extracted from the document using Named Entity Recognition grouped into relevant categories with unique counts and expandable lists."
      expandedChildren={<EntitiesContent data={data} activeCategory={activeCategory} setActiveCategory={setActiveCategory} />}
    >
      <EntitiesContent data={data} activeCategory={activeCategory} setActiveCategory={setActiveCategory} />
    </DashboardPanelFrame>
  );
}
