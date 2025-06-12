import React, { useState, useEffect } from 'react';
import {
  Search,
  MessageSquare,
  Database,
  Brain,
  FolderOpen,
  Plus,
  FileText,
  Settings,
  FolderPlus,
  Home
} from 'lucide-react';

import SearchBar from './components/SearchBar';
import ResultList from './components/ResultList';
import ChatUI from './components/ChatUI';
import FileViewer, { FileUpload, FileBrowser, FileContentViewer } from './components/FileViewer';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import BrowserAutomation from './components/BrowserAutomation';
import ErrorBoundary from './components/ErrorBoundary';

import { queryApi, ingestApi, filesApi, projectsApi } from './api';
import type {
  SearchResult,
  ChatMessage,
  FileInfo,
  CorpusStatus
} from './types';
import type { ResearchProject } from './api';

type MainTab = 'browser' | 'workspace';
type WorkspaceMode = 'search' | 'chat';

const App: React.FC = () => {
  // Main tab state (Ableton-style)
  const [activeTab, setActiveTab] = useState<MainTab>('browser');
  
  // Workspace modes (search and chat only)
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('search');
    // Research projects state
  const [currentProject, setCurrentProject] = useState<string>('default');  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [showProjectSelect, setShowProjectSelect] = useState(false);  const [showNewProject, setShowNewProject] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAddFiles, setShowAddFiles] = useState(false);
  const [allFiles, setAllFiles] = useState<FileInfo[]>([]);
  const [projectFormData, setProjectFormData] = useState({
    name: '',
    description: ''
  });
    // File browser state  
  const [browserSearchTerm, setBrowserSearchTerm] = useState<string>('');
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  
  // State management
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [corpusStatus, setCorpusStatus] = useState<CorpusStatus | null>(null);
    // File management state
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [fileContent, setFileContent] = useState<string>('');
    // Loading states
  const [isSearching, setIsSearching] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);  // Load corpus status on mount
  useEffect(() => {
    loadCorpusStatus();
    loadFiles();
    loadProjects();
  }, []);

  // Load projects when current project changes
  useEffect(() => {
    if (currentProject) {
      loadProjectFiles();
    }
  }, [currentProject]);

  // Keyboard shortcuts for tab switching
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '1':
            event.preventDefault();
            setActiveTab('browser');
            break;
          case '2':
            event.preventDefault();
            setActiveTab('workspace');
            break;
          case 'b':
            event.preventDefault();
            setActiveTab('browser');
            break;
          case 'w':
            event.preventDefault();
            setActiveTab('workspace');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
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

  const loadProjects = async () => {
    try {
      const projectsList = await projectsApi.list();
      setProjects(projectsList);
      
      // Set current project to default if none selected
      if (!currentProject && projectsList.length > 0) {
        setCurrentProject(projectsList[0].id);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };
  const loadFiles = async () => {
    try {
      const response = await filesApi.list(50, 0);
      setAllFiles(response.files);
    } catch (error) {
      console.error('Failed to load files:', error);
    }
  };

  const loadProjectFiles = async () => {
    if (!currentProject) return;
    
    try {
      const projectFiles = await projectsApi.getFiles(currentProject);
      // Update files display based on current project
      setFiles(projectFiles.files || []);
    } catch (error) {
      console.error('Failed to load project files:', error);
      // Fallback to all files if project files fail
      loadFiles();
    }
  };

  const handleCreateProject = async () => {
    try {
      if (!projectFormData.name.trim()) {
        alert('Project name is required');
        return;
      }

      const newProject = await projectsApi.create({
        name: projectFormData.name,
        description: projectFormData.description
      });

      // Refresh projects and select the new one
      await loadProjects();
      setCurrentProject(newProject.id);
      
      // Reset form and close modal
      setProjectFormData({ name: '', description: '' });
      setShowNewProject(false);
    } catch (error) {
      console.error('Failed to create project:', error);      alert('Failed to create project. Please try again.');
    }
  };

  const handleAddFilesToProject = async (filenames: string[]) => {
    if (!currentProject) return;
    
    try {
      for (const filename of filenames) {
        await projectsApi.addFile(currentProject, filename);
      }
      
      // Refresh project files
      await loadProjectFiles();
      setShowAddFiles(false);
    } catch (error) {
      console.error('Failed to add files to project:', error);
      alert('Failed to add files to project. Please try again.');
    }
  };const handleFileUpload = async (fileList: FileList) => {
    try {
      setUploadingFiles(true);
      
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        await ingestApi.ingestFile(file);
        
        // Add file to current project
        if (currentProject) {
          try {
            await projectsApi.addFile(currentProject, file.name);
          } catch (error) {
            console.error(`Failed to add file ${file.name} to project:`, error);
          }
        }
      }
      
      // Refresh files list and corpus status
      await loadProjectFiles();
      await loadCorpusStatus();
      setShowFileUpload(false);
    } catch (error) {
      console.error('File upload failed:', error);
    } finally {
      setUploadingFiles(false);
    }
  };  const handleFolderIngest = async (folderPath: string) => {
    try {
      setUploadingFiles(true);
      
      const result = await ingestApi.ingestFolder({
        folder_path: folderPath,
        file_types: ['.pdf', '.txt', '.md', '.docx'],
        recursive: true
      });
      
      console.log(`Folder ingestion completed: ${result.files_processed} files processed`);
      
      // Note: We can't automatically add files to project from folder ingestion
      // since the API doesn't return the list of processed filenames
      // Users will need to manually assign files to projects after folder ingestion
      
      // Refresh files list and corpus status
      await loadProjectFiles();
      await loadCorpusStatus();
      setShowFileUpload(false);
    } catch (error) {
      console.error('Folder ingestion failed:', error);
    } finally {
      setUploadingFiles(false);
    }
  };
  const handleFileSelect = async (file: FileInfo) => {
    try {
      // Load file content for viewing
      const contentData = await filesApi.getContent(file.filename);
      setFileContent(contentData.content || 'Content not available');
      setSelectedFile(file);
    } catch (error) {
      console.error('Failed to load file content:', error);
      setFileContent('Error loading file content');
      setSelectedFile(file);
    }
  };  const handleFileDelete = async (filename: string) => {
    try {
      await filesApi.delete(filename);
      await loadFiles();
      await loadCorpusStatus();
    } catch (error) {
      console.error('Failed to delete file:', error);
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
  };  const handleResultClick = (result: SearchResult) => {
    // TODO: Implement result click handling
    console.log('Result clicked:', result);
  };

  return (
    <ErrorBoundary>
      <div className="app">        {/* Main Tabs (Ableton-style) */}
        <div className="main-tabs">
          <button
            className={`main-tab ${activeTab === 'browser' ? 'active' : ''}`}
            onClick={() => setActiveTab('browser')}
            title="Project Browser (Ctrl/Cmd+1 or Ctrl/Cmd+B)"
          >
            <FolderOpen size={20} />
            <span>Browser</span>
          </button>
          <button
            className={`main-tab ${activeTab === 'workspace' ? 'active' : ''}`}
            onClick={() => setActiveTab('workspace')}
            title="Research Workspace (Ctrl/Cmd+2 or Ctrl/Cmd+W)"
          >
            <Brain size={20} />
            <span>Workspace</span>
          </button>
            {/* Settings Gear */}
          <button 
            className="settings-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="Settings & Analytics"
          >
            <Settings size={20} />
          </button>
          
          {/* Status Display */}
          <div className="status-display">
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
        </div>        {/* Content Area */}
        <div className="content-area">
          {activeTab === 'browser' ? (
            <div className="browser-view">
              {/* Main Corpus Browser */}
              <div className="corpus-browser">
                <div className="corpus-header">
                  <div className="header-left">
                    <h3>
                      {currentProject === 'default' 
                        ? 'Research Corpus' 
                        : `Project: ${projects.find(p => p.id === currentProject)?.name}`
                      }
                    </h3>
                    <span className="file-count">({files.length} files)</span>
                  </div>                  <div className="corpus-actions">
                    <button 
                      className="upload-btn primary"
                      onClick={() => setShowFileUpload(true)}
                      title="Add files to corpus"
                    >
                      <Plus size={16} />
                      Add Files
                    </button>
                    
                    {currentProject !== 'default' && (
                      <button 
                        className="add-files-btn"
                        onClick={() => setShowAddFiles(true)}
                        title="Add existing files to project"
                      >
                        <Plus size={16} />
                        Add to Project
                      </button>
                    )}
                    
                    <button 
                      className="project-btn"
                      onClick={() => setShowProjectSelect(!showProjectSelect)}
                      title="Switch between corpus and projects"
                    >
                      <Home size={16} />
                      {currentProject === 'default' ? 'Projects' : 'Corpus'}
                    </button>
                  </div>
                </div>                <FileBrowser
                  files={files}
                  onFileSelect={(file) => {
                    handleFileSelect(file);
                    setActiveTab('workspace'); // Switch to workspace when opening file
                  }}
                  onFileDelete={handleFileDelete}
                  searchTerm={browserSearchTerm}
                  onSearchChange={setBrowserSearchTerm}
                />
                
                {/* Project Selector Dropdown */}
                {showProjectSelect && (
                  <div className="project-dropdown">
                    <div className="dropdown-header">
                      <span>Switch View</span>
                      <button 
                        className="close-dropdown"
                        onClick={() => setShowProjectSelect(false)}
                      >
                        <Plus size={16} style={{ transform: 'rotate(45deg)' }} />
                      </button>
                    </div>
                    
                    <div 
                      className={`project-option ${currentProject === 'default' ? 'active' : ''}`}
                      onClick={() => { 
                        setCurrentProject('default'); 
                        setShowProjectSelect(false); 
                      }}
                    >
                      <div className="project-info">
                        <span className="project-name">Research Corpus</span>
                        <span className="project-stats">All files • Main workspace</span>
                      </div>
                    </div>
                    
                    <div className="project-divider"></div>
                    
                    {projects.filter(p => p.id !== 'default').map((project) => (
                      <div 
                        key={project.id}
                        className={`project-option ${currentProject === project.id ? 'active' : ''}`}
                        onClick={() => { 
                          setCurrentProject(project.id); 
                          setShowProjectSelect(false); 
                        }}
                      >
                        <div className="project-info">
                          <span className="project-name">{project.name}</span>
                          <span className="project-stats">{project.filesCount} files • {project.chunksCount} chunks</span>
                        </div>
                      </div>
                    ))}
                    
                    <div className="project-divider"></div>
                    <div 
                      className="project-option new-project"
                      onClick={() => { 
                        setShowNewProject(true); 
                        setShowProjectSelect(false); 
                      }}
                    >
                      <FolderPlus size={16} />
                      <span>New Research Project</span>
                    </div>
                  </div>
                )}
              </div>

              {/* File Preview */}
              {selectedFile ? (
                <FileContentViewer
                  file={selectedFile}
                  content={fileContent}
                  onLineClick={(lineNumber) => {
                    setSelectedLine(lineNumber);
                    setActiveTab('workspace'); // Switch to workspace with line highlighted
                  }}
                  highlightLine={selectedLine || undefined}
                />              ) : (
                <div className="browser-welcome">
                  <div className="welcome-content">
                    <FolderOpen size={48} />
                    <h3>
                      {currentProject === 'default' 
                        ? 'Research Corpus Browser' 
                        : `Project: ${projects.find(p => p.id === currentProject)?.name || 'Unknown Project'}`
                      }
                    </h3>
                    <p>
                      {currentProject === 'default' 
                        ? 'Browse your entire research corpus. Upload documents or organize files into research projects. Click on any file to preview its contents or navigate directly to specific lines in the workspace.'
                        : 'Browse files in this research project. Add more files from your corpus or preview existing ones. Click on any file to view its contents in the workspace.'
                      }
                    </p>
                    <div className="welcome-features">
                      <div className="feature">
                        <FileText size={16} />
                        <span>Preview files with line numbers</span>
                      </div>
                      <div className="feature">
                        <Search size={16} />
                        <span>Search across {currentProject === 'default' ? 'entire corpus' : 'project files'}</span>
                      </div>
                      <div className="feature">
                        <Home size={16} />
                        <span>{currentProject === 'default' ? 'Organize into projects' : 'Part of larger corpus'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="workspace-view">              {/* Workspace Navigation - only search and chat */}
              <nav className="workspace-nav">
                <button
                  className={`nav-item ${workspaceMode === 'search' ? 'active' : ''}`}
                  onClick={() => setWorkspaceMode('search')}
                >
                  <Search size={18} />
                  <span>Search</span>
                </button>
                <button
                  className={`nav-item ${workspaceMode === 'chat' ? 'active' : ''}`}
                  onClick={() => setWorkspaceMode('chat')}
                >
                  <MessageSquare size={18} />
                  <span>Chat</span>
                </button>
              </nav>

              {/* Workspace Content */}
              <div className="workspace-content">
                {workspaceMode === 'search' && (
                  <div className="search-mode">
                    <div className="search-header">
                      <SearchBar onSearch={handleSearch} loading={isSearching} />
                    </div>
                    <div className="search-results">
                      <ResultList
                        results={searchResults}
                        loading={isSearching}
                        onResultClick={(result) => {
                          handleResultClick(result);
                          if (result.source_file) {
                            console.log('Opening file:', result.source_file);
                          }
                        }}
                      />
                    </div>
                  </div>
                )}

                {workspaceMode === 'chat' && (
                  <div className="chat-mode">
                    <ChatUI
                      onSendMessage={handleChatMessage}
                      onStreamMessage={handleStreamMessage}
                      messages={chatMessages}
                      loading={isChatting}
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* New Project Modal */}
        {showNewProject && (
          <div className="settings-overlay">
            <div className="new-project-modal">
              <div className="modal-header">
                <h3>Create New Research Project</h3>
                <button className="close-button" onClick={() => setShowNewProject(false)}>
                  <Plus size={20} style={{ transform: 'rotate(45deg)' }} />
                </button>
              </div>
              <div className="modal-content">                <div className="form-group">
                  <label>Project Name</label>
                  <input 
                    type="text" 
                    placeholder="Enter project name..."
                    className="project-input"
                    value={projectFormData.name}
                    onChange={(e) => setProjectFormData(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea 
                    placeholder="Brief description of your research project..."
                    className="project-textarea"
                    rows={3}
                    value={projectFormData.description}
                    onChange={(e) => setProjectFormData(prev => ({ ...prev, description: e.target.value }))}
                  ></textarea>
                </div>
                <div className="modal-actions">
                  <button 
                    className="cancel-btn"
                    onClick={() => {
                      setShowNewProject(false);
                      setProjectFormData({ name: '', description: '' });
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    className="create-btn"
                    onClick={handleCreateProject}
                    disabled={!projectFormData.name.trim()}
                  >
                    Create Project
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings Modal */}
        {showSettings && (
          <div className="settings-overlay">
            <div className="settings-modal">
              <div className="settings-header">
                <h3>Settings & Analytics</h3>
                <button className="close-button" onClick={() => setShowSettings(false)}>
                  <Plus size={20} style={{ transform: 'rotate(45deg)' }} />
                </button>
              </div>
              <div className="settings-content">
                <div className="settings-section">
                  <h4>Analytics Dashboard</h4>
                  <AnalyticsDashboard loading={isLoadingStatus} />
                </div>
                <div className="settings-section">
                  <h4>Browser Automation</h4>
                  <BrowserAutomation onSessionUpdate={() => {}} />
                </div>
              </div>
            </div>
          </div>        )}

        {/* Add Files to Project Modal */}
        {showAddFiles && (
          <AddFilesToProjectModal
            allFiles={allFiles}
            currentProjectFiles={files}
            onAddFiles={handleAddFilesToProject}
            onClose={() => setShowAddFiles(false)}
          />
        )}

        {/* File Upload Modal */}
        {showFileUpload && (
          <FileUpload
            onUpload={handleFileUpload}
            onFolderIngest={handleFolderIngest}
            uploading={uploadingFiles}
            onClose={() => setShowFileUpload(false)}
          />
        )}        {/* Full File Viewer Modal */}
        {selectedFile && activeTab === 'workspace' && (
          <FileViewer
            file={selectedFile}
            content={fileContent}
            onClose={() => {
              setSelectedFile(null);
              setFileContent('');
              setSelectedLine(null);
            }}
          />
        )}<style jsx>{`
        .app {
          min-height: 100vh;
          background: #0f0f23;
          color: #cccccc;
          display: flex;
          flex-direction: column;
        }

        /* Main Tabs (Ableton-style) */
        .main-tabs {
          display: flex;
          align-items: center;
          background: #1a1a2e;
          border-bottom: 1px solid #374151;
          padding: 0 20px;
          gap: 8px;
        }

        .main-tab {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          background: transparent;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          border-radius: 6px 6px 0 0;
          transition: all 0.2s ease;
          font-size: 14px;
          font-weight: 500;
        }

        .main-tab:hover {
          background: rgba(79, 70, 229, 0.1);
          color: #d1d5db;
        }        .main-tab.active {
          background: #0f0f23;
          color: #4f46e5;
          border-bottom: 2px solid #4f46e5;
        }

        .settings-btn {
          display: flex;
          align-items: center;
          padding: 8px;
          background: transparent;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.2s ease;
          margin-left: auto;
          margin-right: 16px;
        }

        .settings-btn:hover {
          background: rgba(79, 70, 229, 0.1);
          color: #d1d5db;
        }

        .project-selector {
          position: relative;
        }

        .project-dropdown-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid #374151;
          border-radius: 6px;
          color: #9ca3af;
          cursor: pointer;
          font-size: 13px;
          transition: all 0.2s ease;
        }

        .project-dropdown-btn:hover {
          background: rgba(79, 70, 229, 0.1);
          border-color: #4f46e5;
        }

        .project-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 6px;
          min-width: 280px;
          z-index: 100;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .project-option {
          padding: 12px 16px;
          cursor: pointer;
          border-bottom: 1px solid #374151;
          transition: background 0.2s ease;
        }

        .project-option:hover {
          background: rgba(79, 70, 229, 0.1);
        }

        .project-option.active {
          background: rgba(79, 70, 229, 0.2);
          border-left: 3px solid #4f46e5;
        }

        .project-option.new-project {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #4f46e5;
          font-weight: 500;
        }

        .project-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .project-name {
          color: #d1d5db;
          font-weight: 500;
          font-size: 14px;
        }

        .project-stats {
          color: #6b7280;
          font-size: 12px;
        }

        .project-divider {
          height: 1px;
          background: #374151;
          margin: 8px 0;
        }

        .folder-path {
          margin-left: auto;
          position: relative;
        }

        .folder-selector {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid #374151;
          border-radius: 6px;
          color: #9ca3af;
          cursor: pointer;
          font-size: 13px;
        }

        .folder-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 6px;
          min-width: 200px;
          z-index: 100;
          overflow: hidden;
        }        .folder-dropdown div {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          cursor: pointer;
          border-bottom: 1px solid #374151;
          transition: background 0.2s ease;
        }

        .folder-dropdown div:last-child {
          border-bottom: none;
        }

        .folder-dropdown div:hover {
          background: rgba(79, 70, 229, 0.1);
        }

        .folder-dropdown div svg {
          color: #6b7280;
          flex-shrink: 0;
        }

        .folder-dropdown div span {
          color: #d1d5db;
          font-size: 13px;
        }

        .status-display {
          margin-left: 16px;
        }

        .corpus-stats {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
          font-size: 13px;
        }

        /* Content Area */
        .content-area {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }        /* Browser View */
        .browser-view {
          display: flex;
          height: 100%;
          overflow: hidden;
        }

        .project-browser {
          width: 350px;
          background: #1a1a2e;
          border-right: 1px solid #374151;
          display: flex;
          flex-direction: column;
        }

        .settings-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .settings-modal {
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 12px;
          width: 100%;
          max-width: 1200px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .settings-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #374151;
        }

        .settings-header h3 {
          margin: 0;
          color: #f1f5f9;
          font-size: 18px;
          font-weight: 600;
        }

        .close-button {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.2s ease;
        }

        .close-button:hover {
          color: #cbd5e1;
          background: #374151;
        }

        .settings-content {
          flex: 1;
          overflow: auto;
          padding: 20px;
        }

        .settings-section {
          margin-bottom: 32px;
        }        .settings-section h4 {
          margin: 0 0 16px 0;
          color: #d1d5db;
          font-size: 16px;
          font-weight: 600;
          border-bottom: 1px solid #374151;
          padding-bottom: 8px;
        }

        .new-project-modal {
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 12px;
          width: 100%;
          max-width: 500px;
          display: flex;
          flex-direction: column;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #374151;
        }

        .modal-header h3 {
          margin: 0;
          color: #f1f5f9;
          font-size: 18px;
          font-weight: 600;
        }

        .modal-content {
          padding: 20px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          color: #d1d5db;
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 8px;
        }

        .project-input, .project-textarea {
          width: 100%;
          background: #0f0f23;
          border: 1px solid #374151;
          border-radius: 6px;
          padding: 12px;
          color: #d1d5db;
          font-size: 14px;
          resize: none;
        }

        .project-input:focus, .project-textarea:focus {
          outline: none;
          border-color: #4f46e5;
          box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
          margin-top: 20px;
        }

        .cancel-btn, .create-btn {
          padding: 10px 20px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: all 0.2s ease;
        }

        .cancel-btn {
          background: transparent;
          color: #6b7280;
          border: 1px solid #374151;
        }

        .cancel-btn:hover {
          background: #374151;
          color: #d1d5db;
        }

        .create-btn {
          background: #4f46e5;
          color: white;
        }        .create-btn:hover {
          background: #4338ca;
        }

        .create-btn:disabled {
          background: #374151;
          color: #6b7280;
          cursor: not-allowed;
        }        .create-btn:disabled:hover {
          background: #374151;
        }

        /* Corpus Browser Styles */
        .corpus-browser {
          width: 350px;
          background: #1a1a2e;
          border-right: 1px solid #374151;
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .corpus-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid #374151;
        }

        .corpus-actions {
          display: flex;
          gap: 8px;
        }

        .upload-btn.primary {
          background: #4f46e5;
          border: 1px solid #4f46e5;
          border-radius: 6px;
          color: white;
          padding: 8px 12px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          font-weight: 500;
        }

        .upload-btn.primary:hover {
          background: #4338ca;
          border-color: #4338ca;
        }

        .project-btn {
          background: rgba(79, 70, 229, 0.1);
          border: 1px solid #4f46e5;
          border-radius: 6px;
          color: #4f46e5;
          padding: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .project-btn:hover {
          background: rgba(79, 70, 229, 0.2);
        }

        .browser-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid #374151;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }        .browser-header h3 {
          margin: 0;
          color: #d1d5db;
          font-size: 16px;
          font-weight: 600;
        }

        .file-count {
          color: #6b7280;
          font-size: 13px;
          font-weight: 400;
        }

        .add-files-btn {
          background: rgba(79, 70, 229, 0.1);
          border: 1px solid #4f46e5;
          border-radius: 6px;
          color: #4f46e5;
          padding: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }        .add-files-btn:hover {
          background: rgba(79, 70, 229, 0.2);
        }

        .project-dropdown {
          position: absolute;
          top: 100%;
          right: 20px;
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 6px;
          min-width: 300px;
          z-index: 100;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .dropdown-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: #0f0f23;
          border-bottom: 1px solid #374151;
          color: #d1d5db;
          font-weight: 500;
        }

        .close-dropdown {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 4px;
          border-radius: 3px;
          transition: all 0.2s ease;
        }

        .close-dropdown:hover {
          color: #cbd5e1;
          background: #374151;
        }

        .browser-welcome {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0f0f23;
          padding: 40px 20px;
        }

        .welcome-content {
          text-align: center;
          max-width: 400px;
        }

        .welcome-content svg:first-child {
          color: #4f46e5;
          margin-bottom: 20px;
          opacity: 0.8;
        }

        .welcome-content h3 {
          margin: 0 0 16px 0;
          color: #f1f5f9;
          font-size: 20px;
          font-weight: 600;
        }

        .welcome-content > p {
          color: #9ca3af;
          margin: 0 0 32px 0;
          line-height: 1.6;
          font-size: 14px;
        }

        .welcome-features {
          display: flex;
          flex-direction: column;
          gap: 16px;
          text-align: left;
        }

        .feature {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 8px;
          transition: all 0.2s ease;
        }

        .feature:hover {
          background: rgba(79, 70, 229, 0.1);
          border-color: #4f46e5;
        }

        .feature svg {
          color: #4f46e5;
          flex-shrink: 0;
        }

        .feature span {
          color: #d1d5db;
          font-size: 13px;
          line-height: 1.4;
        }

        /* Workspace View */
        .workspace-view {
          display: flex;
          flex-direction: column;
          height: 100%;
        }

        .workspace-nav {
          display: flex;
          background: #1a1a2e;
          border-bottom: 1px solid #374151;
          padding: 0 20px;
        }

        .workspace-nav .nav-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 14px 20px;
          background: transparent;
          border: none;
          color: #9ca3af;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          border-bottom: 2px solid transparent;
        }

        .workspace-nav .nav-item:hover {
          background: rgba(79, 70, 229, 0.1);
          color: #d1d5db;
        }

        .workspace-nav .nav-item.active {
          color: #4f46e5;
          border-bottom-color: #4f46e5;
        }

        .workspace-content {
          flex: 1;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        /* Mode Styles */
        .search-mode,
        .chat-mode,
        .analytics-mode,
        .browser-mode {
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
        }        @media (max-width: 768px) {
          .browser-view {
            flex-direction: column;
          }

          .project-browser {
            width: 100%;
            height: 300px;
          }

          .main-tabs {
            flex-wrap: wrap;
            padding: 8px 16px;
          }

          .project-selector {
            margin-left: 0;
            margin-top: 8px;
          }

          .settings-btn {
            margin-left: 8px;
            margin-right: 0;
          }
        }
      `}</style>
    </div>
    </ErrorBoundary>  );
};

// Add Files to Project Modal Component
interface AddFilesToProjectModalProps {
  allFiles: FileInfo[];
  currentProjectFiles: FileInfo[];
  onAddFiles: (filenames: string[]) => void;
  onClose: () => void;
}

const AddFilesToProjectModal: React.FC<AddFilesToProjectModalProps> = ({
  allFiles,
  currentProjectFiles,
  onAddFiles,
  onClose
}) => {
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Get files that are not already in the current project
  const currentProjectFileNames = new Set(currentProjectFiles.map(f => f.filename));
  const availableFiles = allFiles.filter(file => !currentProjectFileNames.has(file.filename));
  
  // Filter available files by search term
  const filteredFiles = availableFiles.filter(file =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleFileToggle = (filename: string) => {
    setSelectedFiles(prev => 
      prev.includes(filename) 
        ? prev.filter(f => f !== filename)
        : [...prev, filename]
    );
  };

  const handleAddFiles = () => {
    if (selectedFiles.length > 0) {
      onAddFiles(selectedFiles);
    }
  };

  return (
    <div className="settings-overlay">
      <div className="add-files-modal">
        <div className="modal-header">
          <h3>Add Files to Project</h3>
          <button className="close-button" onClick={onClose}>
            <Plus size={20} style={{ transform: 'rotate(45deg)' }} />
          </button>
        </div>
        
        <div className="modal-content">
          <div className="search-section">
            <input
              type="text"
              placeholder="Search available files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="files-section">
            <div className="section-header">
              <span>Available Files ({filteredFiles.length})</span>
              {selectedFiles.length > 0 && (
                <span className="selected-count">{selectedFiles.length} selected</span>
              )}
            </div>
            
            <div className="files-list">
              {filteredFiles.length === 0 ? (
                <div className="no-files">
                  {searchTerm ? 'No files match your search' : 'All files are already in this project'}
                </div>
              ) : (
                filteredFiles.map((file) => (
                  <div key={file.filename} className="file-item">
                    <input
                      type="checkbox"
                      id={`file-${file.filename}`}
                      checked={selectedFiles.includes(file.filename)}
                      onChange={() => handleFileToggle(file.filename)}
                      className="file-checkbox"
                    />
                    <label htmlFor={`file-${file.filename}`} className="file-label">
                      <FileText size={16} />
                      <div className="file-info">
                        <span className="file-name">{file.filename}</span>
                        <span className="file-meta">
                          {file.chunks_count || 0} chunks • {Math.round((file.size || 0) / 1024)} KB
                        </span>
                      </div>
                    </label>
                  </div>
                ))
              )}
            </div>
          </div>
          
          <div className="modal-actions">
            <button className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button 
              className="add-btn"
              onClick={handleAddFiles}
              disabled={selectedFiles.length === 0}
            >
              Add {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
        
        <style jsx>{`
          .add-files-modal {
            background: #1a1a2e;
            border: 1px solid #374151;
            border-radius: 12px;
            width: 100%;
            max-width: 600px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
          }
          
          .search-section {
            padding: 16px 0;
          }
          
          .search-input {
            width: 100%;
            background: #0f0f23;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 12px;
            color: #d1d5db;
            font-size: 14px;
          }
          
          .search-input:focus {
            outline: none;
            border-color: #4f46e5;
          }
          
          .files-section {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
          }
          
          .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #374151;
            color: #d1d5db;
            font-weight: 500;
          }
          
          .selected-count {
            color: #4f46e5;
            font-size: 13px;
          }
          
          .files-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
          }
          
          .no-files {
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
            font-style: italic;
          }
          
          .file-item {
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #2d3748;
          }
          
          .file-item:last-child {
            border-bottom: none;
          }
          
          .file-checkbox {
            margin-right: 12px;
            accent-color: #4f46e5;
          }
          
          .file-label {
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            flex: 1;
          }
          
          .file-label svg {
            color: #4f46e5;
            flex-shrink: 0;
          }
          
          .file-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1;
          }
          
          .file-name {
            color: #d1d5db;
            font-weight: 500;
            font-size: 14px;
          }
          
          .file-meta {
            color: #6b7280;
            font-size: 12px;
          }
          
          .add-btn {
            background: #4f46e5;
            color: white;
          }
          
          .add-btn:hover:not(:disabled) {
            background: #4338ca;
          }
          
          .add-btn:disabled {
            background: #374151;
            color: #6b7280;
            cursor: not-allowed;
          }
        `}</style>
      </div>
    </div>
  );
};

export default App;
