import { useState, useEffect } from "react";
import { api } from "./services/api";
import { Search, Upload, Terminal, LayoutDashboard, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, MessageSquare, Settings2 } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import FeedbackPage from "./pages/FeedbackPage";
import UploadPage from "./pages/UploadPage";
import PromptLab from "./pages/PromptLab";
import NavItem from "./components/ui/NavItem";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export default function App() {
  const [currentView, setCurrentView] = useState("browse");
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isSettingsExpanded, setIsSettingsExpanded] = useState(true);
  const [models, setModels] = useState([]);
  const [activeConfigId, setActiveConfigId] = useState("");

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await api.getConfigs();
        setModels(data);
        if (data.length > 0) setActiveConfigId(data[0].config_id.toString());
      } catch (err) {
        console.error("Failed to load models:", err.message);
      }
    };
    fetchModels();
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
          <NavItem
            icon={<Search className="h-4 w-4 shrink-0" />}
            label="Browse Past Cases"
            isActive={currentView === "browse"}
            onClick={() => setCurrentView("browse")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<Upload className="h-4 w-4 shrink-0" />}
            label="Upload New Case"
            isActive={currentView === "upload"}
            onClick={() => setCurrentView("upload")}
            isCollapsed={isCollapsed}
          />
          <NavItem
            icon={<Terminal className="h-4 w-4 shrink-0" />}
            label="Prompt Lab"
            isActive={currentView === "prompts"}
            onClick={() => setCurrentView("prompts")}
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

        <div className={`mt-auto border-t border-sidebar-border p-5 transition-all duration-300 ${isCollapsed ? 'opacity-0 invisible h-0 overflow-hidden' : 'opacity-100'}`}>
          <button
            type="button"
            onClick={() => setIsSettingsExpanded((current) => !current)}
            aria-expanded={isSettingsExpanded}
            className="flex w-full cursor-pointer items-center justify-between gap-3 text-left text-sidebar-foreground/75"
          >
            <span className="flex items-center gap-2">
              <Settings2 size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest text-sidebar-foreground/75">
                Inference Settings
              </span>
            </span>
            {isSettingsExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          <div className={`grid transition-[grid-template-rows,opacity,margin] duration-300 ${isSettingsExpanded ? 'mt-5 grid-rows-[1fr] opacity-100' : 'mt-0 grid-rows-[0fr] opacity-0'}`}>
            <div className="min-h-0 overflow-hidden">
              <div className="space-y-5">
                <div className="space-y-2">
                  <Label className="text-[10px] text-sidebar-foreground/75 uppercase tracking-wider">Active engine</Label>
                  <Select value={activeConfigId} onValueChange={setActiveConfigId}>
                    <SelectTrigger className="w-full bg-sidebar-accent border-sidebar-border text-sidebar-accent-foreground h-9 text-xs focus:ring-sidebar-ring">
                      <SelectValue placeholder="Select Model" />
                    </SelectTrigger>
                    <SelectContent className="bg-sidebar border-sidebar-border text-sidebar-foreground shadow-lg">
                      {models.map((model) => (
                        <SelectItem key={model.config_id} value={model.config_id.toString()} className="text-xs focus:bg-sidebar-accent focus:text-sidebar-accent-foreground">
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
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
        {currentView === "prompts" && <PromptLab />}
        {currentView === "feedback" && <FeedbackPage />}
      </main>
    </div>
  );
}
