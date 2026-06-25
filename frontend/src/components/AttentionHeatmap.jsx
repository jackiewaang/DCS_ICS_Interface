export default function AttentionHeatmap({ heatmap, hasMLData }) {
    if (!hasMLData || !heatmap || heatmap.length === 0) {
        return (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-center">
                <p className="text-sm text-slate-600">
                    Sentence-level attention analysis is not available for this model configuration.
                </p>
            </div>
        );
    }

    const maxWeight = Math.max(...heatmap.map(s => s.attention_score));
    const minWeight = Math.min(...heatmap.map(s => s.attention_score));
    const avgWeight = heatmap.reduce((sum, s) => sum + s.attention_score, 0) / heatmap.length;

    // Normalize weights to 0-1 range
    const range = maxWeight - minWeight || 1;
    const normalizedHeatmap = heatmap.map(s => ({
        ...s,
        normalizedScore: (s.attention_score - minWeight) / range
    }));

    const getColorClass = (normalizedScore) => {
        if (normalizedScore < 0.25) return 'bg-slate-100';
        if (normalizedScore < 0.5) return 'bg-indigo-100';
        if (normalizedScore < 0.75) return 'bg-indigo-200';
        return 'bg-indigo-400';
    };

    return (
        <div className="space-y-6">
            
            {/* EXPLANATION SECTION */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.18em] mb-1.5">Attention Heatmap</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                    This visualization shows which sentences most influenced the model's prediction. Darker highlighting indicates sentences the model weighted more heavily in its decision. Hover over any sentence to see its precise attention weight.
                </p>
            </div>

            {/* STATISTICS CARDS */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-white border border-slate-200 rounded-lg p-3">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide block">Peak Attention</span>
                    <span className="text-lg font-semibold text-slate-900 mt-1 block">{maxWeight.toFixed(4)}</span>
                </div>
                <div className="bg-white border border-slate-200 rounded-lg p-3">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide block">Average Attention</span>
                    <span className="text-lg font-semibold text-slate-700 mt-1 block">{avgWeight.toFixed(4)}</span>
                </div>
                <div className="bg-white border border-slate-200 rounded-lg p-3">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide block">Total Sentences</span>
                    <span className="text-lg font-semibold text-slate-700 mt-1 block">{heatmap.length}</span>
                </div>
            </div>

            {/* LEGEND */}
            <div className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Attention Scale</div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-slate-100 border border-slate-200"></div>
                        <span className="text-xs text-slate-600">Low (0%)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-slate-200 border border-slate-200"></div>
                        <span className="text-xs text-slate-600">25%</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-slate-300 border border-slate-200"></div>
                        <span className="text-xs text-slate-600">50%</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-slate-500 border border-slate-200"></div>
                        <span className="text-xs text-slate-600">High (100%)</span>
                    </div>
                </div>
            </div>

            {/* TEXT BODY - Professional styling */}
            <div className="border border-slate-200 rounded-lg bg-white overflow-hidden shadow-sm">
                <div className="h-150 overflow-y-auto custom-scrollbar p-8">
                    <div className="prose prose-sm max-w-none">
                        <p className="text-sm leading-relaxed text-slate-700">
                            {normalizedHeatmap.map((sentence, idx) => (
                                <span
                                    key={idx}
                                    className={`${getColorClass(sentence.normalizedScore)} rounded px-1 py-0.5 transition-all duration-200 group relative cursor-help hover:ring-2 hover:ring-slate-400 hover:shadow-md inline-block mr-1 mb-1`}
                                    title={`Attention: ${sentence.attention_score.toFixed(4)}`}
                                >
                                    {sentence.sentence_text}
                                    
                                    {/* Tooltip on hover */}
                                    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex z-50">
                                        <span className="bg-slate-950 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap">
                                            Weight: {sentence.attention_score.toFixed(4)} ({(sentence.normalizedScore * 100).toFixed(0)}%)
                                        </span>
                                    </span>
                                </span>
                            ))}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}