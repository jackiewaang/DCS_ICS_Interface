const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";
const USE_SAMPLE_DATA = import.meta.env.VITE_USE_SAMPLE_DATA === "true";

const MOCK_CONFIGS = [
  {
    config_id: 1,
    name: "Qwen3-Embedding-4B Quantile MIL Fusion",
    emb_model: "Qwen3-Embedding-4B",
    run_mode: "classification",
    fusion_type: "gated",
    normalise_emb: true,
    normalise_case_feats: true,
    label_config: { labels: ["Low Impact", "High Impact"] },
    use_features: 1,
    input_granularity: "sentence",
  },
  {
    config_id: 2,
    name: "all-roberta-large-v1 Full Text",
    emb_model: "all-roberta-large-v1",
    run_mode: "classification",
    fusion_type: "none",
    normalise_emb: true,
    normalise_case_feats: false,
    label_config: { labels: ["Low Impact", "High Impact"] },
    use_features: 0,
    input_granularity: "full_text",
  },
];

const MOCK_CASES = [
  {
    inference_id: "mock-9821",
    document_id: 4187,
    created_at: "2026-07-15T12:00:00Z",
    case_id: 140219,
    ref_year: 2021,
    title: "Reducing Urban Flood Risk Through Community-Led Forecasting",
    institution: "Northbridge University",
    uoa: "UOA 14 - Geography and Environmental Studies",
    status: "analysed",
    ground_truth: 3.8,
    gpa: 3.8,
    true_label: 1,
    model_name: "Qwen3-Embedding-4B Quantile MIL Fusion",
    input_granularity: "sentence",
    model_prediction: 0.87,
    prediction_label: "High Impact",
    model_label: "High Impact",
    narrative_contribution: 0.68,
    feature_contribution: 0.32,
    inference_time_ms: 1240,
    sections: {
      summary: "Research on flood forecasting and participatory planning was translated into decision tools for city councils, insurers, and emergency responders.",
      research: "The underpinning research combined hydrological modelling, household vulnerability mapping, and social science evaluation of local warning systems.",
      impact: "The programme changed flood-preparedness protocols across regional authorities, reduced repeat losses for exposed households, and informed national resilience guidance.",
    },
    heatmap: [
      {
        sentence_text: "The forecasting framework was adopted by three city councils and used to redesign emergency response thresholds for more than 120,000 residents.",
        attention_score: 0.1568,
      },
      {
        sentence_text: "Insurance partners reported a 22 percent reduction in repeat claims after household-level warnings were introduced in high-risk neighbourhoods.",
        attention_score: 0.1324,
      },
      {
        sentence_text: "The Environment Agency cited the research in revised national guidance for surface-water flood response planning.",
        attention_score: 0.1187,
      },
      {
        sentence_text: "Community workshops helped residents interpret risk maps and prepare evacuation plans before seasonal rainfall peaks.",
        attention_score: 0.0972,
      },
      {
        sentence_text: "Local authorities used the dashboard during incident exercises to coordinate shelters, road closures, and public messaging.",
        attention_score: 0.0845,
      },
      {
        sentence_text: "The research team published peer-reviewed work on model calibration and social acceptance of alert thresholds.",
        attention_score: 0.0608,
      },
      {
        sentence_text: "Project documentation was archived in the university repository and made available to regional planning officers.",
        attention_score: 0.0419,
      },
      {
        sentence_text: "The project began with a pilot study in two catchments before expanding to the regional partnership.",
        attention_score: 0.0335,
      },
    ],
    features: {
      "Flesch Reading Ease": 34.7,
      "Dale-Chall Readability Score": 9.64,
      "SMOG Index": 15.2,
      "Automated Readability Index": 16.1,
      "Sentiment (mean)": 0.18,
      "Sentiment (10th)": -0.28,
      "Sentiment (50th)": 0.11,
      "Sentiment (75th)": 0.42,
      "Sentiment (90th)": 0.76,
      "Word count": 1860,
      "Paragraph count": 12,
      ORG: 15,
      MONEY: 4,
      PERSON: 5,
      DATE: 11,
    },
    feature_attributions: {
      "Flesch Reading Ease": 0.096,
      "Dale-Chall Readability Score": 0.141,
      "SMOG Index": 0.087,
      "Automated Readability Index": 0.103,
      "Sentiment (mean)": 0.058,
      "Sentiment (10th)": 0.025,
      "Sentiment (50th)": 0.034,
      "Sentiment (75th)": 0.073,
      "Sentiment (90th)": 0.119,
      "Word count": 0.082,
      "Paragraph count": 0.045,
      ORG: 0.128,
      MONEY: 0.111,
      PERSON: 0.049,
      DATE: 0.053,
    },
    global_importance: {
      "Flesch Reading Ease": 0.71,
      "Dale-Chall Readability Score": 0.88,
      "SMOG Index": 0.64,
      "Automated Readability Index": 0.69,
      "Sentiment (mean)": 0.45,
      "Sentiment (10th)": 0.22,
      "Sentiment (50th)": 0.31,
      "Sentiment (75th)": 0.52,
      "Sentiment (90th)": 0.79,
      "Word count": 0.57,
      "Paragraph count": 0.36,
      ORG: 0.74,
      MONEY: 0.62,
      PERSON: 0.41,
      DATE: 0.49,
    },
    entities: {
      ORG: ["Environment Agency", "Northbridge City Council", "Calder Resilience Partnership", "Yorkshire Water", "Flood Re", "Cabinet Office"],
      MONEY: ["GBP 4.2 million", "22 percent reduction", "GBP 780,000 avoided losses", "120,000 residents"],
      PERSON: ["Professor Aisha Rahman", "Dr. Oliver Chen", "Maria Patel", "James Whitfield", "Helen Morris"],
    },
  },
];

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown Error" }));
        throw new Error(error.detail || `HTTP Error: ${response.status}`);
    }
    return response.json();
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

async function loadSampleCaseById(caseId) {
  const normalizedId = String(caseId).replace(/^mock-/, "");
  return MOCK_CASES.find((item) => {
    return (
      String(item.inference_id) === String(caseId) ||
      String(item.document_id) === normalizedId ||
      String(item.case_id) === normalizedId
    );
  }) || MOCK_CASES[0];
}

async function loadSampleCases(limit = 10) {
  return MOCK_CASES.slice(0, limit);
}

async function getSampleConfigs() {
  return MOCK_CONFIGS;
}

function buildSampleSearchResults(query = "", uoa = "") {
  const normalizedQuery = query.trim().toLowerCase();
  const normalizedUoa = uoa.trim().toLowerCase();

  return MOCK_CASES
    .filter((item) => {
      const title = cleanText(item.title).toLowerCase();
      const caseId = String(item.document_id).toLowerCase();
      const institution = cleanText(item.institution).toLowerCase();
      const modelName = cleanText(item.model_name).toLowerCase();
      const itemUoa = String(item.uoa || "").toLowerCase();

      const matchesQuery = !normalizedQuery || title.includes(normalizedQuery) || caseId.includes(normalizedQuery) || institution.includes(normalizedQuery) || modelName.includes(normalizedQuery) || itemUoa.includes(normalizedQuery);
      const matchesUoa = !normalizedUoa || itemUoa.includes(normalizedUoa);

      return matchesQuery && matchesUoa;
    })
    .slice(0, 12)
    .map((item) => ({
      inference_id: item.inference_id,
      document_id: item.document_id,
      title: cleanText(item.title),
      model_name: item.model_name,
      uoa: item.uoa,
      institution: item.institution,
    }));
}

async function getSampleCases(query = "", uoa = "") {
  const results = buildSampleSearchResults(query, uoa);

  if (query || uoa) {
    return results;
  }

  return loadSampleCases(10);
}

async function getSampleDraft(file) {
  return {
    title: file?.name || "Mock REF case study.pdf",
    sections: {
      summary: "This draft summary was generated from mock upload data. It represents the case overview section returned by the PDF extraction endpoint.",
      research: "This draft underpinning research section describes the academic basis, methods, and findings that support the impact claim.",
      impact: "This draft impact section describes beneficiaries, reach, significance, and evidence of change for the uploaded case study.",
    },
  };
}

function normalizeInferenceOutput(output = {}, draft = {}, configId = null) {
  const featureNames = output.feature_names || [];
  const featureGates = output.feature_gates || [];
  const featureAttributions = Object.fromEntries(
    featureNames.map((name, index) => [name, Number(featureGates[index] || 0)])
  );

  return {
    inference_id: output.inference_id || `draft-${Date.now()}`,
    document_id: output.document_id || "draft",
    created_at: output.created_at || new Date().toISOString(),
    title: draft.title || "Untitled inference",
    institution: draft.institution || "Draft upload",
    uoa: draft.uoa || "User supplied case",
    status: "draft",
    ref_year: null,
    ground_truth: null,
    gpa: null,
    true_label: null,
    score: Number(output.score ?? 0),
    label: output.label || (Number(output.score ?? 0) >= 0.5 ? "High Impact" : "Low Impact"),
    attention: output.attention || [],
    sentences: output.sentences || [],
    model_prediction: Number(output.score ?? 0),
    prediction_label: output.label || (Number(output.score ?? 0) >= 0.5 ? "High Impact" : "Low Impact"),
    model_label: output.label,
    model_name: output.model?.name || "Selected model",
    input_granularity: output.model?.input_granularity,
    narrative_contribution: output.narrative_contribution,
    feature_contribution: output.feature_contribution,
    inference_time_ms: output.inference_time_ms ?? output.inference_time ?? output.elapsed_ms ?? null,
    config_id: output.model?.config_id || configId,
    sections: draft.sections || {},
    heatmap: (output.heatmap || []).map((item) => ({
      sentence_text: item.sentence_text || item.sentence || "",
      attention_score: Number(item.attention_score ?? item.attention ?? 0),
    })),
    features: output.features || {},
    entities: output.entities || {},
    ordered_features: output.ordered_features || [],
    feature_names: featureNames,
    feature_gates: featureGates,
    feature_attributions: output.feature_attributions || featureAttributions,
    global_importance: output.global_importance || {},
  };
}

export const api = {
  // --- MODEL CONFIGS ---
  async getConfigs() {
    if (USE_SAMPLE_DATA) {
      return getSampleConfigs();
    }

    try {
      const response = await fetch(`${API_BASE}/analysis/models`);
      return handleResponse(response);
    } catch {
      return getSampleConfigs();
    }
  },

  // --- ANALYSIS ENGINE ---
  async runAnalysis(file, configId) {
    if (USE_SAMPLE_DATA) {
      return loadSampleCaseById("100");
    }

    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await fetch(`${API_BASE}/analysis/run?config_id=${configId}`, {
        method: "POST",
        body: formData,
      });
      return handleResponse(response);
    } catch {
      return loadSampleCaseById("100");
    }
  },

  async uploadCase(file) {
    if (USE_SAMPLE_DATA) {
      return getSampleDraft(file);
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/cases/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },

  async runInference(sections, configId, draft = {}) {
    if (USE_SAMPLE_DATA) {
      return {
        ...MOCK_CASES[0],
        title: draft.title || MOCK_CASES[0].title,
        sections,
        inference_time_ms: MOCK_CASES[0].inference_time_ms,
      };
    }

    const response = await fetch(`${API_BASE}/analysis/inference?config_id=${configId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: cleanText(draft.title) || "Untitled inference",
        institution: draft.institution || "Draft upload",
        uoa: draft.uoa || "User supplied case",
        summary: sections.summary || "",
        research: sections.research || "",
        impact: sections.impact || "",
      }),
    });
    const output = await handleResponse(response);
    return normalizeInferenceOutput(output, { ...draft, sections }, configId);
  },

  async getInferenceById(inferenceId) {
    if (USE_SAMPLE_DATA || String(inferenceId).startsWith("mock-")) {
      return loadSampleCaseById(inferenceId);
    }

    try {
      const response = await fetch(`${API_BASE}/cases/inference/${inferenceId}`);
      return handleResponse(response);
    } catch {
      return loadSampleCaseById(inferenceId);
    }
  },

  async getLatestInference() {
    if (USE_SAMPLE_DATA) {
      return loadSampleCaseById(MOCK_CASES[0].inference_id);
    }

    const response = await fetch(`${API_BASE}/cases/latest`);
    return handleResponse(response);
  },

  // --- CASE MANAGEMENT ---
  async getCases(query = "", uoa = "") {
    if (USE_SAMPLE_DATA) {
      return getSampleCases(query, uoa);
    }

    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (uoa) params.append("uoa", uoa);
    
    try {
      const response = await fetch(`${API_BASE}/cases/?${params.toString()}`);
      return handleResponse(response);
    } catch {
      return getSampleCases(query, uoa);
    }
  },

  async getCaseById(documentId) {
    if (USE_SAMPLE_DATA || String(documentId).startsWith("mock-")) {
      return loadSampleCaseById(documentId);
    }

    try {
      const response = await fetch(`${API_BASE}/cases/${documentId}`);
      return handleResponse(response);
    } catch {
      return loadSampleCaseById(documentId);
    }
  }
};
