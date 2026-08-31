export const METRIC_DEFINITIONS = {
  // ==========================================
  // LINGUISTIC COMPLEXITY & READABILITY 
  // ==========================================
  "Flesch Reading Ease": {
    category: "Syntactic Complexity",
    description: "Evaluates structural density based on sentence lengths and syllable-per-word frequencies.",
    range: "0 – 100",
    bestRange: "0 – 40",
    format: (v) => v?.toFixed(1),
    getExplanation: (v) => v < 40 
      ? "Advanced Academic Profile. The network favors this high-density, formal syntax structure as a marker of academic rigor." 
      : "Low Structural Density. A simplified narrative style may correlate with lower validation probabilities in this model.",
    getColor: (v) => v < 40 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "Automated Readability Index": {
    category: "Linguistic Grade Level",
    description: "Calculates the US Grade Level equivalent required for narrative comprehension using character and word ratios.",
    range: "1 – 16+",
    bestRange: "14+",
    format: (v) => Math.round(v), 
    getExplanation: (v) => v >= 14 
      ? "Post-Secondary Execution. Complex character-to-word matrices align with elite research dissemination standards." 
      : "General Audience Syntax. Comprehension requirements below undergraduate baselines may trigger a penalization for lack of depth.",
    getColor: (v) => v >= 14 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "Dale-Chall Readability Score": {
    category: "Lexical Sophistication",
    description: "Assesses vocabulary depth by calculating the percentage of specialized, non-standard words used.",
    range: "0.0 – 10.0+",
    bestRange: "9.0+",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v >= 9.0 
      ? "Advanced Technical Register. High saturation of domain-specific terminology provides strong positive validation signals." 
      : "Standard Word Register. Reliance on common vocabulary structures fails to demonstrate specialized domain authority.",
    getColor: (v) => v >= 9.0 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "SMOG Index": {
    category: "Polysyllabic Density",
    description: "Estimates the precise years of formal education required for complete document comprehension based on polysyllabic word distribution.",
    range: "3 – 20",
    bestRange: "14+",
    format: (v) => Math.round(v), 
    getExplanation: (v) => v >= 14 
      ? "Higher Education Demands. Dense polysyllabic sentence structures statistically correlate with verified impact portfolios." 
      : "Lower Literacy Demand. Simplified syllabic tracking indicates a descriptive narrative rather than an analytical evidence framework.",
    getColor: (v) => v >= 14 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },

  // ==========================================
  // SENTIMENT & NARRATIVE TRAJECTORY
  // ==========================================
  "Sentiment (mean)": {
    category: "Global Textual Tone",
    description: "The mean emotional trajectory across the entire corpus grid.",
    range: "-1.00 to +1.00",
    bestRange: "0.00 to +0.30",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.05 
      ? "Optimistic/Progressive Baseline. A sustained positive trajectory signals verified socio-economic success to the fusion layer." 
      : "Neutral/Flat Affect. Purely objective or defensive reporting without progressive outcome markers limits predictive confidence.",
    getColor: (v) => v > 0.05 ? "text-success bg-success/10" : "text-muted-foreground bg-muted"
  },
  "Sentiment (90th)": {
    category: "Peak Outcome Salience",
    description: "The emotional intensity of the top 10% most positive sentences in the text.",
    range: "-1.00 to +1.00",
    bestRange: "+0.60 to +1.00",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.6 
      ? "High Triumphalism. Peak segments contain high-salience 'success statements' that command heavy attention layer weights." 
      : "Subdued Peak Assertions. The most impactful claims lack the positive linguistic emphasis typically found in high-scoring case studies.",
    getColor: (v) => v > 0.6 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "Sentiment (75th)": {
    category: "Upper-Quartile Validation",
    description: "The emotional boundary marking the top 25% of the narrative's trajectory.",
    range: "-1.00 to +1.00",
    bestRange: "+0.30 to +0.70",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.3 
      ? "Consistent Success Narrative. A strong upper-quartile ensures that impact evidence is reinforced throughout the narrative."
      : "Low Affirmation Density. Sustained proof of positive socio-economic translation is statistically weak across this quadrant.",
    getColor: (v) => v > 0.3 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "Sentiment (10th)": {
    category: "Negative Assertion Baseline",
    description: "The emotional intensity of the bottom 10% most negative sentences in the text.",
    range: "-1.00 to +1.00",
    bestRange: "-1.00 to -0.30",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v < -0.3 
      ? "Pessimistic/Regression Baseline. A sustained negative trajectory signals potential challenges to the fusion layer." 
      : "Neutral/Flat Affect. Purely objective or defensive reporting without progressive outcome markers limits predictive confidence.",
    getColor: (v) => v < -0.3 ? "text-destructive bg-destructive/10" : "text-muted-foreground bg-muted"
  },
  "Sentiment (50th)": {
    category: "Median Textual Tone",
    description: "The emotional trajectory at the narrative midpoint.",
    range: "-1.00 to +1.00",
    bestRange: "0.00 to +0.30",
    format: (v) => v?.toFixed(2),
    getExplanation: (v) => v > 0.05 
      ? "Optimistic/Progressive Baseline. A sustained positive trajectory signals verified socio-economic success to the fusion layer." 
      : "Neutral/Flat Affect. Purely objective or defensive reporting without progressive outcome markers limits predictive confidence.",
    getColor: (v) => v > 0.05 ? "text-success bg-success/10" : "text-muted-foreground bg-muted"
    },

  // ==========================================
  // TOKEN FREQUENCIES & STAKEHOLDER EVIDENCE
  // ==========================================
  "Word count": {
    category: "Evidence Capacity",
    description: "Total structural length and token volume of the submitted case study text.",
    range: "0 - 2,500+",
    bestRange: "1,000 - 2,000",
    format: (v) => Number(v).toLocaleString(),
    getExplanation: (v) => v >= 1000 
      ? "Optimal Narrative Scale. Sufficient token volume allows the AttentionMIL layer to build cross-sentence dependencies." 
      : "Truncated Structural Scale. Limited length constraints the extraction of distinct named entities, restricting network convergence.",
    getColor: (v) => v >= 1000 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "Paragraph count": {
    category: "",
    description: "Total number of paragraphs in the document, indicating structural segmentation.",
    range: "0 - 100+",
    bestRange: "5 - 20",
    format: (v) => v,
    getExplanation: (v) => v >= 5 && v <= 20
      ? "Well-Structured Narrative. A balanced paragraph count indicates clear thematic segmentation, aiding model comprehension." 
      : "Overly Dense or Sparse Structure. Too few paragraphs may indicate a lack of depth, while too many can fragment the narrative flow.",
    getColor: (v) => v >= 5 && v <= 20 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "DATE": {
    category: "Temporal Validation (NER)",
    description: "Frequency of explicit chronological markers mapped by the SpaCy token extraction pipeline.",
    range: "0+",
    bestRange: "8+",
    format: (v) => v,
    getExplanation: (v) => v >= 8
      ? "Robust Chronological Framework. High date density signals a structured, long-term impact timeline to the network."
      : "Sparse Chronological Anchors. A lack of specific timelines may cause the model to flag the evidence as anecdotal.",
    getColor: (v) => v >= 8 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "MONEY": {
    category: "Economic Attribution (NER)",
    description: "Frequency of explicit financial extractions denoting funding capital, revenue generation, or socio-economic windfalls.",
    range: "0+",
    bestRange: "1+",
    format: (v) => v,
    getExplanation: (v) => v > 0 
      ? "Quantifiable Economic Evidence. Financial tokens provide highly weighted, objective verification of socio-economic translation."
      : "No Economic Attribution. The narrative relies entirely on qualitative claims, skipping a primary high-weight model indicator.",
    getColor: (v) => v > 0 ? "text-success bg-success/10" : "text-muted-foreground bg-muted"
  },
  "ORG": {
    category: "Institutional Network Density (NER)",
    description: "Frequency of organizational extractions indicating active institutional stakeholders, corporate partners, or external bodies.",
    range: "0+",
    bestRange: "12+",
    format: (v) => v,
    getExplanation: (v) => v >= 12 
      ? "High Stakeholder Reach. A dense institutional profile proves widespread collaboration and external translation to the model."
      : "Isolated Institutional Profile. Few unique external bodies are recognized, indicating a localized impact footprint.",
    getColor: (v) => v >= 12 ? "text-success bg-success/10" : "text-warning bg-warning/10"
  },
  "PERSON": {
    category: "Qualitative Attribution (NER)",
    description: "Frequency of named individual extractions representing key researchers, beneficiaries, or policy leads.",
    range: "0+",
    bestRange: "1+",
    format: (v) => v,
    getExplanation: () => "Individual Provenance Tracker. Maps specific human agents to the narrative framework to verify research leadership and targeted beneficiary tracking.",
    getColor: () => "text-info bg-info/10"
  }
};

export const ENTITY_METRIC_KEYS = ["ORG", "MONEY", "PERSON"];

// Fallback for any metrics not explicitly defined above
export const getDefaultDefinition = (featureName) => ({
  category: "Model Feature",
  description: `Model-derived feature ${featureName} used by the classifier.`,
  bestRange: "Higher is better",
  format: (v) => typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(3) : v,
  getExplanation: () => `A weighted feature used by the AI model. Higher counts or scores generally indicate denser evidence.`,
  getColor: () => "text-muted-foreground bg-muted"
});
