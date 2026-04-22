import { useState, useEffect } from "react";
import { api } from "./services/api";
import { Search, Upload, Terminal, LayoutDashboard, ChevronLeft, ChevronRight, Settings2, Layers } from "lucide-react";
import Dashboard from "./pages/Dashboard";
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
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export default function App() {
  // State to track the currently active tab
  const [currentView, setCurrentView] = useState("browse");
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false); // sidebar management
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
  }

  const activeConfig = models.find(m => m.config_id.toString() === activeConfigId);

  return (
    <div className="flex bg-slate-50 overflow-hidden h-screen w-full">
      
      {/* SIDEBAR NAVIGATION */}
      <aside className={`bg-slate-900 text-slate-300 flex flex-col shadow-xl z-10 shrink-0 transition-all duration-300 ease-in-out relative ${isCollapsed ? 'w-20' : 'w-72'}`}>

        {/* COLLAPSE BUTTON - Swapped to Blue */}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)} 
          className="absolute -right-3 top-12 bg-blue-600 text-white rounded-full p-1 shadow-lg border-2 border-slate-50 hover:bg-blue-700 transition-colors z-20 cursor-pointer">
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>

        <div className={`p-6 overflow-hidden ${isCollapsed ? 'items-center' : ''}`}>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 whitespace-nowrap">
            <LayoutDashboard className="h-5 w-5 text-blue-400 shrink-0" />
            {!isCollapsed && <span>REF Analysis</span>}
          </h2>
          {!isCollapsed && <p className="text-xs text-slate-500 mt-1">Impact Case Evaluation</p>}
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
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
        </nav>

        {/* --- DYNAMIC CONFIGURATION SECTION --- */}
        <div className={`mt-auto border-t border-slate-800 p-6 space-y-6 transition-all duration-300 ${isCollapsed ? 'opacity-0 invisible h-0' : 'opacity-100'}`}>
          <div className="flex items-center gap-2 text-blue-400">
            <Settings2 size={16} />
            <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500">
              Inference Settings
            </h3>
          </div>

          {/* 1. Dynamic Model Selection */}
          <div className="space-y-2">
            <Label className="text-[10px] text-slate-500 uppercase">Active Engine</Label>
              <Select value={activeConfigId} onValueChange={setActiveConfigId}>
                <SelectTrigger className="w-full bg-slate-950 border-slate-800 text-slate-300 h-9 text-xs focus:ring-blue-600">
                  <SelectValue placeholder="Select Model" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-300">
                  {models.map((model) => (
                    <SelectItem key={model.config_id} value={model.config_id.toString()} className="text-xs focus:bg-blue-600">
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator className="bg-slate-800" />

            {/* 2. Feature Status (Reflects DB State) */}
            <div className="space-y-3">
              <Label className="text-[10px] text-slate-500 uppercase">Enabled Features</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="features" 
                    checked={activeConfig?.use_features === 1} 
                    disabled 
                    className="border-slate-700 data-[state=checked]:bg-blue-600 disabled:opacity-50" 
                  />
                  <label className="text-xs text-slate-400 font-medium leading-none">
                    Linguistic GTFs
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="spacy" 
                    checked={activeConfig?.input_granularity === "sentence"} 
                    disabled 
                    className="border-slate-700 data-[state=checked]:bg-blue-600 disabled:opacity-50" 
                  />
                  <label className="text-xs text-slate-400 font-medium leading-none">
                    Attention Heatmap
                  </label>
                </div>
              </div>
            </div>

            <Separator className="bg-slate-800" />

            {/* 3. Text Granularity (Reflects DB State) */}
            <div className="space-y-3">
              <Label className="text-[10px] text-slate-500 uppercase">Input Resolution</Label>
              <RadioGroup 
                value={activeConfig?.input_granularity === "full_text" ? "document" : "sentence"} 
                className="space-y-2"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem 
                    value="document" 
                    id="full" 
                    disabled 
                    className="border-slate-700 text-blue-500 disabled:opacity-50" 
                  />
                  <Label htmlFor="full" className="text-xs text-slate-400 font-medium cursor-default">
                    Document Level
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem 
                    value="sentence" 
                    id="sentence" 
                    disabled 
                    className="border-slate-700 text-blue-500 disabled:opacity-50" 
                  />
                  <Label htmlFor="sentence" className="text-xs text-slate-400 font-medium cursor-default">
                    Sentence Level (MIL)
                  </Label>
                </div>
              </RadioGroup>
            </div>
          </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 h-screen overflow-y-auto relative bg-slate-50">
        {currentView === "browse" && (
          <Dashboard 
            initialCaseId={selectedCaseId} 
            onClearInitial={() => setSelectedCaseId(null)} 
          />
        )}
        {currentView === "upload" && (
          <UploadPage 
            onAnalysisComplete={handleNewAnalysis} 
            activeConfigId={activeConfigId} // Pass this so UploadPage knows which model to use
          />
        )}
        {currentView === "prompts" && <PromptLab />}
      </main>
    </div>
  );
}