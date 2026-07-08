import { useState, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import SearchHeader from '@/components/SearchHeader';
import CaseHeader from '@/components/CaseHeader';
import { api } from '@/services/api'; // Centralized API service
import MainOverviewPanel from '@/components/dashboard/MainOverviewPanel';
import AIInsightsPanel from '@/components/dashboard/AIInsightsPanel';
import HeatmapPanel from '@/components/dashboard/HeatmapPanel';
import FeaturesPanel from '@/components/dashboard/FeaturesPanel';
import EntitiesPanel from '@/components/dashboard/EntitiesPanel';

const TABS = [
  { id: 'main', label: 'Main' },
  { id: 'ai', label: 'AI Insights' },
  { id: 'heatmap', label: 'Heatmap' },
  { id: 'features', label: 'Features' },
  { id: 'entities', label: 'Entities' },
];

const Dashboard = ({ initialCaseId, onClearInitial }) => {
  const [caseData, setCaseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('main');
  const lastHandledInitialCaseId = useRef(null);

  /**
   * Load full case details using Document ID
   */
  const handleLoadCase = async (id) => {
    setActiveTab('main');
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
      if (initialCaseId && lastHandledInitialCaseId.current !== initialCaseId) {
        lastHandledInitialCaseId.current = initialCaseId;
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
  }, [initialCaseId, caseData, onClearInitial]);

  // Loading state (Empty shell)
  if (isLoading && !caseData) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="animate-pulse text-sm font-medium text-muted-foreground">
            Retrieving Analysis from Database...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Search Bar - now triggers handleLoadCase via document_id */}
      <SearchHeader onCaseSelect={(id) => handleLoadCase(id)} />

      <div className="w-full flex-1 bg-background/80 transition-all duration-300">
        <CaseHeader data={caseData} />

        {/* Section tabs */}
        <div className="bg-transparent">
          <div className="mx-auto max-w-7xl px-6 pt-4">
            <div className="flex flex-wrap gap-2 border-b border-border bg-background pb-2">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`cursor-pointer border-0 border-b-2 bg-transparent px-4 py-2 text-sm font-semibold transition-all ${
                    activeTab === tab.id
                      ? 'border-primary text-foreground'
                      : 'border-transparent text-muted-foreground hover:border-border hover:text-foreground'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <main className="max-w-7xl mx-auto px-6 py-5">
          {activeTab === 'main' && <MainOverviewPanel data={caseData} />}
          {activeTab === 'ai' && <AIInsightsPanel data={caseData} />}
          {activeTab === 'heatmap' && <HeatmapPanel data={caseData} />}
          {activeTab === 'features' && <FeaturesPanel data={caseData} />}
          {activeTab === 'entities' && <EntitiesPanel data={caseData} />}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;