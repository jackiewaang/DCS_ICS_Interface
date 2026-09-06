const API_BASE = "/api";
const USER_ID_KEY = "user_id";

function createUserId() {
  const generatedId = globalThis.crypto?.randomUUID?.()
    || `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  try {
    const storedId = localStorage.getItem(USER_ID_KEY);
    if (storedId) return storedId;
    localStorage.setItem(USER_ID_KEY, generatedId);
  } catch (error) {
    console.warn('Session identifier could not be persisted:', error);
  }

  return generatedId;
}

const USER_ID = createUserId();

function errorDetail(payload, status) {
  const detail = payload?.detail ?? payload?.message;
  if (typeof detail === 'string' && detail.trim()) return detail.trim();
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg || item?.message).filter(Boolean);
    if (messages.length) return messages.join(' ');
  }
  return `The analysis service returned an error (${status}). Please try again.`;
}

async function handleResponse(response) {
  const rawBody = await response.text();
  let payload = null;

  if (rawBody) {
    try {
      payload = JSON.parse(rawBody);
    } catch {
      if (response.ok) {
        throw new Error('The analysis service returned an unreadable response. Please try again.');
      }
    }
  }

  if (!response.ok) {
    throw new Error(errorDetail(payload, response.status));
  }

  return payload;
}

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizeInferenceOutput(output = {}, draft = {}, configId = null) {
  if (!output || typeof output !== "object" || Array.isArray(output)) {
    throw new Error("The inference service returned an invalid result. Please try again.");
  }

  const score = Number(output.score);
  if (!Number.isFinite(score)) {
    throw new Error("The inference result did not include a valid prediction score. Please try again.");
  }

  const featureNames = Array.isArray(output.feature_names) ? output.feature_names : [];
  const featureGates = Array.isArray(output.feature_gates) ? output.feature_gates : [];
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
    score,
    label: output.label || (score >= 0.5 ? "High Impact" : "Low Impact"),
    attention: Array.isArray(output.attention) ? output.attention : [],
    sentences: Array.isArray(output.sentences) ? output.sentences : [],
    model_prediction: score,
    prediction_label: output.label || (score >= 0.5 ? "High Impact" : "Low Impact"),
    model_label: output.label,
    model_name: output.model?.name || "Selected model",
    input_granularity: output.model?.input_granularity,
    narrative_contribution: output.narrative_contribution,
    feature_contribution: output.feature_contribution,
    inference_time_ms: output.inference_time_ms ?? output.inference_time ?? output.elapsed_ms ?? null,
    config_id: output.model?.config_id || configId,
    sections: draft.sections || {},
    heatmap: (Array.isArray(output.heatmap) ? output.heatmap : []).map((item) => ({
      sentence_text: item.sentence_text || item.sentence || "",
      attention_score: Number(item.attention_score ?? item.attention ?? 0),
    })),
    features: output.features && typeof output.features === "object" ? output.features : {},
    entities: output.entities && typeof output.entities === "object" ? output.entities : {},
    ordered_features: Array.isArray(output.ordered_features) ? output.ordered_features : [],
    feature_names: featureNames,
    feature_gates: featureGates,
    feature_attributions: output.feature_attributions && typeof output.feature_attributions === "object" ? output.feature_attributions : featureAttributions,
    global_importance: output.global_importance && typeof output.global_importance === "object" ? output.global_importance : {},
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

  async runInference(sections, configId, draft = {}, slurmModels = {}) {
    const params = new URLSearchParams({ config_id: configId });
    if (slurmModels.embeddingModelName) {
      params.set("embedding_model_name", slurmModels.embeddingModelName);
    }
    if (slurmModels.llmModelName) {
      params.set("llm_model_name", slurmModels.llmModelName);
    }
    const response = await fetch(`${API_BASE}/analysis/inference?${params}`, {
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

  async runGemmaInference(sections, title) {
    const response = await fetch(`${API_BASE}/gemma/inference`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-ID": USER_ID,
      },
      body: JSON.stringify({
        title: cleanText(title) || "Untitled inference",
        summary: sections.summary || "",
        research: sections.research || "",
        impact: sections.impact || "",
      }),
    });
    return handleResponse(response);
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
