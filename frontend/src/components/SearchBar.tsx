import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Loader2, X } from 'lucide-react';
import type { SearchBarProps } from '../types';

interface EnhancedSearchBarProps extends SearchBarProps {
  error?: string | null;
  onClear?: () => void;
}

const SearchBar: React.FC<EnhancedSearchBarProps> = ({ 
  onSearch, 
  loading = false, 
  placeholder = "Search your documents...",
  error = null,
  onClear
}) => {  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const debounceTimeoutRef = useRef<number | undefined>(undefined);
  const inputRef = useRef<HTMLInputElement>(null);

  // Enhanced debouncing with cleanup
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = window.setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [query]);

  // Trigger search when debounced query changes
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
    onClear?.();
    inputRef.current?.focus();
  }, [onClear]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  }, [handleClear]);  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit} className="search-form">
        <div className={`search-input-container ${error ? 'error' : ''}`}>
          <Search className="search-icon" size={20} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="search-input"
            disabled={loading}
            autoComplete="off"
            spellCheck="false"
            aria-label="Search documents"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="clear-button"
              title="Clear search"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="search-button"
            title="Search documents"
            aria-label="Search"
          >
            {loading ? (
              <Loader2 className="loading-spinner" size={20} />
            ) : (
              'Search'
            )}
          </button>
        </div>
        
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
        
        {debouncedQuery && debouncedQuery !== query && !error && (
          <div className="search-hint">
            <span>Searching as you type...</span>
          </div>        )}
      </form>

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
        
        .error-message {
          margin-top: 8px;
          text-align: center;
          color: #ef4444;
          font-size: 14px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 6px;
          padding: 8px 12px;
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
    </div>
  );
};

export default SearchBar;
