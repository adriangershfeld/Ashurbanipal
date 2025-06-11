import React, { useState, useEffect, useCallback } from 'react';
import { Search, Loader2, X } from 'lucide-react';
import type { SearchBarProps } from '../types';

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, 
  loading = false, 
  placeholder = "Search your documents..." 
}) => {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce the search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [query]);

  // Trigger search when debounced query changes and is not empty
  useEffect(() => {
    if (debouncedQuery.trim() && debouncedQuery.length >= 2) {
      onSearch(debouncedQuery.trim());
    }
  }, [debouncedQuery, onSearch]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  }, [query, loading, onSearch]);

  const handleClear = useCallback(() => {
    setQuery('');
    setDebouncedQuery('');
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  }, [handleClear]);
  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <div className="search-input-container">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="search-input"
          disabled={loading}
          autoComplete="off"
          spellCheck="false"
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="clear-button"
            title="Clear search"
          >
            <X size={16} />
          </button>
        )}
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="search-button"
          title="Search documents"
        >
          {loading ? (
            <Loader2 className="loading-spinner" size={20} />
          ) : (
            'Search'
          )}
        </button>
      </div>
      
      {debouncedQuery && debouncedQuery !== query && (
        <div className="search-hint">
          <span>Searching as you type...</span>
        </div>
      )}
      
      <style jsx>{`
        .search-bar {
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }
        
        .search-input-container {
          display: flex;
          align-items: center;
          background: #1a1a2e;
          border: 2px solid #16213e;
          border-radius: 12px;
          padding: 8px 12px;
          transition: border-color 0.2s ease;
        }
        
        .search-input-container:focus-within {
          border-color: #4f46e5;
        }
        
        .search-icon {
          color: #6b7280;
          margin-right: 12px;
          flex-shrink: 0;
        }
        
        .search-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: #f3f4f6;
          font-size: 16px;
          padding: 8px 0;
        }
        
        .search-input::placeholder {
          color: #6b7280;
        }
        
        .search-input:disabled {
          opacity: 0.6;
        }
        
        .search-button {
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px 16px;
          cursor: pointer;
          font-weight: 500;
          transition: background-color 0.2s ease;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .search-button:hover:not(:disabled) {
          background: #4338ca;
        }
          .search-button:disabled {
          background: #374151;
          cursor: not-allowed;
        }
        
        .clear-button {
          background: none;
          border: none;
          color: #6b7280;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          margin: 0 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }
        
        .clear-button:hover {
          color: #f3f4f6;
          background: #374151;
        }
        
        .search-hint {
          margin-top: 8px;
          text-align: center;
          font-size: 12px;
          color: #6b7280;
          font-style: italic;
        }
        
        .loading-spinner {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </form>
  );
};

export default SearchBar;
