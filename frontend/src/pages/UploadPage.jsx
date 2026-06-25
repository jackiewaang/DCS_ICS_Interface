import { useState, useRef } from 'react';
import { Upload, FileText, X, ArrowRight, Loader2} from "lucide-react";
import { api } from "@/services/api"; 
import { 
  Card, 
  CardContent, 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const UploadPage = ({ onAnalysisComplete, activeConfigId }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    try {
      const data = await api.runAnalysis(file, activeConfigId);
      
      onAnalysisComplete(data.inference_id);

    } catch (err) {
      console.error("Analysis Pipeline Error:", err);
      setError(err.message || "The model encountered an error during inference.");
      setIsUploading(false);
    }
  };

  const removeFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setIsUploading(false);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-6 md:p-8 space-y-8">
      
      <header className="space-y-2">
        <h1 className="text-2xl md:text-[2rem] font-semibold text-slate-950 tracking-tight">
          New Case Analysis
        </h1>
        <p className="text-slate-500 text-base max-w-2xl leading-relaxed">
          Upload a research case document to receive an in-depth evaluation using the active model engine.
        </p>
      </header>

      <Card 
        className={`border-2 border-dashed border-slate-200 shadow-none bg-white flex flex-col h-72 overflow-hidden transition-all duration-200 
          ${!file ? 'hover:bg-slate-50 hover:border-blue-300' : 'border-solid'}`}
      >
        <CardContent className="p-0 flex-1 flex flex-col">
          {!file ? (
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="group h-full w-full flex flex-col items-center justify-center cursor-pointer p-8"
            >
              <input 
                type="file" 
                className="hidden" 
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".pdf,.docx,.txt"
              />
              <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-5 border border-slate-100 group-hover:scale-105 group-hover:bg-white group-hover:border-slate-300 transition-all duration-300">
                <Upload className="h-8 w-8 text-slate-400 group-hover:text-slate-700 transition-colors" />
              </div>
              <h3 className="text-lg font-semibold text-slate-700">Drop your case study here</h3>
              <p className="text-sm text-slate-400 mt-2 font-medium">PDF, Word, or text files are supported</p>
            </div>
          ) : (
            <div className="p-7 space-y-7 animate-in fade-in slide-in-from-bottom-2 h-full flex flex-col justify-center">
              <div className="flex items-center justify-between bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-950 rounded-lg flex items-center justify-center shadow-md">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <p className="text-base font-semibold text-slate-900">{file.name}</p>
                    <p className="text-[10px] text-slate-400 uppercase tracking-[0.18em] font-black">
                      {(file.size / 1024).toFixed(0)} KB • Ready for evaluation
                    </p>
                  </div>
                </div>
                {!isUploading && (
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={removeFile}
                    className="text-slate-300 hover:text-rose-500 hover:bg-rose-50 cursor-pointer transition-colors"
                  >
                    <X size={24} />
                  </Button>
                )}
              </div>

              {isUploading && (
                <div className="flex flex-col items-center justify-center space-y-4 py-6">
                  <div className="relative">
                    <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                       <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-black text-slate-900 uppercase tracking-widest">
                      Inference Engine Active
                    </p>
                    <p className="text-[11px] text-slate-400 italic mt-1">
                      Processing narrative sections and extracting attention weights...
                    </p>
                  </div>
                </div>
              )}

              {error && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-lg">
                  <p className="text-xs text-rose-600 font-medium">Error: {error}</p>
                </div>
              )}

              {!isUploading && !error && (
                <div className="flex justify-end">
                  <Button 
                    onClick={handleUpload}
                    className="h-11 px-8 bg-slate-950 hover:bg-slate-800 text-white font-semibold rounded-md transition-all cursor-pointer shadow-lg active:scale-95"
                  >
                    <div className="flex items-center gap-2">
                      Start Analysis
                      <ArrowRight className="h-5 w-5" />
                    </div>
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-2">
        <InstructionCard 
          step="Step 1" 
          title="Sectional Embedding" 
          desc="The model generates high-dimensional embeddings for specific narrative sections, including the Summary, Underpinning Research, and Details of Impact." 
        />
        <InstructionCard 
          step="Step 2" 
          title="Feature Generation" 
          desc="If enabled, the pipeline dynamically extracts linguistic and sentiment features tailored to the model's specific configuration requirements." 
        />
        <InstructionCard 
          step="Step 3" 
          title="Predictive Fusion" 
          desc="The engine synthesizes embeddings and features to predict the impact score, returning a sentence-level attention heatmap if supported by the architecture." 
        />
      </div>
    </div>
  );
};

const MetricBox = ({ label, value }) => (
  <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.18em] mb-1">{label}</p>
    <p className="text-xl font-semibold text-slate-900">{value}</p>
  </div>
);

const InstructionCard = ({ step, title, desc }) => (
  <div className="space-y-3 p-2">
    <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">{step}</span>
    <h4 className="font-semibold text-slate-900 text-sm">{title}</h4>
    <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
  </div>
);

export default UploadPage;