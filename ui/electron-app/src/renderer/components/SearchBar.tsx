import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
    initialQuery?: string;
    onSearch: (query: string) => void;
    autoFocus?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ initialQuery = '', onSearch, autoFocus = false }) => {
    const [query, setQuery] = useState(initialQuery);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative w-full max-w-3xl mx-auto group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
            </div>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="block w-full pl-12 pr-4 py-4 rounded-2xl bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 text-lg shadow-sm placeholder-gray-400 dark:placeholder-gray-500 transition-all text-slate-900 dark:text-gray-100 placeholder:text-base placeholder:italic"
                placeholder="Search assets... e.g. 'door', 'tree', 'villa elevation' (bad spelling OK)"
                autoFocus={autoFocus}
            />
        </form>
    );
};

export default SearchBar;
