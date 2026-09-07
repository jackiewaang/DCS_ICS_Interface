import { jsPDF } from 'jspdf';

const MARGIN = 14;

function safeFilename(title) {
  const safeTitle = String(title || 'untitled-gemma-assessment')
    .normalize('NFKD')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase();
  return `${safeTitle || 'untitled-gemma-assessment'}-gemma.pdf`;
}

export function exportGemmaPdf(data) {
  if (!data) return;

  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const textWidth = pageWidth - MARGIN * 2;
  let y = MARGIN;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.text('Gemma REF Assessment', MARGIN, y);
  y += 10;

  doc.setFontSize(12);
  doc.text(doc.splitTextToSize(data.title || 'Untitled inference', textWidth), MARGIN, y);
  y += 12;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.text(`Model: ${data.model_name || 'Gemma'}`, MARGIN, y);
  y += 6;
  doc.text(`Predicted REF GPA: ${Number(data.score).toFixed(2)} / 4.00`, MARGIN, y);
  y += 6;
  const duration = Number.isFinite(data.inference_time_ms)
    ? `${(data.inference_time_ms / 1000).toFixed(1)} seconds`
    : 'Not available';
  doc.text(`Inference time: ${duration}`, MARGIN, y);
  y += 10;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text('Diagnostic comments', MARGIN, y);
  y += 7;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  const lines = doc.splitTextToSize(data.comments || 'No diagnostic comments returned.', textWidth);
  lines.forEach((line) => {
    if (y > pageHeight - MARGIN) {
      doc.addPage();
      y = MARGIN;
    }
    doc.text(line, MARGIN, y);
    y += 5;
  });

  doc.save(safeFilename(data.title));
}
