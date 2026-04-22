import { Info } from "lucide-react";

export default function AttentionHeatmap ({ heatmap, hasMLData }) {
    if (!hasMLData || !heatmap || heatmap.length === 0) {
        return (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-12 text-center">
                <p className="text-slate-400 italic font-serif text-lg">
                Full attention analysis not available for this case study.
                </p>
            </div>
        );
    }

    const maxWeight = Math.max(...heatmap.map(s => s.attention_score));

    return (
    <div className="space-y-6">
      {/* Legend / Toolbar */}
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          Narrative Attention Map
        </h3>
        <div className="flex items-center gap-3 text-xs font-bold text-slate-400 uppercase">
          <span>Low Interest</span>
          <div className="w-32 h-1.5 rounded-full bg-gradient-to-r from-slate-100 to-blue-500 border border-slate-200"></div>
          <span className="text-blue-600">High Attention</span>
        </div>
      </div>

      {/* Main Text Body */}
      <div className="h-[850px] overflow-y-auto border border-slate-200 rounded-xl bg-white p-8 shadow-inner">
        <div className="font-serif text-lg leading-relaxed text-slate-800 antialiased">
          {heatmap.map((sentence, idx) => {
            const relativeWeight = maxWeight > 0 ? (sentence.attention_score / maxWeight) : 0;
            // Opacity scaling using standard rgba
            const backgroundColor = `rgba(14, 165, 233, ${relativeWeight * 0.4})`;

            return (
              <span
                key={idx}
                className="inline transition-all rounded-sm px-0.5 group relative cursor-help hover:ring-1 hover:ring-blue-300"
                style={{ backgroundColor }}
              >
                {sentence.sentence_text}{" "}
                
                <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                  <span className="bg-slate-900 text-white text-xs px-2 py-1 rounded shadow-xl whitespace-nowrap">
                    Attention Weight: {sentence.attention_score.toFixed(4)}
                  </span>
                </span>
              </span>
            );
          })}
        </div>
    </div>
    </div>
  );
}