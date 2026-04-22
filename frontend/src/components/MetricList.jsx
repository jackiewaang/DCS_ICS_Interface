import React from 'react';
import { METRIC_DEFINITIONS, getDefaultDefinition } from '../helper/metric_definitions';

const MetricList = ({ data }) => {
  // 1. Data Source Pivot
  const features = data?.features || {};
  const hasFeatures = Object.keys(features).length > 0;
  console.log(features)

  const topFeatures = [
    { 
      label: "Reading Ease", 
      field: "Flesch Reading Ease", 
      aliases: ["flesch_reading_ease"], 
      importance: 0.052 
    },
    { 
      label: "SMOG Grade", 
      field: "SMOG Index", 
      aliases: ["smog_index"], 
      importance: 0.042 
    },
    { 
      label: "Complexity (ARI)", 
      field: "Automated Readability Index", 
      aliases: ["ari"], 
      importance: 0.051 
    },
    { 
      label: "Overall Tone", 
      field: "Sentiment (mean)", 
      aliases: ["sentiment_mean"], 
      importance: 0.043 
    },
    { 
      label: "Volume", 
      field: "Word count", 
      aliases: ["word_count"], 
      importance: 0.046 
    },
  ];

  // Fallback for models that don't use the 33 statistical features (like Qwen Full-Text)
  if (!hasFeatures) {
    return (
      <div className="bg-slate-100/50 border border-slate-200 rounded-lg p-6 text-center">
        <p className="text-xs text-slate-500 italic leading-relaxed">
          Linguistic GTF extraction is skipped for the active LLM architecture. 
          The model utilizes raw semantic embeddings for prediction.
        </p>
      </div>
    );
  }
return (
    <div className="flex flex-col space-y-8">
      {topFeatures.map((item, idx) => {
        // --- MULTI-KEY LOOKUP LOGIC ---
        // Look for the primary 'field' name first, then check any aliases
        let val = features[item.field];
        if (val === undefined && item.aliases) {
          for (const alias of item.aliases) {
            if (features[alias] !== undefined) {
              val = features[alias];
              break;
            }
          }
        }

        const def = METRIC_DEFINITIONS[item.field] || getDefaultDefinition(item.field);
        const explanation = def.getExplanation(val) || "";
        const [statusLabel, ...descriptionParts] = explanation.split('.');
        const description = descriptionParts.join('.').trim();

        return (
          <div key={idx} className="border-b border-slate-200 pb-6 last:border-0 pt-2 transition-all hover:bg-slate-50/50 -mx-2 px-2 rounded-lg">
            <div className="flex justify-between items-start mb-3">
              <div className="flex flex-col">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                  {def.category}
                </span>
                {def.range && (
                  <span className="text-[9px] font-mono text-slate-300">
                    Range: {def.range}
                  </span>
                )}
              </div>
              <div className="flex flex-col items-end">
                <span className="text-[9px] font-bold text-slate-300 uppercase">Weight</span>
                <span className="text-xs font-mono font-bold text-blue-600/60">
                  {item.importance.toFixed(3)}
                </span>
              </div>
            </div>

            <h4 className="text-sm font-bold text-slate-800 mb-2">
              {item.field}
            </h4>

            <div className="flex items-baseline gap-3 mb-3">
              <span className="text-3xl font-bold leading-none tabular-nums text-slate-900">
                {/* Convert to Number in case the JSON has it as a string (e.g., "0.0") */}
                {val !== undefined && val !== null ? def.format(Number(val)) : "—"}
              </span>
              {val !== undefined && val !== null && (
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter border ${getStatusStyle(statusLabel)}`}>
                  {statusLabel}
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-500 italic leading-snug">
              {description || "Metric captured within baseline operational parameters."}
            </p>
          </div>
        );
      })}
    </div>
  );
};

const getStatusStyle = (label) => {
  const l = label?.toLowerCase() || "";
  if (l.includes("high") || l.includes("good") || l.includes("positive")) 
    return "bg-emerald-50 text-emerald-700 border-emerald-100";
  if (l.includes("complex") || l.includes("low") || l.includes("negative") || l.includes("poor")) 
    return "bg-rose-50 text-rose-700 border-rose-100";
  return "bg-slate-50 text-slate-600 border-slate-200";
};

export default MetricList;