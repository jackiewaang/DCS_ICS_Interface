import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import SearchHeader from '@/components/SearchHeader';
import CaseHeader from '@/components/CaseHeader';
import AttentionHeatmap from '@/components/AttentionHeatmap';
import MetricList from '@/components/MetricList';
import NERComp from '@/components/NERComp';
import { api } from '@/services/api'; // Centralized API service

const Dashboard = ({ initialCaseId, onClearInitial }) => {
  const [caseData, setCaseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Load full case details using Document ID
   */
  const handleLoadCase = async (id) => {
    setIsLoading(true);
    try {
      // We are now fetching a specific INFERENCE
      const data = await api.getInferenceById(id);
      setCaseData(data);
    } catch (error) {
      console.error("Error loading analysis:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      // If we just uploaded a new file, the backend returned the NEW inference_id
      if (initialCaseId) {
        await handleLoadCase(initialCaseId);
        if (onClearInitial) onClearInitial();
        return;
      }

      if (!caseData) {
        const list = await api.getCases(); // This now returns inference-centric rows
        if (list && list.length > 0) {
          await handleLoadCase(list[0].inference_id);
        }
      }
    };
    init();
  }, [initialCaseId]);

  // Loading state (Empty shell)
  if (isLoading && !caseData) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
          <p className="text-sm font-medium text-slate-500 animate-pulse">
            Retrieving Analysis from Database...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Search Bar - now triggers handleLoadCase via document_id */}
      <SearchHeader onCaseSelect={(id) => handleLoadCase(id)} />

      <div className="flex-1 w-full transition-all duration-300">
        {/* Identity & Prediction Banner */}
        <CaseHeader data={caseData} />

        {/* 2-Column Analytical Report */}
        <main className="max-w-7xl mx-auto px-8 py-12">
          <div className="grid grid-cols-12 gap-12">
            
            {/* LEFT COLUMN: Explainability (Heatmap & NER) */}
            <div className="col-span-12 lg:col-span-8 space-y-12">
              <section>
                <AttentionHeatmap
                  heatmap={caseData?.heatmap || []}
                  // Checks if we have sentence-level weights to show
                  hasMLData={caseData?.heatmap && caseData.heatmap.length > 0}
                />
              </section>

              <section>
                 <NERComp data={caseData} />
              </section>
            </div>

            {/* RIGHT COLUMN: Quantitative Metrics */}
            <aside className="col-span-12 lg:col-span-4 space-y-8">
              <section>
                <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-200 pb-2 mb-6">
                  Linguistic & Sentiment Profile
                </h3>
                {/* MetricList now consumes the parsed features_json from caseData */}
                <MetricList data={caseData} />
              </section>
            </aside>

          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;