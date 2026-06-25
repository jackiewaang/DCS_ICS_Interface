const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:11005/api";
const USE_SAMPLE_DATA = import.meta.env.VITE_USE_SAMPLE_DATA === "true";

const SAMPLE_INDEX_URL = "/index.json";
const SAMPLE_CASES_PATH = "/data/case_studies";

const sampleCaseCache = new Map();
let sampleIndexPromise = null;

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown Error" }));
        throw new Error(error.detail || `HTTP Error: ${response.status}`);
    }
    return response.json();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP Error: ${response.status}`);
  }
  return response.json();
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizePrediction(prediction = {}) {
  const confidence = Number(prediction.confidence ?? 0.5);
  const label = String(prediction.label || "").toLowerCase().includes("high")
    ? "High Impact"
    : "Low Impact";

  return {
    model_prediction: confidence,
    prediction_label: label,
  };
}

function countItems(values = []) {
  return Array.isArray(values) ? values.length : 0;
}

function buildSampleFeatureMaps(sample = {}) {
  const readability = sample.readability_metrics || {};
  const sentiment = sample.sentiment_analysis || {};
  const ner = sample["SpaCy NER"] || {};
  const wordCount = sample.structure?.word_count ?? 0;

  const features = {
    "Flesch Reading Ease": readability.flesch_reading_ease,
    "Automated Readability Index": readability.automated_readability_index,
    "Dale-Chall Readability Score": readability.dale_chall_readability_score,
    "SMOG Index": readability.smog_index,
    "Sentiment (mean)": sentiment["sentiment (mean)"],
    "Sentiment (75th)": sentiment["sentiment (75th)"],
    "Sentiment (90th)": sentiment["sentiment (90th)"],
    "Word count": wordCount,
    DATE: countItems(ner.DATE),
    MONEY: countItems(ner.MONEY),
    ORG: countItems(ner.ORG),
    PERSON: countItems(ner.PERSON),
  };

  const globalImportance = {
    "Flesch Reading Ease": 0.95,
    "Automated Readability Index": 0.9,
    "Dale-Chall Readability Score": 0.82,
    "SMOG Index": 0.78,
    "Word count": 0.68,
    "Sentiment (mean)": 0.62,
    "Sentiment (90th)": 0.56,
    "Sentiment (75th)": 0.5,
    ORG: 0.42,
    DATE: 0.34,
    MONEY: 0.3,
    PERSON: 0.24,
  };

  const featureAttributions = Object.fromEntries(
    Object.entries(globalImportance).map(([name, importance]) => [
      name,
      Number((importance * 0.65).toFixed(3)),
    ])
  );

  return { features, globalImportance, featureAttributions };
}

function normalizeSampleCase(sample, inferenceId) {
  const caseId = String(sample.case_id || inferenceId || sample.id || "sample");
  const title = cleanText(sample.metadata?.title) || `Sample Case ${caseId}`;
  const institution = cleanText(sample.metadata?.institution) || "Sample archive";
  const uoa = cleanText(sample.metadata?.uoa) || "Sample case";
  const prediction = normalizePrediction(sample.predictions?.mil_fusion);
  const featureMaps = buildSampleFeatureMaps(sample);

  return {
    inference_id: inferenceId || `sample-${caseId}`,
    document_id: caseId,
    title,
    institution,
    uoa,
    model_name: "Sample MIL Fusion",
    ground_truth: null,
    narrative_contribution: 0.75,
    feature_contribution: 0.25,
    heatmap: (sample.text_analysis || []).map((item) => ({
      sentence_text: cleanText(item.text),
      attention_score: Number(item.weight || 0),
    })),
    entities: {
      ORG: sample["SpaCy NER"]?.ORG || [],
      MONEY: sample["SpaCy NER"]?.MONEY || [],
      PERSON: sample["SpaCy NER"]?.PERSON || [],
    },
    ...prediction,
    ...featureMaps,
  };
}

async function loadSampleIndex() {
  if (!sampleIndexPromise) {
    sampleIndexPromise = fetchJson(SAMPLE_INDEX_URL).catch(() => []);
  }

  return sampleIndexPromise;
}

async function loadSampleCaseById(caseId) {
  const normalizedId = String(caseId).replace(/^sample-/, "");

  if (sampleCaseCache.has(normalizedId)) {
    return sampleCaseCache.get(normalizedId);
  }

  const sample = await fetchJson(`${SAMPLE_CASES_PATH}/${normalizedId}.json`);
  const normalized = normalizeSampleCase(sample, `sample-${normalizedId}`);
  sampleCaseCache.set(normalizedId, normalized);
  return normalized;
}

async function loadSampleCases(limit = 10) {
  const index = await loadSampleIndex();
  const ids = index.slice(0, limit).map((item) => item.id);
  const cases = await Promise.all(ids.map((id) => loadSampleCaseById(id).catch(() => null)));
  return cases.filter(Boolean);
}

async function getSampleConfigs() {
  return [
    {
      config_id: 1,
      name: "Sample MIL Fusion",
      use_features: 1,
      input_granularity: "sentence",
    },
    {
      config_id: 2,
      name: "Sample Full Text",
      use_features: 0,
      input_granularity: "full_text",
    },
    {
      config_id: 3,
      name: "Sample Semantic Only",
      use_features: 0,
      input_granularity: "sentence",
    },
  ];
}

function buildSampleSearchResults(index, query = "", uoa = "") {
  const normalizedQuery = query.trim().toLowerCase();
  const normalizedUoa = uoa.trim().toLowerCase();

  return index
    .filter((item) => {
      const title = cleanText(item.title).toLowerCase();
      const caseId = String(item.id).toLowerCase();
      const itemUoa = String(item.uoa || "").toLowerCase();

      const matchesQuery = !normalizedQuery || title.includes(normalizedQuery) || caseId.includes(normalizedQuery) || itemUoa.includes(normalizedQuery);
      const matchesUoa = !normalizedUoa || itemUoa.includes(normalizedUoa);

      return matchesQuery && matchesUoa;
    })
    .slice(0, 12)
    .map((item) => ({
      inference_id: `sample-${item.id}`,
      document_id: item.id,
      title: cleanText(item.title),
      model_name: "Sample MIL Fusion",
      uoa: item.uoa,
      institution: "Sample archive",
    }));
}

async function getSampleCases(query = "", uoa = "") {
  const index = await loadSampleIndex();
  const results = buildSampleSearchResults(index, query, uoa);

  if (query || uoa) {
    return results;
  }

  return loadSampleCases(results.length > 0 ? Math.min(results.length, 10) : 10);
}

export const api = {
  // --- MODEL CONFIGS ---
  async getConfigs() {
    if (USE_SAMPLE_DATA) {
      return getSampleConfigs();
    }

    try {
      const response = await fetch(`${API_BASE}/analysis/configs`);
      return handleResponse(response);
    } catch (error) {
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
    } catch (error) {
      return loadSampleCaseById("100");
    }
  },

  async getInferenceById(inferenceId) {
    if (USE_SAMPLE_DATA || String(inferenceId).startsWith("sample-")) {
      return loadSampleCaseById(inferenceId);
    }

    try {
      const response = await fetch(`${API_BASE}/cases/inference/${inferenceId}`);
      return handleResponse(response);
    } catch (error) {
      return loadSampleCaseById(inferenceId);
    }
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
    } catch (error) {
      return getSampleCases(query, uoa);
    }
  },

  async getCaseById(documentId) {
    if (USE_SAMPLE_DATA || String(documentId).startsWith("sample-")) {
      return loadSampleCaseById(documentId);
    }

    try {
      const response = await fetch(`${API_BASE}/cases/${documentId}`);
      return handleResponse(response);
    } catch (error) {
      return loadSampleCaseById(documentId);
    }
  }
};