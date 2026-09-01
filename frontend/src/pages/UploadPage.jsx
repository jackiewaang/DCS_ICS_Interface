import { useRef, useState } from 'react';
import { FilePlus2 } from 'lucide-react';
import { api } from '@/services/api';
import InferenceResults from '@/components/InferenceResults';
import SectionEditor from '@/components/SectionEditor';
import ErrorAlert from '@/components/ui/ErrorAlert';
import { getUserErrorMessage } from '@/helper/error_messages';

const SECTION_FIELDS = [
  {
    id: 'summary',
    label: 'Summary of Impact',
    description: 'High-level overview of the impact.',
    suggestedWords: 100,
  },
  {
    id: 'research',
    label: 'Underpinning Research',
    description: 'Core research that enabled the impact.',
    suggestedWords: 600,
  },
  {
    id: 'impact',
    label: 'Details of Impact',
    description: 'Evidence of how the impact was achieved.',
    suggestedWords: 1500,
  },
];

const EMPTY_DRAFT = {
  title: '',
  sections: {
    summary: '',
    research: '',
    impact: '',
  },
};

const EXPANDED_SECTIONS = {
  summary: false,
  research: false,
  impact: false,
};

const COLLAPSED_SECTIONS = {
  summary: true,
  research: true,
  impact: true,
};

function hasSectionText(sections) {
  return Boolean(sections.summary || sections.research || sections.impact);
}

export default function UploadPage({
  activeConfigId,
  inferenceResult,
  onAnalysisComplete,
  onClearAnalysis,
  modelsError,
  onRetryModels,
  embeddingModelName,
  llmModelName,
}) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunningInference, setIsRunningInference] = useState(false);
  const [isEditorCollapsed, setIsEditorCollapsed] = useState(false);
  const [error, setError] = useState(null);
  const [inferenceError, setInferenceError] = useState(null);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [collapsedSections, setCollapsedSections] = useState(EXPANDED_SECTIONS);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    const isPdf = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setFile(null);
      setDraft(EMPTY_DRAFT);
      onClearAnalysis?.();
      setError('Only PDF files are supported.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (selectedFile.size === 0) {
      setFile(null);
      setDraft(EMPTY_DRAFT);
      onClearAnalysis?.();
      setError('The selected PDF is empty. Choose a valid case-study file.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setFile(selectedFile);
    setDraft(EMPTY_DRAFT); 
    setCollapsedSections(EXPANDED_SECTIONS);
    onClearAnalysis?.();
    setError(null);
    setInferenceError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      return;
    }

    setIsUploading(true);
    setError(null);
    setInferenceError(null);

    try {
      const data = await api.uploadCase(file);
      setDraft({
        title: data.title || file.name,
        sections: {
          summary: data.sections?.summary || '',
          research: data.sections?.research || '',
          impact: data.sections?.impact || '',
        },
      });
      setCollapsedSections(EXPANDED_SECTIONS);
      onClearAnalysis?.();
    } catch (err) {
      console.error('Upload Error:', err);
      setError(getUserErrorMessage(err, 'Could not extract REF sections from the uploaded PDF.'));
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunInference = async () => {
    if (!activeConfigId || !hasSectionText(draft.sections)) {
      return;
    }

    setIsRunningInference(true);
    setInferenceError(null);
    onClearAnalysis?.();

    try {
      const startedAt = performance.now();
      const result = await api.runInference(draft.sections, activeConfigId, {
        title: draft.title,
        sections: draft.sections,
      }, {
        embeddingModelName,
        llmModelName,
      });
      const inferenceTimeMs = Math.round(performance.now() - startedAt);
      onAnalysisComplete?.({
        ...result,
        inference_time_ms: result.inference_time_ms ?? inferenceTimeMs, // TODO: Check if backend is returning inference_time_ms, if not, use the calculated time
      });
      setCollapsedSections(COLLAPSED_SECTIONS);
    } catch (err) {
      console.error('Inference Error:', err);
      setInferenceError(getUserErrorMessage(err, 'Could not run inference for the current draft.'));
    } finally {
      setIsRunningInference(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setIsUploading(false);
    setIsRunningInference(false);
    setError(null);
    setInferenceError(null);
    setDraft(EMPTY_DRAFT);
    setCollapsedSections(EXPANDED_SECTIONS);
    onClearAnalysis?.();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const updateSection = (sectionId, value) => {
    setDraft((current) => ({
      ...current,
      sections: {
        ...current.sections,
        [sectionId]: value,
      },
    }));
  };

  const toggleSection = (sectionId) => {
    setCollapsedSections((current) => ({
      ...current,
      [sectionId]: !current[sectionId],
    }));
  };

  const hasDraft = Boolean(draft.title || hasSectionText(draft.sections));
  const canRunInference = Boolean(activeConfigId && hasSectionText(draft.sections) && !isRunningInference);

  return (
    <div className="flex min-h-full w-full flex-col gap-6 p-6 md:p-8">
      <header className="shrink-0 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <FilePlus2 className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem]">
              New Case Draft
            </h1>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              Upload a PDF, edit the extracted REF sections, then run inference with the active model.
            </p>
          </div>
        </div>
      </header>

      {modelsError ? (
        <ErrorAlert
          title="Inference models are unavailable"
          message={modelsError}
          onRetry={onRetryModels}
        />
      ) : null}

      <div className={`grid min-h-0 flex-1 items-stretch gap-5 ${isEditorCollapsed ? 'grid-cols-[4rem_minmax(0,1fr)]' : 'grid-cols-1 xl:grid-cols-[minmax(28rem,0.86fr)_minmax(0,1.14fr)]'}`}>
        <SectionEditor
          file={file}
          fileInputRef={fileInputRef}
          draft={draft}
          sections={SECTION_FIELDS}
          collapsedSections={collapsedSections}
          isCollapsed={isEditorCollapsed}
          onToggle={() => setIsEditorCollapsed((current) => !current)}
          onFileChange={handleFileChange}
          onChooseFile={() => fileInputRef.current?.click()}
          onRemoveFile={removeFile}
          onExtract={handleUpload}
          onRunInference={handleRunInference}
          onTitleChange={(value) => setDraft((current) => ({ ...current, title: value }))}
          onSectionChange={updateSection}
          onToggleSection={toggleSection}
          isUploading={isUploading}
          isRunningInference={isRunningInference}
          canRunInference={canRunInference}
          error={error}
          inferenceError={inferenceError}
          hasDraft={hasDraft}
        />

        <InferenceResults data={inferenceResult} />
      </div>
    </div>
  );
}
