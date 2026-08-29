export const INSIGHT_CATEGORIES = [
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

export function getObservedRange(rows, key) {
  const values = rows
    .map((row) => Number(row[key]))
    .filter((value) => Number.isFinite(value));

  if (!values.length) {
    return 'N/A';
  }

  return `${Math.min(...values).toFixed(4)} - ${Math.max(...values).toFixed(4)}`;
}
