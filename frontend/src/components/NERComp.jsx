import React from 'react';
import { decodeHTML } from '@/helper/utils';

const NERComp = ({ data }) => {
  const nerData = data?.entities || {};
  
  // Standard IDs used for the UI, with an 'aliases' array to handle schema mismatches
  const categories = [
    { id: "ORG", aliases: ["orgs", "ORG"], label: "Organizations & Partners" },
    { id: "MONEY", aliases: ["money", "MONEY"], label: "Economic & Financial Markers" },
    { id: "PERSON", aliases: ["people", "PERSON"], label: "Key Individuals & Stakeholders" }
  ];

  return (
    <div className="mt-12 pt-12 border-t border-slate-200">
      <div className="mb-8">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
          Extracted Evidence Index
        </h3>
        <p className="text-[10px] text-slate-400 mt-1">
          Entity clusters identified by spaCy TRF and mapped to predictive linguistic features.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        {categories.map((cat) => {
          // --- THE MAPPING LOGIC ---
          // This looks for 'ORG' first, and falls back to 'orgs' if 'ORG' is undefined.
          const rawItems = cat.aliases.reduce((acc, alias) => {
            return acc.length > 0 ? acc : (nerData[alias] || []);
          }, []);
          
          const items = Array.from(
            new Set(rawItems.map(i => decodeHTML(i).trim()))
          ).filter(Boolean);

          return (
            <div key={cat.id} className="flex flex-col">
              <h4 className="text-sm font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2 flex justify-between items-center">
                {cat.label}
                <span className="text-[10px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-full border border-blue-100">
                  {items.length}
                </span>
              </h4>
              
              {items.length > 0 ? (
                <ul className="space-y-2">
                  {items.slice(0, 15).map((item, idx) => (
                    <li key={idx} className="text-xs text-slate-600 flex items-start gap-2 group">
                      <span className="text-blue-400 select-none group-hover:text-blue-600 transition-colors">•</span>
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                  
                  {items.length > 15 && (
                    <li className="text-[10px] text-slate-400 italic pt-1 pl-4 border-t border-slate-50 mt-2">
                      + {items.length - 15} additional entries detected
                    </li>
                  )}
                </ul>
              ) : (
                <p className="text-xs text-slate-400 italic">No evidence detected in this category.</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NERComp;