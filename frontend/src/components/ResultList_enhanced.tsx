import React, { useState } from 'react';
import { FileText, Search, Copy, CheckCircle } from 'lucide-react';
import type { ResultListProps, SearchResult } from '../types';

const ResultList: React.FC<ResultListProps> = ({ 
  results, 
  loading = false, 
  onResultClick 
}) => {
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates(prev => ({ ...prev, [id]: true }));
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [id]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  if (loading) {
    return (
      <div className="result-list-loading">
        <div className="loading-skeleton">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="skeleton-item">
              <div className="skeleton-header"></div>
              <div className="skeleton-content"></div>
              <div className="skeleton-content short"></div>
            </div>
          ))}
        </div>
        
        <style jsx>{`
          .result-list-loading {
            padding: 20px;
          }
          
          .skeleton-item {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            animation: pulse 2s ease-in-out infinite;
          }
          
          .skeleton-header {
            height: 20px;
            background: #374151;
            border-radius: 4px;
            margin-bottom: 12px;
            width: 60%;
          }
          
          .skeleton-content {
            height: 16px;
            background: #374151;
            border-radius: 4px;
            margin-bottom: 8px;
          }
          
          .skeleton-content.short {
            width: 40%;
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
        `}</style>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="no-results">
        <Search size={48} className="no-results-icon" />
        <h3>No results found</h3>
        <p>Try adjusting your search query or check if documents have been ingested.</p>
        
        <style jsx>{`
          .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
          }
          
          .no-results-icon {
            margin-bottom: 16px;
            opacity: 0.5;
            color: #4f46e5;
          }
          
          .no-results h3 {
            margin: 0 0 8px 0;
            color: #cbd5e1;
            font-size: 18px;
            font-weight: 600;
          }
          
          .no-results p {
            margin: 0;
            font-size: 14px;
            line-height: 1.5;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="result-list">
      <div className="results-header">
        <span className="results-count">
          {results.length} result{results.length !== 1 ? 's' : ''} found
        </span>
      </div>
      
      <div className="results-container">
        {results.map((result, index) => (
          <ResultCard
            key={result.chunk_id || index}
            result={result}
            onResultClick={onResultClick}
            onCopy={copyToClipboard}
            copiedStates={copiedStates}
          />
        ))}
      </div>
      
      <style jsx>{`
        .result-list {
          padding: 20px;
        }
        
        .results-header {
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #334155;
        }
        
        .results-count {
          color: #cbd5e1;
          font-size: 14px;
          font-weight: 500;
        }
        
        .results-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
      `}</style>
    </div>
  );
};

interface ResultCardProps {
  result: SearchResult;
  onResultClick?: (result: SearchResult) => void;
  onCopy: (text: string, id: string) => void;
  copiedStates: Record<string, boolean>;
}

const ResultCard: React.FC<ResultCardProps> = ({ 
  result, 
  onResultClick, 
  onCopy, 
  copiedStates 
}) => {
  const [expanded, setExpanded] = useState(false);
  const cardId = `result-${result.chunk_id}`;
  
  const handleCardClick = () => {
    if (onResultClick) {
      onResultClick(result);
    }
  };

  const displayContent = expanded 
    ? result.content 
    : `${result.content.slice(0, 300)}${result.content.length > 300 ? '...' : ''}`;

  return (
    <div className="result-card" onClick={handleCardClick}>
      <div className="result-header">
        <div className="result-info">
          <div className="result-file">
            <FileText size={16} />
            <span className="file-name">{result.source_file}</span>
          </div>
          <div className="result-score">
            <span className="score-label">Relevance:</span>
            <span className="score-value">{(result.similarity_score * 100).toFixed(1)}%</span>
          </div>
        </div>
        
        <div className="result-actions">
          <button
            className="copy-button"
            onClick={(e) => {
              e.stopPropagation();
              onCopy(result.content, cardId);
            }}
            title="Copy content"
          >
            {copiedStates[cardId] ? (
              <CheckCircle size={16} className="copied" />
            ) : (
              <Copy size={16} />
            )}
          </button>
        </div>
      </div>
      
      <div className="result-content">
        {displayContent}
      </div>
      
      {result.content.length > 300 && (
        <button 
          className="expand-button"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
      
      <div className="result-meta">
        {result.metadata && Object.keys(result.metadata).length > 0 && (
          <div className="metadata">
            {Object.entries(result.metadata).slice(0, 3).map(([key, value]) => (
              <span key={key} className="meta-item">
                {key}: {String(value)}
              </span>
            ))}
          </div>
        )}
      </div>
      
      <style jsx>{`
        .result-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .result-card:hover {
          border-color: #4f46e5;
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
          transform: translateY(-1px);
        }
        
        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }
        
        .result-info {
          flex: 1;
        }
        
        .result-file {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .file-name {
          color: #f1f5f9;
          font-weight: 500;
          font-size: 14px;
        }
        
        .result-score {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
        }
        
        .score-label {
          color: #64748b;
        }
        
        .score-value {
          color: #4f46e5;
          font-weight: 600;
        }
        
        .result-actions {
          display: flex;
          gap: 8px;
        }
        
        .copy-button {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .copy-button:hover {
          color: #cbd5e1;
          background: #374151;
        }
        
        .copied {
          color: #10b981 !important;
        }
        
        .result-content {
          color: #cbd5e1;
          line-height: 1.6;
          margin-bottom: 12px;
          white-space: pre-wrap;
        }
        
        .expand-button {
          background: none;
          border: none;
          color: #4f46e5;
          cursor: pointer;
          font-size: 12px;
          padding: 4px 0;
          margin-bottom: 12px;
        }
        
        .expand-button:hover {
          color: #6366f1;
        }
        
        .result-meta {
          border-top: 1px solid #334155;
          padding-top: 12px;
        }
        
        .metadata {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }
        
        .meta-item {
          font-size: 11px;
          color: #64748b;
          background: #0f172a;
          padding: 4px 8px;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
};

export default ResultList;
