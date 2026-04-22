export const METRIC_DEFINITIONS = {
  // --- READABILITY METRICS ---
  "Flesch Reading Ease": {
    category: "Linguistic Complexity",
    range: "0-100",
    format: (v) => v?.toFixed(1),
    getExplanation: (v) => v < 40 
      ? "Professional/Academic Style. The model strongly favors this complex, formal tone for high-impact validation." 
      : "Conversational Style. Scores above 60 are often penalized by the model as they may lack professional rigor.",
    getColor: (v) => v < 40 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "Automated Readability Index": {
    category: "Grade Level",
    range: "1-14+",
    format: (v) => Math.round(v), // Represents US Grade Level
    getExplanation: (v) => v > 12 
      ? "University Level. The model rewards complex sentence structures and longer word lengths typical of high-impact research." 
      : "Standard/Basic Level. A score below 12 (High School) may indicate a narrative that lacks the structural density the model prioritizes.",
    getColor: (v) => v > 12 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "Dale-Chall Readability Score": {
    category: "Vocabulary Depth",
    range: "0-10+",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v >= 9.0 
      ? "Sophisticated Vocabulary. High use of precise, technical terminology—a strong positive indicator for this model." 
      : "Common Vocabulary. The text relies on 'easy' words. The model may flag this as lacking the specific terminology of a professional ICS.",
    getColor: (v) => v >= 9.0 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "SMOG Index": {
    category: "Educational Level",
    range: "1-20 (Years)",
    format: (v) => Math.round(v), // Convert to Integer (Years of schooling)
    getExplanation: (v) => v > 14 
      ? "Post-Graduate Level. High linguistic demand (14+ years of education) is a positive predictor for the MIL model." 
      : "Undergraduate/General Level. If the SMOG index is too low, the model may perceive the evidence as lacking technical depth.",
    getColor: (v) => v > 14 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },

  // --- SENTIMENT METRICS ---
  "Sentiment (mean)": {
    category: "Emotional Tone",
    range: "-1.0 to +1.0",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.1 
      ? "Sustained Positive Narrative. A positive average tone signals a 'Success Story,' which the model identifies with high impact." 
      : "Neutral/Flat Tone. Purely objective reporting without positive outcome markers can result in lower model confidence.",
    getColor: (v) => v > 0.1 ? "text-emerald-600 bg-emerald-50" : "text-slate-500 bg-slate-50"
  },
  "Sentiment (90th)": {
    category: "Peak Positivity",
    range: "-1.0 to +1.0",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.7 
      ? "High Triumphalism. The most positive 10% of your text is very strong, likely containing 'Power Sentences' that drive the AI's decision." 
      : "Low Peak Positivity. Even the strongest claims feel subdued. The model looks for 'breakout' positive evidence.",
    getColor: (v) => v > 0.7 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "Sentiment (75th)": {
    category: "Narrative Tone",
    range: "-1.0 to +1.0",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.4 
      ? "Strong Impact Markers. The top 25% of your sentences carry a clear 'Success Narrative' that the model highly values." 
      : "Low Impact Intensity. Even your stronger claims lack the emotional 'punch' or positive framing the AI associates with high-impact cases.",
    getColor: (v) => v > 0.4 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },

  // --- ENTITY & STRUCTURAL COUNTS ---
  "Word count": {
    category: "Structural Depth",
    range: "0-1500+",
    format: (v) => v,
    getExplanation: (v) => v > 750 
      ? "Adequate Evidence Volume. Sufficient length allows the model to detect enough distinct entities and attention-worthy evidence." 
      : "Insufficient Detail. Short texts often lack the density of evidence (names, dates, stats) required for a high-impact rating.",
    getColor: (v) => v > 750 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "DATE": {
    category: "Quantitative Evidence (NER)",
    format: (v) => v,
    getExplanation: (v) => "Chronological evidence. High counts signal to the model that the impact is backed by concrete timelines and historical data.",
    getColor: (v) => v > 5 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "MONEY": {
    category: "Economic Impact",
    format: (v) => v,
    getExplanation: (v) => v > 0 
      ? "Financial evidence detected. This is a high-weight driver for demonstrating economic significance."
      : "No financial markers found. If applicable, adding specific funding amounts or economic savings can boost the impact score.",
    getColor: (v) => v > 0 ? "text-emerald-600 bg-emerald-50" : "text-slate-400 bg-slate-50"
  },
  "ORG": {
    category: "Partnership Evidence",
    format: (v) => v,
    getExplanation: (v) => v > 8 
      ? "Strong stakeholder density. The model views high organization counts as evidence of significant reach and collaboration."
      : "Low organization count. Consider explicitly naming more partners, government bodies, or NGOs to strengthen evidence.",
    getColor: (v) => v > 8 ? "text-emerald-600 bg-emerald-50" : "text-amber-600 bg-amber-50"
  },
  "PERSON": {
    category: "Qualitative Evidence (NER)",
    format: (v) => v,
    getExplanation: (v) => "Individual beneficiaries or key researchers. Used by the model to verify human-level impact and specific collaborations.",
    getColor: () => "text-blue-600 bg-blue-50"
  }
};

// Fallback for any metrics not explicitly defined above
export const getDefaultDefinition = (featureName) => ({
  category: "Model Feature",
  format: (v) => typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(3) : v,
  getExplanation: () => `A weighted feature used by the AI model. Higher counts or scores generally indicate denser evidence.`,
  getColor: () => "text-slate-600 bg-slate-100"
});