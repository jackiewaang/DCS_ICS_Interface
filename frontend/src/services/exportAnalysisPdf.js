import { jsPDF } from 'jspdf';
import { autoTable } from 'jspdf-autotable';

const MARGIN = 14;
const SECTION_GAP = 7;

const LLM_SECTIONS = [
  ['significance_limitations', 'Significance Limitations'],
  ['significance_improvements', 'Significance Improvements'],
  ['outreach_limitations', 'Outreach Limitations'],
  ['outreach_improvements', 'Outreach Improvements'],
];

function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return 'Not available';
  }
  if (Array.isArray(value)) {
    return value.map(formatValue).join(', ');
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(6)));
  }
  return String(value);
}

function addPageIfNeeded(doc, y, requiredHeight = 12) {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (y + requiredHeight <= pageHeight - MARGIN) {
    return y;
  }
  doc.addPage();
  return MARGIN;
}

function addHeading(doc, title, y) {
  const nextY = addPageIfNeeded(doc, y, 14);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(30, 41, 59);
  doc.text(title, MARGIN, nextY);
  return nextY + 6;
}

function addText(doc, text, y) {
  const pageWidth = doc.internal.pageSize.getWidth();
  const lines = doc.splitTextToSize(formatValue(text), pageWidth - MARGIN * 2);
  let nextY = y;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(51, 65, 85);

  lines.forEach((line) => {
    nextY = addPageIfNeeded(doc, nextY, 5);
    doc.text(line, MARGIN, nextY);
    nextY += 4.5;
  });

  return nextY + SECTION_GAP;
}

function addTable(doc, y, head, body, columnStyles = {}) {
  const startY = addPageIfNeeded(doc, y, 16);
  autoTable(doc, {
    startY,
    head: [head],
    body,
    margin: { left: MARGIN, right: MARGIN },
    theme: 'grid',
    styles: {
      cellPadding: 2,
      font: 'helvetica',
      fontSize: 8,
      overflow: 'linebreak',
      textColor: [51, 65, 85],
      valign: 'top',
    },
    headStyles: {
      fillColor: [51, 65, 85],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252],
    },
    columnStyles,
  });

  return (doc.lastAutoTable?.finalY || startY) + SECTION_GAP;
}

function getAttentionRows(data) {
  if (Array.isArray(data.heatmap) && data.heatmap.length > 0) {
    return data.heatmap.map((item, index) => [
      index + 1,
      formatValue(item.sentence_text ?? item.sentence),
      formatValue(item.attention_score ?? item.attention),
    ]);
  }

  const sentences = Array.isArray(data.sentences) ? data.sentences : [];
  const attention = Array.isArray(data.attention) ? data.attention : [];
  return sentences.map((sentence, index) => [
    index + 1,
    formatValue(sentence),
    formatValue(attention[index]),
  ]);
}

function getFeatureRows(data) {
  const features = data.features || {};
  const localWeights = data.feature_attributions || {};
  const globalWeights = data.global_importance || {};
  const featureNames = new Set([
    ...Object.keys(features),
    ...Object.keys(localWeights),
    ...Object.keys(globalWeights),
    ...(data.feature_names || []),
  ]);

  return [...featureNames].map((name) => {
    const featureIndex = (data.feature_names || []).indexOf(name);
    const orderedValue = featureIndex >= 0 ? data.ordered_features?.[featureIndex] : undefined;
    const localWeight = localWeights[name] ?? (featureIndex >= 0 ? data.feature_gates?.[featureIndex] : undefined);

    return [
      name,
      formatValue(features[name] ?? orderedValue),
      formatValue(localWeight),
      formatValue(globalWeights[name]),
    ];
  });
}

function getEntityRows(data) {
  return Object.entries(data.entities || {}).map(([category, values]) => [
    category,
    Array.isArray(values) ? values.length : 'Not available',
    formatValue(values),
  ]);
}

function addLlmInsights(doc, llmState, y) {
  let nextY = addHeading(doc, 'LLM-Generated Insights', y);
  const status = llmState?.status || 'idle';
  nextY = addText(doc, `Status: ${status}${llmState?.errorMessage ? ` - ${llmState.errorMessage}` : ''}`, nextY);

  if (status !== 'completed' || !llmState.result) {
    return addText(doc, 'Generated insights were not available when this report was exported.', nextY);
  }

  LLM_SECTIONS.forEach(([key, title]) => {
    nextY = addHeading(doc, title, nextY);
    const items = Array.isArray(llmState.result[key]) ? llmState.result[key] : [];
    const body = items.length > 0
      ? items.map((item, index) => [index + 1, formatValue(item)])
      : [['-', 'No generated response was returned.']];
    nextY = addTable(doc, nextY, ['#', 'Insight'], body, {
      0: { cellWidth: 10 },
    });
  });

  return nextY;
}

function addPageNumbers(doc) {
  const pageCount = doc.getNumberOfPages();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139);
    doc.text(`Page ${page} of ${pageCount}`, pageWidth - MARGIN, pageHeight - 7, { align: 'right' });
  }
}

function reportFilename(title) {
  const safeTitle = String(title || 'untitled-analysis')
    .normalize('NFKD')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase();
  return `${safeTitle || 'untitled-analysis'}-analysis.pdf`;
}

export function exportAnalysisPdf(data, llmState) {
  if (!data) {
    return;
  }

  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  let y = MARGIN;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(15, 23, 42);
  doc.text('REF Impact Case Analysis', MARGIN, y);
  y += 8;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(71, 85, 105);
  const titleLines = doc.splitTextToSize(
    formatValue(data.title || 'Untitled Analysis'),
    doc.internal.pageSize.getWidth() - MARGIN * 2
  );
  doc.text(titleLines, MARGIN, y);
  y += titleLines.length * 4.5;
  doc.setFontSize(8);
  doc.text(`Exported ${new Date().toLocaleString()}`, MARGIN, y);
  y += SECTION_GAP;

  y = addHeading(doc, 'Case and Model Information', y);
  y = addTable(doc, y, ['Field', 'Value'], [
    ['Title', formatValue(data.title)],
    ['Institution', formatValue(data.institution)],
    ['Unit of Assessment', formatValue(data.uoa)],
    ['Status', formatValue(data.status)],
    ['REF Year', formatValue(data.ref_year)],
    ['Document ID', formatValue(data.document_id)],
    ['Inference ID', formatValue(data.inference_id)],
    ['Created At', formatValue(data.created_at)],
    ['Model', formatValue(data.model_name)],
    ['Model Configuration ID', formatValue(data.config_id)],
    ['Input Granularity', formatValue(data.input_granularity)],
    ['Inference Time (ms)', formatValue(data.inference_time_ms)],
  ], {
    0: { cellWidth: 48 },
  });

  y = addHeading(doc, 'AttentionMIL Result', y);
  y = addTable(doc, y, ['Metric', 'Value'], [
    ['Prediction Label', formatValue(data.prediction_label || data.label)],
    ['Prediction Score', formatValue(data.model_prediction ?? data.score)],
    ['Ground Truth', formatValue(data.ground_truth ?? data.true_label)],
    ['GPA', formatValue(data.gpa)],
    ['Narrative Contribution', formatValue(data.narrative_contribution)],
    ['Feature Contribution', formatValue(data.feature_contribution)],
  ], {
    0: { cellWidth: 55 },
  });

  const submittedSections = [
    ['Summary of Impact', data.sections?.summary],
    ['Underpinning Research', data.sections?.research],
    ['Details of Impact', data.sections?.impact],
  ];
  submittedSections.forEach(([title, content]) => {
    y = addHeading(doc, title, y);
    y = addText(doc, content, y);
  });

  y = addHeading(doc, 'Attention Heatmap', y);
  const attentionRows = getAttentionRows(data);
  y = addTable(
    doc,
    y,
    ['#', 'Sentence', 'Attention Weight'],
    attentionRows.length > 0 ? attentionRows : [['-', 'No sentence-level attention data.', '-']],
    {
      0: { cellWidth: 10 },
      2: { cellWidth: 32 },
    }
  );

  y = addHeading(doc, 'Extracted Features and Weights', y);
  const featureRows = getFeatureRows(data);
  y = addTable(
    doc,
    y,
    ['Feature', 'Value', 'Local Weight', 'Global Weight'],
    featureRows.length > 0 ? featureRows : [['No features available.', '-', '-', '-']],
    {
      0: { cellWidth: 52 },
      2: { cellWidth: 30 },
      3: { cellWidth: 30 },
    }
  );

  y = addHeading(doc, 'Extracted Entities', y);
  const entityRows = getEntityRows(data);
  y = addTable(
    doc,
    y,
    ['Category', 'Count', 'Entities'],
    entityRows.length > 0 ? entityRows : [['No entities available.', '-', '-']],
    {
      0: { cellWidth: 38 },
      1: { cellWidth: 18 },
    }
  );

  addLlmInsights(doc, llmState, y);
  addPageNumbers(doc);
  doc.save(reportFilename(data.title));
}
