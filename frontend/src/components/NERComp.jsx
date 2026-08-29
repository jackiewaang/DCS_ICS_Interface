import React from 'react';
import { decodeHTML } from '@/helper/utils';

const NERComp = ({ data }) => {
  const nerData = data?.entities || {};
  
  const categories = [
    { id: "ORG", aliases: ["orgs", "ORG"], label: "Organizations & Partners" },
    { id: "MONEY", aliases: ["money", "MONEY"], label: "Economic Impact" },
    { id: "PERSON", aliases: ["people", "PERSON"], label: "Key Individuals" }
  ];

  return (
    <div className="space-y-6">
      
      {/* EXPLANATION SECTION */}
      <div className="bg-muted border border-border rounded-lg p-4">
        <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.18em] mb-1.5">Evidence Index</h3>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Key entities extracted from the narrative that may influence impact assessment: organizations, financial impact, and stakeholder involvement.
        </p>
      </div>

      {/* CARDS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {categories.map((cat) => {
          const rawItems = cat.aliases.reduce((acc, alias) => {
            return acc.length > 0 ? acc : (nerData[alias] || []);
          }, []);
          
          const items = Array.from(
            new Set(rawItems.map(i => decodeHTML(i).trim()))
          ).filter(Boolean);

          return (
            <div key={cat.id} className="bg-card border border-border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
              
              {/* HEADER */}
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-bold text-foreground">{cat.label}</h4>
                <span className="text-xs font-semibold bg-secondary text-secondary-foreground px-2 py-1 rounded-full">
                  {items.length}
                </span>
              </div>

              {/* CONTENT */}
              {items.length > 0 ? (
                <ul className="space-y-2">
                  {items.slice(0, 12).map((item, idx) => (
                    <li key={idx} className="text-xs text-secondary-foreground flex items-start gap-2">
                      <span className="text-muted-foreground select-none shrink-0 mt-1">•</span>
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                  
                  {items.length > 12 && (
                    <li className="text-[10px] text-muted-foreground pt-2 mt-2 border-t border-border italic">
                      +{items.length - 12} more detected
                    </li>
                  )}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground italic">No evidence detected</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NERComp;
