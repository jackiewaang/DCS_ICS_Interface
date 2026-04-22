import { useState, useEffect, useRef } from "react";
import { Search, Loader2 } from "lucide-react";
import { api } from "@/services/api";

export default function SearchHeader({ onCaseSelect }) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
        if (query.length < 2) {
            setResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsLoading(true);
            try {
                // API now returns Inference-centric results
                const data = await api.getCases(query); 
                setResults(data);
                setIsOpen(true);
            } catch (err) {
                console.error("Search error:", err);
            } finally {
                setIsLoading(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    return (
        <div className="w-full border-b border-slate-200 bg-white" ref={wrapperRef}>
            <div className="max-w-7xl mx-auto px-8 py-4">
                <div className="relative group max-w-2xl">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                        {isLoading ? <Loader2 className="w-4 h-4 text-blue-500 animate-spin" /> : <Search className="w-4 h-4 text-slate-400" />}
                    </div>
                    
                    <input
                        type="text"
                        className="w-full bg-slate-50 border border-slate-200 py-2 pl-11 pr-4 rounded-md text-sm transition-all focus:bg-white focus:ring-1 focus:ring-blue-600 focus:border-blue-600 outline-none"
                        placeholder="Search by Title, Model, or Institution..."
                        value={query}
                        onFocus={() => query.length > 0 && setIsOpen(true)}
                        onChange={(e) => setQuery(e.target.value)}
                    />

                    {isOpen && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-md shadow-lg z-[100] max-h-80 overflow-y-auto">
                            {results.length > 0 ? (
                                results.map((item) => (
                                    <button
                                        key={item.inference_id} // Unique primary key
                                        onClick={() => {
                                            onCaseSelect(item.inference_id); // Pass the inference ID
                                            setIsOpen(false);
                                            setQuery("");
                                        }}
                                        className="cursor-pointer w-full text-left px-4 py-3 hover:bg-blue-50 flex flex-col border-b border-slate-50 last:border-0"
                                    >
                                        <div className="flex justify-between items-start gap-4">
                                            <span className="text-sm font-semibold text-slate-900">{item.title}</span>
                                            {/* Model Badge */}
                                            <span className="text-[9px] font-bold text-blue-600 bg-blue-50 border border-blue-100 px-1.5 py-0.5 rounded uppercase shrink-0">
                                                {item.model_name}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                                                DOC: {item.document_id} • {item.uoa} • {item.institution}
                                            </span>
                                        </div>
                                    </button>
                                ))
                            ) : (
                                <div className="px-4 py-6 text-center text-xs text-slate-400 italic">
                                    No matching analysis results found.
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}