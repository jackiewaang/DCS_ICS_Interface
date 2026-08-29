import { useState, useEffect } from "react";
import { api } from "./services/api";
import { Bot, Cpu, Database, Search, Upload, Terminal, LayoutDashboard, ChevronLeft, ChevronRight, MessageSquare } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import FeedbackPage from "./pages/FeedbackPage";
import ModelConfigsPage from "./pages/ModelConfigsPage";
import UploadPage from "./pages/UploadPage";
import PromptLab from "./pages/PromptLab";
import NavItem from "./components/ui/NavItem";

export default function App() {
  const [currentView, setCurrentView] = useState("browse");
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
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

  const handleNewAnalysis = (newInferenceId) => {
    setSelectedCaseId(newInferenceId);
    setCurrentView("browse");
  };

  return (
    <div className="flex bg-background overflow-hidden h-screen w-full text-foreground">
      <aside className={`bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border shadow-sm z-10 shrink-0 transition-all duration-300 ease-in-out relative ${isCollapsed ? 'w-20' : 'w-68'}`}>
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)} 
          className="absolute -right-3 top-10 bg-card text-primary rounded-full p-1 shadow-sm border border-border hover:bg-secondary transition-colors z-20 cursor-pointer">
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>

        <div className={`p-5 overflow-hidden ${isCollapsed ? 'items-center' : ''}`}>
          <h2 className="text-lg font-semibold text-sidebar-foreground flex items-center gap-2 whitespace-nowrap">
            <LayoutDashboard className="h-4 w-4 text-sidebar-foreground/80 shrink-0" />
            {!isCollapsed && <span>REF Analysis</span>}
          </h2>
          {!isCollapsed && <p className="text-[11px] text-sidebar-foreground/70 mt-1">Impact case evaluation</p>}
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-3">
          <div className="hidden">
            <NavItem
              icon={<Search className="h-4 w-4 shrink-0" />}
              label="Browse Past Cases"
              isActive={currentView === "browse"}
              onClick={() => setCurrentView("browse")}
              isCollapsed={isCollapsed}
            />
          </div>
          <NavItem
            icon={<Upload className="h-4 w-4 shrink-0" />}
            label="Upload New Case"
            isActive={currentView === "upload"}
            onClick={() => setCurrentView("upload")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<Database className="h-4 w-4 shrink-0" />}
            label="Model Configs"
            isActive={currentView === "models"}
            onClick={() => setCurrentView("models")}
            isCollapsed={isCollapsed}
          />
          <div className="hidden">
            <NavItem
              icon={<Terminal className="h-4 w-4 shrink-0" />}
              label="Prompt Lab"
              isActive={currentView === "prompts"}
              onClick={() => setCurrentView("prompts")}
              isCollapsed={isCollapsed}
            />
          </div>
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
            <div className="rounded-md border border-sidebar-border bg-sidebar-accent p-3">
              <div className="flex items-center gap-2 text-sidebar-foreground/70">
                <Cpu className="h-3.5 w-3.5 shrink-0" />
                <span className="text-[10px] font-semibold uppercase tracking-wider">Embedding</span>
              </div>
              <p className="mt-1.5 truncate text-xs font-medium text-sidebar-accent-foreground" title={runtimeModels.embedding_model || "Unavailable"}>
                {runtimeModels.embedding_model || "Unavailable"}
              </p>
            </div>
            <div className="rounded-md border border-sidebar-border bg-sidebar-accent p-3">
              <div className="flex items-center gap-2 text-sidebar-foreground/70">
                <Bot className="h-3.5 w-3.5 shrink-0" />
                <span className="text-[10px] font-semibold uppercase tracking-wider">LLM</span>
              </div>
              <p className="mt-1.5 truncate text-xs font-medium text-sidebar-accent-foreground" title={runtimeModels.llm_model || "Unavailable"}>
                {runtimeModels.llm_model || "Unavailable"}
              </p>
            </div>
          </div>
          <p className="mt-4 border-t border-sidebar-border pt-4 text-xs leading-relaxed text-sidebar-foreground/65">
            Documents, model outputs, and usage activity are logged for research analysis using a randomly generated session identifier rather than your name or other direct identifiers. Inference results are retained in the application database for approximately two minutes before automatic deletion. Refreshing the page clears the results shown in your browser, but does not immediately remove research logs already recorded on the server.
          </p>
        </div>
      </aside>

      <main className="flex-1 h-screen overflow-y-auto relative bg-transparent">
        {currentView === "browse" && (
          <Dashboard 
            initialCaseId={selectedCaseId} 
            onClearInitial={() => setSelectedCaseId(null)} 
          />
        )}
        {currentView === "upload" && (
          <UploadPage 
            onAnalysisComplete={handleNewAnalysis} 
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
        {currentView === "prompts" && <PromptLab />}
        {currentView === "feedback" && <FeedbackPage />}
      </main>
    </div>
  );
}
