import React from 'react';
import { FileText, ExternalLink, Clock } from 'lucide-react';
import type { ResultListProps, SearchResult } from '../types';

const ResultList: React.FC<ResultListProps> = ({ 
  results, 
  loading = false, 
  onResultClick 
}) => {
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
            background: #1a1a2e;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
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
        `}</style>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="no-results">
        <FileText size={48} className="no-results-icon" />
        <h3>No results found</h3>
        <p>Try adjusting your search query or check if documents have been ingested.</p>
        
        <style jsx>{`
          .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
          }
          
          .no-results-icon {
            margin-bottom: 16px;
            opacity: 0.5;
          }
          
          .no-results h3 {
            margin: 0 0 8px 0;
            color: #9ca3af;
          }
          
          .no-results p {
            margin: 0;
            font-size: 14px;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="result-list">
      <div className="results-header">
        <span className="results-count">{results.length} results</span>
      </div>
      
      <div className="results-container">
        {results.map((result, index) => (
          <ResultItem
            key={`${result.chunk_id}-${index}`}
            result={result}
            onClick={() => onResultClick?.(result)}
          />
        ))}
      </div>
      
      <style jsx>{`
        .result-list {
          padding: 20px;
        }
        
        .results-header {
          margin-bottom: 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid #374151;
        }
        
        .results-count {
          color: #9ca3af;
          font-size: 14px;
          font-weight: 500;
        }
        
        .results-container {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
      `}</style>
    </div>
  );
};

interface ResultItemProps {
  result: SearchResult;
  onClick?: () => void;
}

const ResultItem: React.FC<ResultItemProps> = ({ result, onClick }) => {
  const formatScore = (score: number) => Math.round(score * 100);
  
  return (
    <div className="result-item" onClick={onClick}>
      <div className="result-header">
        <div className="result-source">
          <FileText size={16} />
          <span className="source-name">{result.source_file}</span>
          <ExternalLink size={14} className="external-link" />
        </div>
        <div className="result-score">
          {formatScore(result.similarity_score)}%
        </div>
      </div>
      
      <div className="result-content">
        {result.content}
      </div>
      
      {result.metadata && Object.keys(result.metadata).length > 0 && (
        <div className="result-metadata">
          <Clock size={12} />
          {result.metadata.page && <span>Page {result.metadata.page}</span>}
          {result.metadata.section && <span>• {result.metadata.section}</span>}
        </div>
      )}
      
      <style jsx>{`
        .result-item {
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 8px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .result-item:hover {
          border-color: #4f46e5;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
        }
        
        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        
        .result-source {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
          font-size: 14px;
        }
        
        .source-name {
          font-weight: 500;
          color: #d1d5db;
        }
        
        .external-link {
          opacity: 0.6;
        }
        
        .result-score {
          background: #4f46e5;
          color: white;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }
        
        .result-content {
          color: #f3f4f6;
          line-height: 1.6;
          margin-bottom: 12px;
          font-size: 15px;
        }
        
        .result-metadata {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #6b7280;
          font-size: 12px;
        }
      `}</style>
    </div>
  );
};

export default ResultList;
