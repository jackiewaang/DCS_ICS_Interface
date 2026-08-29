import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./services/api";
import { Bot, Cpu, Database, History as HistoryIcon, Upload, LayoutDashboard, ChevronLeft, ChevronRight, MessageSquare } from "lucide-react";
import FeedbackPage from "./pages/FeedbackPage";
import RuntimeModelCard from "./components/RuntimeModelCard";
import InferenceHistoryPage from "./pages/InferenceHistoryPage";
import ModelConfigsPage from "./pages/ModelConfigsPage";
import UploadPage from "./pages/UploadPage";
import NavItem from "./components/ui/NavItem";
import { getUserErrorMessage } from "./helper/error_messages";

const LLM_TIMEOUT_MS = 305_000;

export default function App() {
  const [currentView, setCurrentView] = useState("upload");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [inferenceHistory, setInferenceHistory] = useState([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [uploadInferenceResult, setUploadInferenceResult] = useState(null);
  const [models, setModels] = useState([]);
  const [isModelsLoading, setIsModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState("");
  const [activeConfigId, setActiveConfigId] = useState("");
  const [runtimeModels, setRuntimeModels] = useState({
    embedding_model: null,
    llm_model: null,
  });
  const [runtimeModelsError, setRuntimeModelsError] = useState("");
  const modelsRequestId = useRef(0);
  const runtimeModelsRequestId = useRef(0);
  const llmRequests = useRef(new Map());
  const llmStartedIds = useRef(new Set());

  const fetchModels = useCallback(async () => {
    const requestId = ++modelsRequestId.current;
    setIsModelsLoading(true);
    setModelsError("");
    try {
      const data = await api.getConfigs();
      if (!Array.isArray(data)) throw new Error("The model list returned by the service is invalid.");
      if (requestId !== modelsRequestId.current) return;
      setModels(data);
      setActiveConfigId((current) => {
        if (data.some((model) => String(model.config_id) === current)) return current;
        return data[0]?.config_id?.toString() || "";
      });
    } catch (err) {
      if (requestId !== modelsRequestId.current) return;
      setModels([]);
      setActiveConfigId("");
      setModelsError(getUserErrorMessage(err, "Model configurations could not be loaded."));
      console.error("Failed to load models:", err);
    } finally {
      if (requestId === modelsRequestId.current) setIsModelsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const fetchRuntimeModels = useCallback(async () => {
    const requestId = ++runtimeModelsRequestId.current;
    setRuntimeModelsError("");
    try {
      const data = await api.getRuntimeModels();
      if (!data || typeof data !== "object") throw new Error("Runtime model information is invalid.");
      if (requestId !== runtimeModelsRequestId.current) return;
      setRuntimeModels(data);
    } catch (err) {
      if (requestId !== runtimeModelsRequestId.current) return;
      setRuntimeModels({ embedding_model: null, llm_model: null });
      setRuntimeModelsError(getUserErrorMessage(err, "Runtime model information could not be loaded."));
      console.error("Failed to load runtime model information:", err);
    }
  }, []);

  useEffect(() => {
    fetchRuntimeModels();
  }, [fetchRuntimeModels]);

  const updateLlmFeedback = useCallback((inferenceId, llmFeedback) => {
    setInferenceHistory((current) => current.map((item) => (
      item.inference_id === inferenceId
        ? { ...item, llm_feedback: llmFeedback }
        : item
    )));
    setUploadInferenceResult((current) => (
      current?.inference_id === inferenceId
        ? { ...current, llm_feedback: llmFeedback }
        : current
    ));
  }, []);

  const startLlmFeedback = useCallback((result) => {
    const inferenceId = result.inference_id;
    if (!inferenceId || !result.llm_input || llmStartedIds.current.has(inferenceId)) return;

    const controller = new AbortController();
    const request = { controller, didTimeout: false, timeoutId: null };
    request.timeoutId = window.setTimeout(() => {
      request.didTimeout = true;
      controller.abort();
    }, LLM_TIMEOUT_MS);
    llmStartedIds.current.add(inferenceId);
    llmRequests.current.set(inferenceId, request);

    api.getLLMFeedback(result.llm_input, controller.signal)
      .then((feedback) => {
        updateLlmFeedback(inferenceId, {
          result: feedback,
          status: "completed",
          errorMessage: "",
        });
      })
      .catch((error) => {
        if (error.name === "AbortError" && !request.didTimeout) return;
        updateLlmFeedback(inferenceId, {
          result: null,
          status: "error",
          errorMessage: request.didTimeout
            ? "AI insight generation timed out after five minutes."
            : getUserErrorMessage(error, "AI insights could not be generated. Please try again later."),
        });
      })
      .finally(() => {
        window.clearTimeout(request.timeoutId);
        if (llmRequests.current.get(inferenceId) === request) {
          llmRequests.current.delete(inferenceId);
        }
      });
  }, [updateLlmFeedback]);

  useEffect(() => () => {
    llmRequests.current.forEach(({ controller, timeoutId }) => {
      window.clearTimeout(timeoutId);
      controller.abort();
    });
    llmRequests.current.clear();
    llmStartedIds.current.clear();
  }, []);

  const handleAnalysisComplete = useCallback((result) => {
    const sharedResult = {
      ...result,
      llm_feedback: result.llm_feedback || (result.llm_input
        ? { result: null, status: "running", errorMessage: "" }
        : { result: null, status: "not_found", errorMessage: "" }),
    };

    setInferenceHistory((current) => {
      const existingIndex = current.findIndex((item) => item.inference_id === sharedResult.inference_id);
      if (existingIndex === -1) {
        return [sharedResult, ...current];
      }

      return current.map((item, index) => index === existingIndex ? sharedResult : item);
    });
    setUploadInferenceResult(sharedResult);
    setSelectedHistoryId(sharedResult.inference_id);

    if (sharedResult.llm_feedback.status === "running") {
      startLlmFeedback(sharedResult);
    }

    return sharedResult;
  }, [startLlmFeedback]);

  return (
    <div className="flex bg-background overflow-hidden h-screen w-full text-foreground">
      <aside className={`bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border shadow-sm z-10 shrink-0 transition-all duration-300 ease-in-out relative ${isCollapsed ? 'w-20' : 'w-68'}`}>
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)} 
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="absolute -right-4 top-8 z-20 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-2 border-background bg-card text-primary shadow-md transition-all hover:scale-105 hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring">
          {isCollapsed ? <ChevronRight size={17} /> : <ChevronLeft size={17} />}
        </button>

        <div className={`p-5 overflow-hidden ${isCollapsed ? 'items-center' : ''}`}>
          <h2 className="text-lg font-semibold text-sidebar-foreground flex items-center gap-2 whitespace-nowrap">
            <LayoutDashboard className="h-4 w-4 text-sidebar-foreground/80 shrink-0" />
            {!isCollapsed && <span>REF Analysis</span>}
          </h2>
          {!isCollapsed && <p className="text-[11px] text-sidebar-foreground/70 mt-1">Impact case evaluation</p>}
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-3">
          <NavItem
            icon={<Upload className="h-4 w-4 shrink-0" />}
            label="Upload New Case"
            isActive={currentView === "upload"}
            onClick={() => setCurrentView("upload")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<HistoryIcon className="h-4 w-4 shrink-0" />}
            label="Inference History"
            isActive={currentView === "history"}
            onClick={() => setCurrentView("history")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<Database className="h-4 w-4 shrink-0" />}
            label="Model Configs"
            isActive={currentView === "models"}
            onClick={() => setCurrentView("models")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<MessageSquare className="h-4 w-4 shrink-0" />}
            label="Feedback"
            isActive={currentView === "feedback"}
            onClick={() => setCurrentView("feedback")}
            isCollapsed={isCollapsed}
          />
        </nav>

        <div className={`mt-auto border-t border-sidebar-border transition-all duration-300 ${isCollapsed ? 'invisible h-0 overflow-hidden p-0 opacity-0' : 'p-5 opacity-100'}`}>
          <p className="text-[10px] font-black uppercase tracking-widest text-sidebar-foreground/70">
            Runtime Models
          </p>
          <div className="mt-4 space-y-3">
            <RuntimeModelCard icon={Cpu} label="Embedding" value={runtimeModels.embedding_model} error={runtimeModelsError} onRetry={fetchRuntimeModels} />
            <RuntimeModelCard icon={Bot} label="LLM" value={runtimeModels.llm_model} error={runtimeModelsError} onRetry={fetchRuntimeModels} />
            <label className="block rounded-md border border-sidebar-border bg-sidebar-accent p-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/70">
                Inference engine
              </span>
              <select
                value={activeConfigId}
                onChange={(event) => setActiveConfigId(event.target.value)}
                disabled={isModelsLoading || models.length === 0}
                className="mt-2 w-full cursor-pointer rounded-md border border-sidebar-border bg-sidebar px-2.5 py-2 text-xs text-sidebar-foreground outline-none focus:ring-2 focus:ring-sidebar-ring disabled:cursor-not-allowed disabled:opacity-60"
              >
                {models.length === 0 ? <option value="">Unavailable</option> : null}
                {models.map((model) => (
                  <option key={model.config_id} value={model.config_id}>
                    #{model.config_id} · {model.name || model.emb_model || 'Unnamed model'}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </aside>

      <main className="flex-1 h-screen overflow-y-auto relative bg-transparent">
        {currentView === "history" && (
          <InferenceHistoryPage
            history={inferenceHistory}
            selectedId={selectedHistoryId}
            onSelect={setSelectedHistoryId}
          />
        )}
        {currentView === "upload" && (
          <UploadPage 
            inferenceResult={uploadInferenceResult}
            onAnalysisComplete={handleAnalysisComplete}
            onClearAnalysis={() => setUploadInferenceResult(null)}
            activeConfigId={activeConfigId}
            modelsError={modelsError || (!isModelsLoading && models.length === 0
              ? "No inference models are currently registered."
              : "")}
            onRetryModels={fetchModels}
          />
        )}
        {currentView === "models" && (
          <ModelConfigsPage
            models={models}
            isLoading={isModelsLoading}
            error={modelsError}
            onRetry={fetchModels}
          />
        )}
        {currentView === "feedback" && <FeedbackPage />}
      </main>
    </div>
  );
}
