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
        <div className="relative z-50 w-full border-b border-border/80 bg-secondary/75 backdrop-blur-sm" ref={wrapperRef}>
            <div className="mx-auto max-w-7xl px-6 py-2.5">
                <div className="relative z-50 group max-w-2xl">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                        {isLoading ? <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" /> : <Search className="w-4 h-4 text-muted-foreground/70" />}
                    </div>
                    
                    <input
                        type="text"
                        className="w-full bg-card border border-input py-2.5 pl-11 pr-4 rounded-md text-sm transition-all focus:bg-card focus:ring-1 focus:ring-ring focus:border-ring outline-none"
                        placeholder="Search by Title, Model, or Institution..."
                        value={query}
                        onFocus={() => query.length > 0 && setIsOpen(true)}
                        onChange={(e) => setQuery(e.target.value)}
                    />

                    {isOpen && (
                        <div className="absolute left-0 right-0 top-full z-999 mt-1 max-h-80 overflow-y-auto rounded-md border border-border bg-popover text-popover-foreground shadow-lg" style={{ zIndex: 999 }}>
                            {results.length > 0 ? (
                                results.map((item) => (
                                    <button
                                        key={item.inference_id} // Unique primary key
                                        onClick={() => {
                                            onCaseSelect(item.inference_id); // Pass the inference ID
                                            setIsOpen(false);
                                            setQuery("");
                                        }}
                                        className="group/item cursor-pointer w-full text-left px-4 py-3 hover:bg-accent hover:text-accent-foreground flex flex-col border-b border-border/40 last:border-0"
                                    >
                                        <div className="flex justify-between items-start gap-4">
                                            <span className="text-sm font-semibold">{item.title}</span>
                                            {/* Model Badge */}
                                            <span className="text-[9px] font-bold text-secondary-foreground bg-secondary border border-border px-1.5 py-0.5 rounded uppercase shrink-0">
                                                {item.model_name}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[10px] text-muted-foreground group-hover/item:text-accent-foreground uppercase tracking-wider">
                                                DOC: {item.document_id} • {item.uoa} • {item.institution}
                                            </span>
                                        </div>
                                    </button>
                                ))
                            ) : (
                                <div className="px-4 py-6 text-center text-xs text-muted-foreground italic">
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
