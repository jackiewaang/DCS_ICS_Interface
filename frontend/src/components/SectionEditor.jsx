import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, FileText, Loader2, Play, Upload, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

function countWords(text) {
  return String(text || '').trim().split(/\s+/).filter(Boolean).length;
}

export default function SectionEditor({
  file,
  fileInputRef,
  draft,
  sections,
  collapsedSections,
  isCollapsed,
  onToggle,
  onFileChange,
  onChooseFile,
  onRemoveFile,
  onExtract,
  onRunInference,
  onTitleChange,
  onSectionChange,
  onToggleSection,
  isUploading,
  isRunningInference,
  canRunInference,
  error,
  inferenceError,
  hasDraft,
}) {
  return (
    <section className={`h-full rounded-lg border border-slate-200 bg-white shadow-sm transition-all ${isCollapsed ? 'w-16' : 'w-full'}`}>
      <div className={`flex h-full flex-col ${isCollapsed ? 'items-center p-3' : 'p-5'}`}>
        <button
          type="button"
          onClick={onToggle}
          aria-label={isCollapsed ? 'Expand editor' : 'Collapse editor'}
          className="cursor-pointer mb-4 inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 shadow-sm hover:bg-slate-50"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>

        {isCollapsed ? (
          <div className="flex flex-1 items-center">
            <span className="rotate-180 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500 [writing-mode:vertical-rl]">
              Editor
            </span>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="border-b border-slate-200 pb-4">
              <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                PDF upload
              </span>
              <div className="mt-3 flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-slate-50">
                  <FileText className="h-5 w-5 text-slate-600" />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-900">
                    {file ? file.name : 'No PDF selected'}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {file ? `${(file.size / 1024).toFixed(0)} KB ready for extraction` : 'Choose a REF case PDF to begin.'}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept="application/pdf,.pdf"
                  onChange={onFileChange}
                />
                <Button type="button" variant="outline" onClick={onChooseFile} className=" cursor-pointer h-10 gap-2">
                  <Upload className="h-4 w-4" />
                  Choose PDF
                </Button>
                {file && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onRemoveFile}
                    className="cursor-pointer h-10 gap-2 text-slate-500 hover:text-rose-600"
                  >
                    <X className="h-4 w-4" />
                    Clear
                  </Button>
                )}
                <Button
                  type="button"
                  onClick={onExtract}
                  disabled={!file || isUploading}
                  className="cursor-pointer h-10 gap-2 bg-slate-950 text-white hover:bg-slate-800"
                >
                  {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  Extract Sections
                </Button>
              </div>

              {error && (
                <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3">
                  <p className="text-sm font-medium text-rose-700">{error}</p>
                </div>
              )}
            </div>

            <div className="border-b border-slate-200 pb-4">
              <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div className="w-full">
                  <label htmlFor="inference-name" className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">
                    Inference name
                  </label>
                  <input
                    id="inference-name"
                    value={draft.title}
                    onChange={(event) => onTitleChange(event.target.value)}
                    placeholder="Uploaded PDF name will appear here."
                    className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-900 outline-none transition-colors focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
                  />
                </div>

                <Button
                  type="button"
                  onClick={onRunInference}
                  disabled={!canRunInference}
                  className="cursor-pointer h-10 shrink-0 gap-2 bg-slate-950 text-white hover:bg-slate-800 disabled:bg-slate-300"
                >
                  {isRunningInference ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run Inference
                </Button>
              </div>

              {inferenceError && (
                <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3">
                  <p className="text-sm font-medium text-rose-700">{inferenceError}</p>
                </div>
              )}
            </div>

            <div>
              <p className="mb-3 text-right text-xs text-slate-400">
                REF 2029 maximum: 2,200 words overall
              </p>
              <div className="grid gap-4">
                {sections.map((section) => (
                  <div key={section.id} className="rounded-md border border-slate-200 bg-slate-50/60">
                    <div className="flex flex-wrap items-center justify-between gap-3 p-4">
                      <div>
                        <label htmlFor={`section-${section.id}`} className="text-sm font-semibold text-slate-900">
                          {section.label}
                        </label>
                        <p className="mt-1 text-xs text-slate-500">{section.description}</p>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-xs font-medium text-slate-400">
                          {countWords(draft.sections[section.id]).toLocaleString()} words · Suggested ~{section.suggestedWords.toLocaleString()}
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => onToggleSection(section.id)}
                          className="h-8 gap-2 px-2 text-slate-500 cursor-pointer"
                        >
                          {collapsedSections[section.id] ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
                          {collapsedSections[section.id] ? 'Edit' : 'Collapse'}
                        </Button>
                      </div>
                    </div>

                    {!collapsedSections[section.id] && (
                      <div className="px-4 pb-4">
                        <textarea
                          id={`section-${section.id}`}
                          value={draft.sections[section.id]}
                          onChange={(event) => onSectionChange(section.id, event.target.value)}
                          placeholder={hasDraft ? 'No text was extracted for this section.' : 'Extracted section text will appear here.'}
                          className="min-h-40 w-full resize-y rounded-md border border-slate-200 bg-white px-3 py-3 text-sm leading-6 text-slate-800 outline-none transition-colors focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
