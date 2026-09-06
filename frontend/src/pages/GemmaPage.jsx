import { useRef, useState } from 'react';
import { Sparkles } from 'lucide-react';

import GemmaResults from '@/components/GemmaResults';
import SectionEditor from '@/components/SectionEditor';
import { getUserErrorMessage } from '@/helper/error_messages';
import { api } from '@/services/api';


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
  sections: { summary: '', research: '', impact: '' },
};

const EXPANDED_SECTIONS = { summary: false, research: false, impact: false };
const COLLAPSED_SECTIONS = { summary: true, research: true, impact: true };

function hasSectionText(sections) {
  return Boolean(sections.summary || sections.research || sections.impact);
}

export default function GemmaPage({ onProcessingChange }) {
  const [file, setFile] = useState(null);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [inferenceError, setInferenceError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunningInference, setIsRunningInference] = useState(false);
  const [isEditorCollapsed, setIsEditorCollapsed] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState(EXPANDED_SECTIONS);
  const fileInputRef = useRef(null);

  const clearDraft = () => {
    setFile(null);
    setDraft(EMPTY_DRAFT);
    setResult(null);
    setError(null);
    setInferenceError(null);
    setCollapsedSections(EXPANDED_SECTIONS);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    const isPdf = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf');
    if (!isPdf || selectedFile.size === 0) {
      clearDraft();
      setError(isPdf ? 'The selected PDF is empty.' : 'Only PDF files are supported.');
      return;
    }

    setFile(selectedFile);
    setDraft(EMPTY_DRAFT);
    setResult(null);
    setError(null);
    setInferenceError(null);
    setCollapsedSections(EXPANDED_SECTIONS);
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
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
      setResult(null);
    } catch (uploadError) {
      setError(getUserErrorMessage(uploadError, 'Could not extract REF sections from the uploaded PDF.'));
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunInference = async () => {
    if (isRunningInference || !hasSectionText(draft.sections)) return;

    setIsRunningInference(true);
    onProcessingChange?.(true);
    setInferenceError(null);
    setResult(null);
    try {
      const data = await api.runGemmaInference(draft.sections, draft.title);
      setResult(data);
      setCollapsedSections(COLLAPSED_SECTIONS);
    } catch (runError) {
      setInferenceError(getUserErrorMessage(runError, 'Could not run the Gemma assessment.'));
    } finally {
      setIsRunningInference(false);
      onProcessingChange?.(false);
    }
  };

  const updateSection = (sectionId, value) => {
    setDraft((current) => ({
      ...current,
      sections: { ...current.sections, [sectionId]: value },
    }));
  };

  const hasDraft = Boolean(draft.title || hasSectionText(draft.sections));

  return (
    <div className="flex min-h-full w-full flex-col gap-6 p-6 md:p-8">
      <header className="shrink-0 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem]">
              Fine-tuned Gemma Assessment
            </h1>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              Predict a continuous REF GPA and generate concise diagnostic comments.
            </p>
          </div>
        </div>
      </header>

      <div className={`grid min-h-0 flex-1 items-stretch gap-5 ${isEditorCollapsed ? 'grid-cols-[4rem_minmax(0,1fr)]' : 'grid-cols-1 xl:grid-cols-[minmax(28rem,0.9fr)_minmax(0,1.1fr)]'}`}>
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
          onRemoveFile={clearDraft}
          onExtract={handleUpload}
          onRunInference={handleRunInference}
          onTitleChange={(value) => setDraft((current) => ({ ...current, title: value }))}
          onSectionChange={updateSection}
          onToggleSection={(sectionId) => setCollapsedSections((current) => ({
            ...current,
            [sectionId]: !current[sectionId],
          }))}
          isUploading={isUploading}
          isRunningInference={isRunningInference}
          canRunInference={hasSectionText(draft.sections) && !isRunningInference}
          error={error}
          inferenceError={inferenceError}
          hasDraft={hasDraft}
        />

        <GemmaResults data={result} />
      </div>
    </div>
  );
}
