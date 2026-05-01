export default function CaseHeader({ data }) {
  if (!data) return null;

  // 1. Identification
  const getSourceLabel = () => {
    if (data.ref_year) return `REF ${data.ref_year} Archive`;
    return "User Inference";
  };

  const confidence = data.score || 0;
  const isHighImpact = confidence >= 0.5;
  const displayPrediction = isHighImpact ? "High Impact" : "Low Impact";
  const confidencePercentage = (isHighImpact ? confidence : (1 - confidence)) * 100;

  return (
    <header className="py-10 border-b border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                {getSourceLabel()} • DOC: {data.document_id}
              </span>
              {data.uoa && (
                <span className="text-[10px] font-semibold text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
                   UoA: {data.uoa}
                </span>
              )}
            </div>
            
            <h1 className="text-3xl font-semibold text-slate-900 leading-tight">
              {data.title}
            </h1>
            <p className="text-sm text-slate-500 mt-2">{data.institution}</p>
          </div>

          <div className="flex items-center gap-10 shrink-0 border-l border-slate-100 pl-10">
            
            {/* AI Prediction Area */}
            <div className="flex flex-col min-w-[140px]">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                AI Evaluation
              </span>
              <div className="flex flex-col gap-1">
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-bold ${isHighImpact ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {displayPrediction}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded uppercase">
                    {confidencePercentage.toFixed(0)}%
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 italic">
                  Engine: {data.model_name || "Unknown"}
                </span>
              </div>
            </div>

            {/* Ground Truth Area */}
            <div className="flex flex-col min-w-[140px]">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                Ground Truth
              </span>
              {data.ref_year ? (
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-bold ${data.gpa >= 3 ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {data.gpa >= 3 ? "High Impact" : "Low Impact"}
                  </span>
                  <span className="text-xs font-bold text-slate-400 italic">
                    ({data.gpa.toFixed(2)} GPA)
                  </span>
                </div>
              ) : (
                <div className="flex items-center h-[32px]">
                  <span className="text-sm font-medium text-slate-300 italic">Not Available</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}