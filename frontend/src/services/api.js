const API_BASE = "/api";
const USER_ID_KEY = "user_id";
const USER_ID = localStorage.getItem(USER_ID_KEY) || crypto.randomUUID();
localStorage.setItem(USER_ID_KEY, USER_ID);

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
    llm_input: output.llm_input || null,
  };
}

export const api = {
  // --- MODEL CONFIGS ---
  async getConfigs() {
    const response = await fetch(`${API_BASE}/analysis/models`);
    return handleResponse(response);
  },

  async getRuntimeModels() {
    const response = await fetch(`${API_BASE}/analysis/runtime-models`);
    return handleResponse(response);
  },

  async uploadCase(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/cases/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },

  async runInference(sections, configId, draft = {}) {
    const response = await fetch(`${API_BASE}/analysis/inference?config_id=${configId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-ID": USER_ID,
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

  async getLLMFeedback(llmInput, signal) {
    const response = await fetch(`${API_BASE}/analysis/llm-feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-ID": USER_ID,
      },
      body: JSON.stringify(llmInput),
      signal,
    });
    return handleResponse(response);
  },

  // --- FEEDBACK ---
  async submitFeedback(feedback) {
    const response = await fetch(`${API_BASE}/feedback/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(feedback),
    });
    return handleResponse(response);
  }
};
