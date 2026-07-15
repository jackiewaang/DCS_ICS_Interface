export default function CaseHeader({ data }) {
  if (!data) return null;

  const getSourceLabel = () => {
    if (data.ref_year) return `REF ${data.ref_year} Archive`;
    return "User Inference";
  };

  const formatInferenceTime = () => {
    const milliseconds = Number(data.inference_time_ms);
    if (!Number.isFinite(milliseconds) || milliseconds <= 0) {
      return null;
    }

    if (milliseconds < 1000) {
      return `${Math.round(milliseconds)} ms`;
    }

    return `${(milliseconds / 1000).toFixed(2)} s`;
  };

  const inferenceTime = formatInferenceTime();

  return (
    <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-sm">
      <div className="px-6 py-6 max-w-7xl mx-auto">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.18em]">
          {getSourceLabel()} • Doc #{data.document_id}
        </span>
        <h1 className="text-2xl md:text-[2rem] font-semibold text-slate-900 mt-2 leading-tight">
          {data.title || "Untitled Analysis"}
        </h1>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3">
          <span className="text-sm text-slate-600">{data.institution}</span>
          <span className="inline-block h-1 w-1 rounded-full bg-slate-300" />
          <span className="text-sm font-medium text-slate-700">{data.uoa}</span>
          {data.model_name && (
            <>
              <span className="inline-block h-1 w-1 rounded-full bg-slate-300" />
              <span className="text-sm font-medium text-slate-700">Model: {data.model_name}</span>
            </>
          )}
          {inferenceTime && (
            <>
              <span className="inline-block h-1 w-1 rounded-full bg-slate-300" />
              <span className="text-sm font-medium text-slate-700">Inference time: {inferenceTime}</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
