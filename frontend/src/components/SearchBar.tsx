import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import type { SearchBarProps } from '../types';

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, 
  loading = false, 
  placeholder = "Search your documents..." 
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <div className="search-input-container">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="search-input"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="search-button"
        >
          {loading ? (
            <Loader2 className="loading-spinner" size={20} />
          ) : (
            'Search'
          )}
        </button>
      </div>
      
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
