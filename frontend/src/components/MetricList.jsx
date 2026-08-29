import React from 'react';
import { METRIC_DEFINITIONS, getDefaultDefinition } from '../helper/metric_definitions';

const MetricList = ({ data }) => {
  console.log(data);
  const features = data?.features || {};
  const attributions = data?.feature_attributions || {};
  const globalImportance = data?.global_importance || {};

  const blacklisted = [
    "Number of organizations mentioned",
    "Number of named individuals",
    "Number of countries or regions mentioned"
  ];

  const rawList = Object.keys(globalImportance)
  .filter(name => !blacklisted.includes(name))
  .map(academicName => {
    const featureKey = Object.keys(features).find(
      k => k.toLowerCase().replace(/_/g, ' ') === academicName.toLowerCase().replace(/_/g, ' ')
    );
    const val = features[featureKey];
    
    const attrKeyWithSuffix = `${academicName}_AbsAttribution`;
    const localRaw = attributions[academicName] ?? attributions[attrKeyWithSuffix] ?? 0;

    const globalRaw = globalImportance[academicName] || 0;

    return {
      name: academicName,
      value: val,
      localRaw: localRaw,
      globalRaw: globalRaw
    };
  })
  .filter(item => item.value !== undefined);

  const maxLocal = Math.max(...rawList.map(i => i.localRaw), 0.0001);
  const maxGlobal = Math.max(...rawList.map(i => i.globalRaw), 0.0001);
  const sortedMetrics = rawList.sort((a, b) => b.globalRaw - a.globalRaw);

  const hasFeatures = Object.keys(features).length > 0;

  if (!hasFeatures) {
    return (
      <div className="bg-muted border border-border rounded-lg p-5 text-center">
        <p className="text-sm text-muted-foreground">
          Linguistic features are not enabled for this model. The analysis relies on semantic embeddings only.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-4">
      
      {/* EXPLANATION SECTION */}
      <div className="bg-muted border border-border rounded-lg p-4">
        <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.18em] mb-1.5">Linguistic Feature Analysis</h3>
        <p className="text-xs text-muted-foreground leading-relaxed">
          This profile shows how linguistic features influence the prediction. <span className="font-semibold text-secondary-foreground">Global Weight</span> indicates how the model values each feature across all cases. <span className="font-semibold text-secondary-foreground">Local Weight</span> shows how much this specific feature influenced this case's prediction.
        </p>
      </div>

      {/* METRICS CONTAINER - Fixed height with independent scrolling */}
      <div className="h-screen overflow-y-auto custom-scrollbar border border-border rounded-lg bg-card p-3">
        <div className="space-y-3">
          
          {sortedMetrics.map((item, idx) => {
            const def = METRIC_DEFINITIONS[item.name] || getDefaultDefinition(item.name);
            const localRel = (item.localRaw / maxLocal) * 100;
            const globalRel = (item.globalRaw / maxGlobal) * 100;

            return (
              <div key={idx} className="bg-muted border border-border rounded-lg p-4 hover:bg-card transition-colors">
                
                {/* HEADER: Title + Value */}
                <div className="flex justify-between items-start mb-3 gap-4">
                  <div className="flex-1">
                    <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.18em] mb-0.5">
                      #{idx + 1} • {def.category}
                    </div>
                    <h4 className="text-sm font-bold text-foreground">
                      {item.name}
                    </h4>
                  </div>
                  <div className="text-right ml-4">
                    <span className="text-base font-semibold text-foreground tabular-nums block">
                      {def.format(Number(item.value))}
                    </span>
                    <span className="text-xs text-muted-foreground font-medium">Measured value</span>
                  </div>
                </div>

                {/* COMPARISON: Side-by-Side Bars */}
                <div className="space-y-4 mt-4 pt-4 border-t border-border">
                  
                  {/* Global Weight */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-secondary-foreground">Global Weight</span>
                      <span className="text-xs font-semibold text-muted-foreground">{globalRel.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full transition-all duration-700"
                        style={{ width: `${globalRel}%` }} 
                      />
                    </div>
                    <p className="text-[9px] text-muted-foreground mt-1 italic">Model baseline importance across all cases</p>
                  </div>

                  {/* Local Weight */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-semibold text-secondary-foreground">Local Weight</span>
                      <span className="text-xs font-semibold text-secondary-foreground">{localRel.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div 
                        className="h-full bg-accent rounded-full transition-all duration-700"
                        style={{ width: `${localRel}%` }} 
                      />
                    </div>
                    <p className="text-[9px] text-muted-foreground mt-1 italic">Influence on this case's prediction</p>
                  </div>
                </div>

              </div>
            );
          })}

        </div>
      </div>
    </div>
  );
};

export default MetricList;
