import React, { useState, useEffect } from 'react';
import {
  Search,
  MessageSquare,
  Files,
  Database,
  Brain,
  Folder,
  Globe
} from 'lucide-react';

import SearchBar from './components/SearchBar';
import ResultList from './components/ResultList';
import ChatUI from './components/ChatUI';
import FileViewer from './components/FileViewer';
import ErrorBoundary from './components/ErrorBoundary';

import { queryApi, ingestApi } from './api';
import type {
  SearchResult,
  ChatMessage,
  FileInfo,
  SearchMode,
  CorpusStatus
} from './types';

const App: React.FC = () => {
  // State management
  const [currentMode, setCurrentMode] = useState<SearchMode>('semantic');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [corpusStatus, setCorpusStatus] = useState<CorpusStatus | null>(null);
    // Loading states
  const [isSearching, setIsSearching] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);

  // Load corpus status on mount
  useEffect(() => {
    loadCorpusStatus();
  }, []);

  const loadCorpusStatus = async () => {
    try {
      setIsLoadingStatus(true);
      const status = await ingestApi.getStatus();
      setCorpusStatus(status);
    } catch (error) {
      console.error('Failed to load corpus status:', error);
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const handleSearch = async (query: string) => {
    try {
      setIsSearching(true);
      const response = await queryApi.search({
        query,
        limit: 20,
        similarity_threshold: 0.5
      });
      setSearchResults(response.results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleChatMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMessage]);

    try {
      setIsChatting(true);
      const response = await queryApi.chat({
        message,
        history: chatMessages,
        use_rag: true
      });
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        sources: response.sources,
        response_time_ms: response.response_time_ms
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat failed:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatting(false);
    }
  };

  const handleStreamMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };    setChatMessages(prev => [...prev, userMessage]);

    // Create placeholder assistant message that will be updated
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, assistantMessage]);    try {
      setIsChatting(true);
      let fullResponse = '';
      let responseTimeMs = 0;

      await queryApi.chatStream(
        {
          message,
          history: chatMessages,
          use_rag: true
        },
        // onChunk
        (chunk: string) => {
          fullResponse += chunk;
          setChatMessages(prev => 
            prev.map((msg, index) => 
              index === prev.length - 1 
                ? { ...msg, content: fullResponse }
                : msg
            )
          );
        },
        // onSources
        (streamSources: SearchResult[]) => {
          setChatMessages(prev => 
            prev.map((msg, index) => 
              index === prev.length - 1 
                ? { ...msg, sources: streamSources }
                : msg
            )
          );
        },
        // onError
        (error: string) => {
          console.error('Streaming error:', error);
          setChatMessages(prev => 
            prev.map((msg, index) => 
              index === prev.length - 1 
                ? { ...msg, content: `Error: ${error}` }
                : msg
            )
          );
        },
        // onComplete
        (metadata: any) => {
          responseTimeMs = metadata.response_time_ms;
          setChatMessages(prev => 
            prev.map((msg, index) => 
              index === prev.length - 1 
                ? { ...msg, response_time_ms: responseTimeMs }
                : msg
            )
          );
        }
      );
    } catch (error) {
      console.error('Streaming chat failed:', error);
      setChatMessages(prev => 
        prev.map((msg, index) => 
          index === prev.length - 1 
            ? { ...msg, content: 'Sorry, I encountered an error processing your request. Please try again.' }
            : msg
        )
      );
    } finally {
      setIsChatting(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    // TODO: Implement result click handling
    console.log('Result clicked:', result);
  };

  return (
    <ErrorBoundary>
      <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Brain size={24} />
            <h1>Ashurbanipal</h1>
          </div>
            <div className="header-info">
            {isLoadingStatus ? (
              <div className="corpus-stats">
                <Database size={16} />
                <span>Loading...</span>
              </div>
            ) : corpusStatus ? (
              <div className="corpus-stats">
                <Database size={16} />
                <span>{corpusStatus.total_documents} docs</span>
                <span>•</span>
                <span>{corpusStatus.total_chunks} chunks</span>
              </div>
            ) : (
              <div className="corpus-stats">
                <Database size={16} />
                <span>No corpus data</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="app-nav">
        <button
          className={`nav-item ${currentMode === 'semantic' ? 'active' : ''}`}
          onClick={() => setCurrentMode('semantic')}
        >
          <Search size={20} />
          <span>Search</span>
        </button>
        <button
          className={`nav-item ${currentMode === 'chat' ? 'active' : ''}`}
          onClick={() => setCurrentMode('chat')}
        >
          <MessageSquare size={20} />
          <span>Chat</span>
        </button>
        <button
          className={`nav-item ${currentMode === 'files' ? 'active' : ''}`}
          onClick={() => setCurrentMode('files')}
        >
          <Files size={20} />
          <span>Files</span>
        </button>
      </nav>

      {/* Main Content */}
      <main className="app-main">
        {currentMode === 'semantic' && (
          <div className="search-mode">
            <div className="search-header">
              <SearchBar onSearch={handleSearch} loading={isSearching} />
            </div>
            <div className="search-results">              <ResultList
                results={searchResults}
                loading={isSearching}
                onResultClick={(result) => {
                  handleResultClick(result);
                  // If the result has file info, we could open it
                  if (result.source_file) {
                    // For now, just console log, but this could trigger file opening
                    console.log('Opening file:', result.source_file);
                  }
                }}
              />
            </div>
          </div>
        )}        {currentMode === 'chat' && (
          <div className="chat-mode">
            <ChatUI
              onSendMessage={handleChatMessage}
              onStreamMessage={handleStreamMessage}
              messages={chatMessages}
              loading={isChatting}
            />
          </div>
        )}

        {currentMode === 'files' && (
          <div className="files-mode">
            <div className="coming-soon">
              <Files size={48} />
              <h3>File Management</h3>
              <p>File browser and management coming soon...</p>
            </div>
          </div>
        )}
      </main>

      {/* Quick Actions Sidebar */}
      <aside className="quick-actions">
        <h3>Quick Actions</h3>
        <button className="action-button">
          <Folder size={16} />
          <span>Ingest Folder</span>
        </button>
        <button className="action-button">
          <Globe size={16} />
          <span>Research Session</span>
        </button>
        <button className="action-button" onClick={loadCorpusStatus}>
          <Database size={16} />
          <span>Refresh Status</span>
        </button>
      </aside>

      {/* File Viewer Modal */}
      {selectedFile && (
        <FileViewer
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
        />
      )}

      <style jsx>{`
        .app {
          min-height: 100vh;
          background: #0f0f23;
          color: #cccccc;
          display: grid;
          grid-template-areas:
            "header header header"
            "nav main sidebar"
            "nav main sidebar";
          grid-template-columns: 200px 1fr 250px;
          grid-template-rows: auto 60px 1fr;
          gap: 1px;
          background: #374151;
        }

        .app-header {
          grid-area: header;
          background: #1a1a2e;
          padding: 16px 24px;
          border-bottom: 1px solid #374151;
        }

        .header-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
          max-width: 1400px;
          margin: 0 auto;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #4f46e5;
        }

        .logo h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 700;
          color: #f3f4f6;
        }

        .header-info {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .corpus-stats {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
          font-size: 14px;
        }

        .app-nav {
          grid-area: nav;
          background: #1a1a2e;
          padding: 20px 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 20px;
          background: transparent;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          text-align: left;
          transition: all 0.2s ease;
          font-size: 14px;
        }

        .nav-item:hover {
          background: rgba(79, 70, 229, 0.1);
          color: #d1d5db;
        }

        .nav-item.active {
          background: rgba(79, 70, 229, 0.2);
          color: #4f46e5;
          border-right: 3px solid #4f46e5;
        }

        .app-main {
          grid-area: main;
          background: #0f0f23;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .search-mode,
        .chat-mode,
        .files-mode {
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .search-header {
          padding: 24px;
          border-bottom: 1px solid #374151;
        }

        .search-results {
          flex: 1;
          overflow: auto;
        }

        .coming-soon {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #6b7280;
          text-align: center;
        }

        .coming-soon h3 {
          margin: 16px 0 8px 0;
          color: #9ca3af;
        }

        .quick-actions {
          grid-area: sidebar;
          background: #1a1a2e;
          padding: 20px;
        }

        .quick-actions h3 {
          margin: 0 0 16px 0;
          color: #d1d5db;
          font-size: 16px;
          font-weight: 600;
        }

        .action-button {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          background: transparent;
          border: 1px solid #374151;
          border-radius: 8px;
          color: #9ca3af;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-bottom: 8px;
          font-size: 14px;
        }

        .action-button:hover {
          background: rgba(79, 70, 229, 0.1);
          border-color: #4f46e5;
          color: #d1d5db;
        }

        @media (max-width: 768px) {
          .app {
            grid-template-areas:
              "header"
              "nav"
              "main";
            grid-template-columns: 1fr;
            grid-template-rows: auto auto 1fr;
          }

          .app-nav {
            flex-direction: row;
            padding: 12px 20px;
            overflow-x: auto;
          }

          .nav-item {
            flex-shrink: 0;
            border-right: none;
            border-radius: 8px;
          }

          .nav-item.active {
            border-right: none;
            border-bottom: 3px solid #4f46e5;
          }

          .quick-actions {
            display: none;
          }        }
      `}</style>
    </div>
    </ErrorBoundary>
  );
};

export default App;
