import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, 
  User, 
  Bot, 
  Loader2, 
  FileText, 
  Clock, 
  Copy, 
  CheckCircle, 
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Brain
} from 'lucide-react';
import type { ChatUIProps, ChatMessage, SearchResult } from '../types';

const ChatUI: React.FC<ChatUIProps> = ({ 
  onSendMessage, 
  messages, 
  loading = false,
  onStreamMessage 
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(true);
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [inputMessage]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !loading) {
      setError(null);
      if (useStreaming && onStreamMessage) {
        onStreamMessage(inputMessage.trim());
      } else {
        onSendMessage(inputMessage.trim());
      }
      setInputMessage('');
    }
  }, [inputMessage, loading, onSendMessage, onStreamMessage, useStreaming]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

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

  return (
    <div className="chat-ui">
      <div className="chat-messages">
        {error && (
          <div className="error-message">
            <AlertTriangle size={16} />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="dismiss-error">✕</button>
          </div>
        )}
        
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <Bot size={48} className="welcome-icon" />
            <h3>Ask me anything about your documents</h3>
            <p>I'll search through your corpus and provide contextual answers with source citations.</p>
            <div className="welcome-features">
              <div className="feature-item">
                <FileText size={16} />
                <span>Source citations</span>
              </div>
              <div className="feature-item">
                <Clock size={16} />
                <span>Real-time streaming</span>
              </div>
              <div className="feature-item">
                <Brain size={16} />
                <span>RAG-enhanced responses</span>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage 
              key={`${message.timestamp}-${index}`} 
              message={message} 
              onCopy={copyToClipboard}
              copiedStates={copiedStates}
            />
          ))
        )}
        
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <Loader2 size={16} className="spinning" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-controls">
        <label className="streaming-toggle">
          <input
            type="checkbox"
            checked={useStreaming}
            onChange={(e) => setUseStreaming(e.target.checked)}
          />
          <span>Enable streaming responses</span>
        </label>
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-container">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            className="chat-input"
            rows={1}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="send-button"
            title="Send message (Enter)"
          >
            {loading ? <Loader2 size={18} className="spinning" /> : <Send size={18} />}
          </button>
        </div>
      </form>
      
      <style jsx>{`
        .chat-ui {
          display: flex;
          flex-direction: column;
          height: 100%;
          max-height: 600px;
          background: #0f172a;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          scrollbar-width: thin;
          scrollbar-color: #374151 transparent;
        }
        
        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
          background: transparent;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
          background: #374151;
          border-radius: 3px;
        }
        
        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #ef4444;
          color: white;
          border-radius: 8px;
          font-size: 14px;
        }
        
        .dismiss-error {
          background: none;
          border: none;
          color: white;
          cursor: pointer;
          margin-left: auto;
          padding: 0;
          font-size: 16px;
          opacity: 0.8;
        }
        
        .dismiss-error:hover {
          opacity: 1;
        }
        
        .chat-welcome {
          text-align: center;
          padding: 40px 20px;
          color: #cbd5e1;
        }
        
        .welcome-icon {
          margin-bottom: 16px;
          opacity: 0.7;
          color: #4f46e5;
        }
        
        .chat-welcome h3 {
          margin: 0 0 8px 0;
          color: #f1f5f9;
          font-size: 20px;
          font-weight: 600;
        }
        
        .chat-welcome p {
          margin: 0 0 24px 0;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .welcome-features {
          display: flex;
          justify-content: center;
          gap: 24px;
          flex-wrap: wrap;
        }
        
        .feature-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: #94a3b8;
        }
        
        .feature-item svg {
          color: #4f46e5;
        }
        
        .chat-controls {
          padding: 12px 20px;
          border-top: 1px solid #1e293b;
          background: #0f172a;
        }
        
        .streaming-toggle {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #cbd5e1;
          cursor: pointer;
        }
        
        .streaming-toggle input[type="checkbox"] {
          accent-color: #4f46e5;
        }
        
        .chat-input-form {
          padding: 16px 20px;
          border-top: 1px solid #1e293b;
          background: #0f172a;
        }
        
        .chat-input-container {
          display: flex;
          align-items: flex-end;
          gap: 12px;
          background: #1e293b;
          border: 2px solid #334155;
          border-radius: 12px;
          padding: 8px 12px;
          transition: all 0.2s ease;
        }
        
        .chat-input-container:focus-within {
          border-color: #4f46e5;
          box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .chat-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: #f1f5f9;
          font-size: 14px;
          line-height: 1.5;
          resize: none;
          min-height: 20px;
          max-height: 120px;
          padding: 8px 0;
          font-family: inherit;
        }
        
        .chat-input::placeholder {
          color: #64748b;
        }
        
        .send-button {
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          min-width: 36px;
          height: 36px;
        }
        
        .send-button:hover:not(:disabled) {
          background: #4338ca;
          transform: translateY(-1px);
        }
        
        .send-button:disabled {
          background: #374151;
          cursor: not-allowed;
          transform: none;
        }
        
        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #64748b;
          font-style: italic;
        }
        
        .spinning {
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

interface ChatMessageProps {
  message: ChatMessage;
  onCopy: (text: string, id: string) => void;
  copiedStates: Record<string, boolean>;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onCopy, copiedStates }) => {
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const isUser = message.role === 'user';
  const messageId = `${message.timestamp}-${message.role}`;
  
  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="message-content-wrapper">
        <div className="message-content">
          {message.content}
        </div>
        
        {message.sources && message.sources.length > 0 && (
          <div className="message-sources">
            <button 
              className="sources-toggle"
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
            >
              <FileText size={14} />
              <span>{message.sources.length} source{message.sources.length > 1 ? 's' : ''}</span>
              {sourcesExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            
            {sourcesExpanded && (
              <div className="sources-list">
                {message.sources.map((source, index) => (
                  <SourceCard key={source.chunk_id || index} source={source} onCopy={onCopy} copiedStates={copiedStates} />
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="message-meta">
          <span className="message-timestamp">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
          {message.response_time_ms && (
            <span className="response-time">
              <Clock size={12} />
              {message.response_time_ms.toFixed(0)}ms
            </span>
          )}
          <button
            className="copy-button"
            onClick={() => onCopy(message.content, messageId)}
            title="Copy message"
          >
            {copiedStates[messageId] ? (
              <CheckCircle size={14} className="copied" />
            ) : (
              <Copy size={14} />
            )}
          </button>
        </div>
      </div>
      
      <style jsx>{`
        .message {
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }
        
        .message.user {
          flex-direction: row-reverse;
        }
        
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .message.user .message-avatar {
          background: #4f46e5;
          color: white;
        }
        
        .message.assistant .message-avatar {
          background: #374151;
          color: #9ca3af;
        }
        
        .message-content-wrapper {
          max-width: 70%;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .message.user .message-content-wrapper {
          align-items: flex-end;
        }
        
        .message-content {
          background: #1e293b;
          padding: 12px 16px;
          border-radius: 16px;
          word-wrap: break-word;
          line-height: 1.5;
          color: #f1f5f9;
          white-space: pre-wrap;
        }
        
        .message.user .message-content {
          background: #4f46e5;
          color: white;
        }
        
        .message-sources {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .sources-toggle {
          display: flex;
          align-items: center;
          gap: 6px;
          background: #334155;
          color: #cbd5e1;
          border: none;
          padding: 6px 12px;
          border-radius: 8px;
          font-size: 12px;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }
        
        .sources-toggle:hover {
          background: #475569;
        }
        
        .sources-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        
        .message-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          color: #64748b;
        }
        
        .message.user .message-meta {
          flex-direction: row-reverse;
        }
        
        .response-time {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .copy-button {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 2px;
          border-radius: 4px;
          transition: color 0.2s ease;
        }
        
        .copy-button:hover {
          color: #cbd5e1;
        }
        
        .copied {
          color: #10b981 !important;
        }
      `}</style>
    </div>
  );
};

interface SourceCardProps {
  source: SearchResult;
  onCopy: (text: string, id: string) => void;
  copiedStates: Record<string, boolean>;
}

const SourceCard: React.FC<SourceCardProps> = ({ source, onCopy, copiedStates }) => {
  const [expanded, setExpanded] = useState(false);
  const sourceId = `source-${source.chunk_id}`;
  const displayContent = expanded ? source.content : `${source.content.slice(0, 150)}${source.content.length > 150 ? '...' : ''}`;
  
  return (
    <div className="source-card">
      <div className="source-header">
        <div className="source-info">
          <span className="source-file">{source.source_file}</span>
          <span className="similarity-score">
            {(source.similarity_score * 100).toFixed(1)}% match
          </span>
        </div>
        <div className="source-actions">
          <button
            className="copy-source-button"
            onClick={() => onCopy(source.content, sourceId)}
            title="Copy source content"
          >
            {copiedStates[sourceId] ? (
              <CheckCircle size={12} className="copied" />
            ) : (
              <Copy size={12} />
            )}
          </button>
        </div>
      </div>
      
      <div className="source-content">
        {displayContent}
      </div>
      
      {source.content.length > 150 && (
        <button 
          className="expand-button"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
      
      <style jsx>{`
        .source-card {
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
          padding: 12px;
          font-size: 12px;
        }
        
        .source-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .source-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        
        .source-file {
          color: #f1f5f9;
          font-weight: 500;
        }
        
        .similarity-score {
          color: #64748b;
          font-size: 11px;
        }
        
        .source-actions {
          display: flex;
          gap: 4px;
        }
        
        .copy-source-button {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: color 0.2s ease;
        }
        
        .copy-source-button:hover {
          color: #cbd5e1;
        }
        
        .source-content {
          color: #cbd5e1;
          line-height: 1.4;
          margin-bottom: 8px;
        }
        
        .expand-button {
          background: none;
          border: none;
          color: #4f46e5;
          cursor: pointer;
          font-size: 11px;
          padding: 0;
        }
        
        .expand-button:hover {
          color: #6366f1;
        }
        
        .copied {
          color: #10b981 !important;
        }
      `}</style>
    </div>
  );
};

export default ChatUI;