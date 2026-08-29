import { useCallback, useState, useEffect } from "react";
import { api } from "./services/api";
import { Bot, Cpu, Database, History as HistoryIcon, Upload, LayoutDashboard, ChevronLeft, ChevronRight, MessageSquare } from "lucide-react";
import FeedbackPage from "./pages/FeedbackPage";
import RuntimeModelCard from "./components/RuntimeModelCard";
import InferenceHistoryPage from "./pages/InferenceHistoryPage";
import ModelConfigsPage from "./pages/ModelConfigsPage";
import UploadPage from "./pages/UploadPage";
import NavItem from "./components/ui/NavItem";

export default function App() {
  const [currentView, setCurrentView] = useState("upload");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [inferenceHistory, setInferenceHistory] = useState([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [models, setModels] = useState([]);
  const [isModelsLoading, setIsModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState("");
  const [activeConfigId, setActiveConfigId] = useState("");
  const [runtimeModels, setRuntimeModels] = useState({
    embedding_model: null,
    llm_model: null,
  });

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await api.getConfigs();
        setModels(data);
        if (data.length > 0) setActiveConfigId(data[0].config_id.toString());
      } catch (err) {
        setModelsError(err.message || "Model configurations could not be loaded.");
        console.error("Failed to load models:", err.message);
      } finally {
        setIsModelsLoading(false);
      }
    };
    fetchModels();
  }, []);

  useEffect(() => {
    const fetchRuntimeModels = async () => {
      try {
        setRuntimeModels(await api.getRuntimeModels());
      } catch (err) {
        console.error("Failed to load runtime model information:", err.message);
      }
    };
    fetchRuntimeModels();
  }, []);

  const handleAnalysisUpdate = useCallback((result) => {
    setInferenceHistory((current) => {
      const existingIndex = current.findIndex((item) => item.inference_id === result.inference_id);
      if (existingIndex === -1) {
        return [result, ...current];
      }

      return current.map((item, index) => index === existingIndex ? result : item);
    });
    setSelectedHistoryId(result.inference_id);
  }, []);

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
            <RuntimeModelCard icon={Cpu} label="Embedding" value={runtimeModels.embedding_model} />
            <RuntimeModelCard icon={Bot} label="LLM" value={runtimeModels.llm_model} />
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
            onResultUpdate={handleAnalysisUpdate}
          />
        )}
        {currentView === "upload" && (
          <UploadPage 
            onAnalysisComplete={handleAnalysisUpdate}
            activeConfigId={activeConfigId}
          />
        )}
        {currentView === "models" && (
          <ModelConfigsPage
            models={models}
            isLoading={isModelsLoading}
            error={modelsError}
          />
        )}
        {currentView === "feedback" && <FeedbackPage />}
      </main>
    </div>
  );
}
