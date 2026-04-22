const API_BASE = "http://localhost:8001/api";

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown Error" }));
        throw new Error(error.detail || `HTTP Error: ${response.status}`);
    }
    return response.json();
}

export const api = {
  // --- MODEL CONFIGS ---
  async getConfigs() {
    const response = await fetch(`${API_BASE}/analysis/configs`);
    return handleResponse(response);
  },

  // --- ANALYSIS ENGINE ---
  async runAnalysis(file, configId) {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch(`${API_BASE}/analysis/run?config_id=${configId}`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },

  async getInferenceById(inferenceId) {
    const response = await fetch(`${API_BASE}/cases/inference/${inferenceId}`);
    return handleResponse(response);
  },

  // --- CASE MANAGEMENT ---
  async getCases(query = "", uoa = "") {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (uoa) params.append("uoa", uoa);
    
    const response = await fetch(`${API_BASE}/cases/?${params.toString()}`);
    return handleResponse(response);
  },

  async getCaseById(documentId) {
    const response = await fetch(`${API_BASE}/cases/${documentId}`);
    return handleResponse(response);
  }
};