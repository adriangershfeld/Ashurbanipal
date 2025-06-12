import React, { useState, useRef } from 'react';
import { 
  X, 
  FileText, 
  Upload, 
  File, 
  Trash2, 
  Eye, 
  Plus,
  Search,
  Filter,
  FolderOpen
} from 'lucide-react';
import type { FileInfo, FileViewerProps } from '../types';

// Main FileViewer Modal Component
const FileViewer: React.FC<FileViewerProps> = ({ file, content, onClose }) => {
  if (!file) return null;

  return (
    <div className="file-viewer-overlay">
      <div className="file-viewer-modal">
        <div className="file-viewer-header">
          <div className="file-info">
            <FileText size={20} />
            <div>
              <h3>{file.filename}</h3>              <span className="file-details">
                {file.size ? `${Math.round(file.size / 1024)} KB` : 'Unknown size'} • 
                {file.chunks_count || 0} chunks
              </span>
            </div>
          </div>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="file-viewer-content">
          <div className="content-area">
            {content ? (
              <pre className="file-content">{content}</pre>
            ) : (
              <div className="no-content">
                <FileText size={48} />
                <p>Content not available</p>
              </div>
            )}
          </div>
        </div>

        <style jsx>{`
          .file-viewer-overlay {
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

          .file-viewer-modal {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            width: 100%;
            max-width: 800px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
          }

          .file-viewer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #334155;
          }

          .file-info {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .file-info svg {
            color: #4f46e5;
          }

          .file-info h3 {
            margin: 0;
            color: #f1f5f9;
            font-size: 16px;
            font-weight: 600;
          }

          .file-details {
            color: #64748b;
            font-size: 12px;
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

          .file-viewer-content {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
          }

          .content-area {
            flex: 1;
            overflow: auto;
            padding: 20px;
          }

          .file-content {
            color: #e2e8f0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
          }

          .no-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: #64748b;
          }

          .no-content svg {
            margin-bottom: 12px;
            opacity: 0.5;
          }
        `}</style>
      </div>
    </div>
  );
};

// File Upload Modal Component
interface FileUploadProps {
  onUpload: (files: FileList) => void;
  onFolderIngest: (folderPath: string) => void;
  uploading: boolean;
  onClose: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload, onFolderIngest, uploading, onClose }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadMode, setUploadMode] = useState<'files' | 'folder'>('files');
  const [folderPath, setFolderPath] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files);
    }
  };  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
    }
  };

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files);
      // Get the folder path from the first file
      const firstFile = e.target.files[0];
      if (firstFile.webkitRelativePath) {
        const folderName = firstFile.webkitRelativePath.split('/')[0];
        setFolderPath(folderName);
      }
    }
  };
  const handleFolderPathSubmit = () => {
    if (selectedFiles && selectedFiles.length > 0) {
      // Use the selected files for processing
      const folderName = selectedFiles[0].webkitRelativePath?.split('/')[0] || 'Selected Folder';
      onFolderIngest(folderName);
    }
  };

  const handleBrowseFolder = () => {
    folderInputRef.current?.click();
  };

  const clearFolderSelection = () => {
    setSelectedFiles(null);
    setFolderPath('');
    if (folderInputRef.current) {
      folderInputRef.current.value = '';
    }
  };

  return (
    <div className="file-upload-overlay">
      <div className="file-upload-modal">        <div className="upload-header">
          <h3>Add Documents to Corpus</h3>
          <button className="close-button" onClick={onClose} disabled={uploading}>
            <X size={20} />
          </button>
        </div>

        <div className="upload-content">
          {/* Upload Mode Tabs */}
          <div className="upload-mode-tabs">
            <button 
              className={`mode-tab ${uploadMode === 'files' ? 'active' : ''}`}
              onClick={() => setUploadMode('files')}
            >
              Upload Files
            </button>
            <button 
              className={`mode-tab ${uploadMode === 'folder' ? 'active' : ''}`}
              onClick={() => setUploadMode('folder')}
            >
              Select Folder
            </button>
          </div>

          {uploadMode === 'files' ? (
            <div
              className={`upload-area ${dragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={48} />
              <h4>
                {uploading ? 'Uploading...' : 'Drop files here or click to browse'}
              </h4>
              <p>Supports PDF, DOCX, TXT, and MD files</p>
              
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                disabled={uploading}
              />
            </div>          ) : (
            <div className="folder-upload-area">
              {/* Native Folder Selection */}
              <div className="folder-selection-section">
                <h4>Select Folder</h4>
                {selectedFiles && selectedFiles.length > 0 ? (
                  <div className="folder-selected">
                    <div className="folder-info-selected">
                      <div className="folder-name">
                        📁 {folderPath || 'Selected Folder'}
                      </div>
                      <div className="folder-stats">
                        {selectedFiles.length} files selected
                      </div>
                    </div>
                    <div className="folder-actions">                      <button 
                        className="change-folder-btn"
                        onClick={handleBrowseFolder}
                        disabled={uploading}
                      >
                        Change
                      </button>
                      <button 
                        className="clear-folder-btn"
                        onClick={clearFolderSelection}
                        disabled={uploading}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="folder-picker">                    <button 
                      className="browse-folder-btn"
                      onClick={handleBrowseFolder}
                      disabled={uploading}
                    >
                      <Upload size={20} />
                      Select Folder
                    </button>
                    <p className="browse-hint">
                      Choose a folder to process all documents within it
                    </p>
                  </div>
                )}
                  {/* Hidden folder input */}
                <input
                  ref={folderInputRef}
                  type="file"
                  {...({ webkitdirectory: '' } as any)}
                  multiple
                  onChange={handleFolderSelect}
                  style={{ display: 'none' }}
                  disabled={uploading}
                />              </div>

              {/* Process Button */}
              <div className="process-section">
                <button 
                  className="ingest-button"
                  onClick={handleFolderPathSubmit}
                  disabled={uploading || !selectedFiles || selectedFiles.length === 0}
                >
                  {uploading ? 'Processing...' : 'Process Folder'}
                </button>
              </div>

              {/* Information */}
              <div className="folder-info">
                <p><strong>Note:</strong> This will scan the selected folder for documents and add them to your corpus.</p>
                <p>Supported formats: PDF, DOCX, TXT, MD files</p>
              </div>
            </div>
          )}
        </div>

        <style jsx>{`
          .file-upload-overlay {
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

          .file-upload-modal {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            width: 100%;
            max-width: 500px;
          }

          .upload-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #334155;
          }

          .upload-header h3 {
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

          .close-button:hover:not(:disabled) {
            color: #cbd5e1;
            background: #374151;
          }

          .close-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }          .upload-content {
            padding: 20px;
          }

          .upload-mode-tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid #334155;
          }

          .mode-tab {
            flex: 1;
            padding: 12px 20px;
            background: none;
            border: none;
            color: #64748b;
            cursor: pointer;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
          }

          .mode-tab:hover {
            color: #cbd5e1;
          }

          .mode-tab.active {
            color: #4f46e5;
            border-bottom-color: #4f46e5;
          }

          .folder-upload-area {
            padding: 20px;
          }

          .folder-path-input {
            margin-bottom: 20px;
          }

          .folder-path-input label {
            display: block;
            color: #f1f5f9;
            font-weight: 500;
            margin-bottom: 8px;
          }

          .folder-path-input input {
            width: 100%;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px 16px;
            color: #e2e8f0;
            font-size: 14px;
            margin-bottom: 12px;
          }

          .folder-path-input input:focus {
            outline: none;
            border-color: #4f46e5;
          }

          .ingest-button {
            background: #4f46e5;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s ease;
          }

          .ingest-button:hover:not(:disabled) {
            background: #4338ca;
          }

          .ingest-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .folder-info {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.5;
          }

          .folder-info p {
            margin: 0 0 8px 0;
          }

          .folder-info p:last-child {
            margin-bottom: 0;
          }

          .upload-area {
            border: 2px dashed #334155;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: #0f172a;
          }

          .upload-area:hover:not(.uploading) {
            border-color: #4f46e5;
            background: rgba(79, 70, 229, 0.05);
          }

          .upload-area.active {
            border-color: #4f46e5;
            background: rgba(79, 70, 229, 0.1);
          }

          .upload-area.uploading {
            opacity: 0.7;
            cursor: not-allowed;
          }

          .upload-area svg {
            color: #4f46e5;
            margin-bottom: 16px;
          }

          .upload-area h4 {
            margin: 0 0 8px 0;
            color: #f1f5f9;
            font-size: 16px;
            font-weight: 600;
          }

          .upload-area p {
            margin: 0;
            color: #64748b;
            font-size: 14px;
          }
        `}</style>
      </div>
    </div>
  );
};

// File Manager Component
interface FileManagerProps {
  files: FileInfo[];
  onFileSelect: (file: FileInfo) => void;
  onFileDelete: (filename: string) => void;
  onUploadClick: () => void;
}

export const FileManager: React.FC<FileManagerProps> = ({
  files,
  onFileSelect,
  onFileDelete,
  onUploadClick
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'date'>('name');

  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.filename.localeCompare(b.filename);
      case 'size':
        return (b.size || 0) - (a.size || 0);      case 'date':
        return new Date(b.modified_date || 0).getTime() - new Date(a.modified_date || 0).getTime();
      default:
        return 0;
    }
  });

  return (
    <div className="file-manager">
      <div className="file-manager-header">
        <h2>File Management</h2>
        <button className="upload-button" onClick={onUploadClick}>
          <Plus size={16} />
          Upload Files
        </button>
      </div>

      <div className="file-controls">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="sort-controls">
          <Filter size={16} />
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as 'name' | 'size' | 'date')}>
            <option value="name">Sort by Name</option>
            <option value="size">Sort by Size</option>
            <option value="date">Sort by Date</option>
          </select>
        </div>
      </div>

      <div className="files-list">
        {sortedFiles.length === 0 ? (
          <div className="no-files">
            <File size={48} />
            <h3>No files found</h3>
            <p>
              {searchTerm 
                ? 'No files match your search criteria' 
                : 'Upload files to get started with your research corpus'
              }
            </p>
            {!searchTerm && (
              <button className="upload-cta" onClick={onUploadClick}>
                <Upload size={16} />
                Upload Your First File
              </button>
            )}
          </div>
        ) : (
          <div className="files-grid">            {sortedFiles.map((file) => (
              <FileCard
                key={file.filename}
                file={file}
                onSelect={() => onFileSelect(file)}
                onDelete={() => onFileDelete(file.filename)}
              />
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .file-manager {
          padding: 24px;
          background: #0f172a;
          min-height: 100vh;
          color: #e2e8f0;
        }

        .file-manager-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .file-manager-header h2 {
          color: #f1f5f9;
          margin: 0;
          font-size: 28px;
          font-weight: 600;
        }

        .upload-button {
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 12px 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s ease;
        }

        .upload-button:hover {
          background: #4338ca;
        }

        .file-controls {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .search-box {
          flex: 1;
          min-width: 200px;
          position: relative;
          display: flex;
          align-items: center;
        }

        .search-box svg {
          position: absolute;
          left: 12px;
          color: #64748b;
          z-index: 1;
        }

        .search-box input {
          width: 100%;
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 8px;
          padding: 12px 16px 12px 40px;
          color: #e2e8f0;
          font-size: 14px;
        }

        .search-box input:focus {
          outline: none;
          border-color: #4f46e5;
        }

        .search-box input::placeholder {
          color: #64748b;
        }

        .sort-controls {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .sort-controls svg {
          color: #64748b;
        }

        .sort-controls select {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 8px;
          padding: 12px 16px;
          color: #e2e8f0;
          font-size: 14px;
          cursor: pointer;
        }

        .sort-controls select:focus {
          outline: none;
          border-color: #4f46e5;
        }

        .files-list {
          flex: 1;
        }

        .no-files {
          text-align: center;
          padding: 60px 20px;
          color: #64748b;
        }

        .no-files svg {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .no-files h3 {
          margin: 0 0 8px 0;
          color: #cbd5e1;
          font-size: 18px;
          font-weight: 600;
        }

        .no-files p {
          margin: 0 0 24px 0;
          line-height: 1.5;
        }

        .upload-cta {
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 12px 20px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s ease;
        }

        .upload-cta:hover {
          background: #4338ca;
        }

        .files-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }
      `}</style>
    </div>
  );
};

// Individual File Card Component
interface FileCardProps {
  file: FileInfo;
  onSelect: () => void;
  onDelete: () => void;
}

const FileCard: React.FC<FileCardProps> = ({ file, onSelect, onDelete }) => {
  const formatFileSize = (bytes: number | undefined) => {
    if (!bytes) return 'Unknown size';
    const kb = bytes / 1024;
    if (kb < 1024) return `${Math.round(kb)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="file-card">
      <div className="file-card-header">
        <FileText size={20} />
        <div className="file-actions">
          <button className="action-btn view" onClick={onSelect} title="View file">
            <Eye size={14} />
          </button>
          <button className="action-btn delete" onClick={onDelete} title="Delete file">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="file-card-content">
        <h4 className="file-name">{file.filename}</h4>        <div className="file-stats">
          <span className="stat">
            <strong>{file.chunks_count || 0}</strong> chunks
          </span>
          <span className="stat">
            {formatFileSize(file.size)}
          </span>
          <span className="stat">
            {formatDate(file.modified_date)}
          </span>
        </div>
      </div>

      <style jsx>{`
        .file-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .file-card:hover {
          border-color: #4f46e5;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
        }

        .file-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .file-card-header svg {
          color: #4f46e5;
        }

        .file-actions {
          display: flex;
          gap: 4px;
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .file-card:hover .file-actions {
          opacity: 1;
        }

        .action-btn {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 6px;
          border-radius: 4px;
          transition: all 0.2s ease;
        }

        .action-btn:hover {
          color: #cbd5e1;
          background: #374151;
        }

        .action-btn.delete:hover {
          color: #ef4444;
        }

        .file-name {
          margin: 0 0 8px 0;
          color: #f1f5f9;
          font-size: 16px;
          font-weight: 600;
          line-height: 1.3;
          word-break: break-word;
        }

        .file-stats {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .stat {
          color: #64748b;
          font-size: 12px;
        }

        .stat strong {
          color: #4f46e5;
        }
      `}</style>
    </div>
  );
};

// Compact File Browser for Browser Tab
interface FileBrowserProps {
  files: FileInfo[];
  onFileSelect: (file: FileInfo) => void;
  onFileDelete: (filename: string) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  files,
  onFileSelect,
  onFileDelete,
  searchTerm,
  onSearchChange
}) => {
  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );  const handleOpenInExplorer = async (filepath: string) => {
    try {
      // Import the API function
      const { filesApi } = await import('../api');
      await filesApi.openFolder(filepath);
      console.log('Folder opened successfully');
    } catch (error: any) {
      console.error('Failed to open in explorer:', error);
      
      // Show user-friendly error message
      const errorMessage = error.message || 'Failed to open folder in file explorer';
      alert(`Error: ${errorMessage}`);
    }
  };

  const formatFileSize = (bytes: number | undefined) => {
    if (!bytes) return 'Unknown';
    const kb = bytes / 1024;
    if (kb < 1024) return `${Math.round(kb)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="file-browser-content">
      <div className="browser-search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Search files..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="files-list-compact">
        {filteredFiles.length === 0 ? (
          <div className="no-files-compact">
            <File size={24} />
            <p>
              {searchTerm ? 'No files match your search' : 'No files uploaded yet'}
            </p>
          </div>
        ) : (
          filteredFiles.map((file) => (
            <div 
              key={file.filename} 
              className="file-item-compact"
              onClick={() => onFileSelect(file)}
            >
              <div className="file-icon">
                <FileText size={16} />
              </div>
              <div className="file-details">
                <div className="file-name-compact">{file.filename}</div>
                <div className="file-meta">
                  <span>{file.chunks_count || 0} chunks</span>
                  <span>•</span>
                  <span>{formatFileSize(file.size)}</span>
                </div>
              </div>              <div className="file-actions-compact">
                <button 
                  className="action-btn-compact explorer"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenInExplorer(file.filepath);
                  }}
                  title="Open in file explorer"
                >
                  <FolderOpen size={12} />
                </button>
                <button 
                  className="action-btn-compact delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    onFileDelete(file.filename);
                  }}
                  title="Delete file"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .file-browser-content {
          display: flex;
          flex-direction: column;
          height: 100%;
          overflow: hidden;
        }

        .browser-search {
          position: relative;
          display: flex;
          align-items: center;
          margin: 16px 20px;
        }

        .browser-search svg {
          position: absolute;
          left: 12px;
          color: #64748b;
          z-index: 1;
        }

        .browser-search input {
          width: 100%;
          background: #0f0f23;
          border: 1px solid #374151;
          border-radius: 6px;
          padding: 8px 12px 8px 36px;
          color: #e2e8f0;
          font-size: 13px;
        }

        .browser-search input:focus {
          outline: none;
          border-color: #4f46e5;
        }

        .browser-search input::placeholder {
          color: #64748b;
        }

        .files-list-compact {
          flex: 1;
          overflow-y: auto;
          padding: 0 20px 20px;
        }

        .no-files-compact {
          text-align: center;
          padding: 40px 20px;
          color: #64748b;
        }

        .no-files-compact svg {
          margin-bottom: 12px;
          opacity: 0.5;
        }

        .no-files-compact p {
          margin: 0;
          font-size: 13px;
          line-height: 1.4;
        }

        .file-item-compact {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
          border: 1px solid transparent;
        }

        .file-item-compact:hover {
          background: rgba(79, 70, 229, 0.1);
          border-color: #4f46e5;
        }

        .file-icon {
          flex-shrink: 0;
          color: #4f46e5;
        }

        .file-details {
          flex: 1;
          min-width: 0;
        }

        .file-name-compact {
          color: #d1d5db;
          font-size: 13px;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 2px;
        }

        .file-meta {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #6b7280;
          font-size: 11px;
        }

        .file-actions-compact {
          flex-shrink: 0;
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .file-item-compact:hover .file-actions-compact {
          opacity: 1;
        }        .action-btn-compact {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
          padding: 4px;
          border-radius: 3px;
          transition: all 0.2s ease;
          margin-left: 4px;
        }

        .action-btn-compact:hover {
          color: #cbd5e1;
          background: #374151;
        }

        .action-btn-compact.explorer:hover {
          color: #3b82f6;
        }

        .action-btn-compact.delete:hover {
          color: #ef4444;
        }

        /* Scrollbar styling */
        .files-list-compact::-webkit-scrollbar {
          width: 6px;
        }

        .files-list-compact::-webkit-scrollbar-track {
          background: #1a1a2e;
        }

        .files-list-compact::-webkit-scrollbar-thumb {
          background: #374151;
          border-radius: 3px;
        }

        .files-list-compact::-webkit-scrollbar-thumb:hover {
          background: #4b5563;
        }
      `}</style>
    </div>
  );
};

// Enhanced File Content Viewer for Browser Tab
interface FileContentViewerProps {
  file: FileInfo;
  content: string;
  onLineClick?: (lineNumber: number) => void;
  highlightLine?: number;
}

export const FileContentViewer: React.FC<FileContentViewerProps> = ({
  file,
  content,
  onLineClick,
  highlightLine
}) => {
  const lines = content.split('\n');
  
  return (
    <div className="file-content-viewer">
      <div className="content-header">
        <div className="file-info-minimal">
          <FileText size={16} />
          <span className="filename">{file.filename}</span>
        </div>
        <div className="content-stats">
          <span>{lines.length} lines</span>
          <span>•</span>
          <span>{file.chunks_count || 0} chunks</span>
        </div>
      </div>
      
      <div className="content-body">
        <div className="line-numbers">
          {lines.map((_, index) => (
            <div 
              key={index}
              className={`line-number ${highlightLine === index + 1 ? 'highlighted' : ''}`}
              onClick={() => onLineClick?.(index + 1)}
            >
              {index + 1}
            </div>
          ))}
        </div>
        <div className="content-lines">
          {lines.map((line, index) => (
            <div 
              key={index}
              className={`content-line ${highlightLine === index + 1 ? 'highlighted' : ''}`}
              onClick={() => onLineClick?.(index + 1)}
            >
              {line || ' '}
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .file-content-viewer {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #0f0f23;
          border-left: 1px solid #374151;
        }

        .content-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #374151;
          background: #1a1a2e;
        }

        .file-info-minimal {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #d1d5db;
        }

        .file-info-minimal svg {
          color: #4f46e5;
        }

        .filename {
          font-size: 13px;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 200px;
        }

        .content-stats {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #6b7280;
          font-size: 11px;
        }

        .content-body {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .line-numbers {
          background: #1a1a2e;
          border-right: 1px solid #374151;
          padding: 8px 0;
          user-select: none;
          min-width: 50px;
          max-width: 60px;
          overflow: hidden;
        }

        .line-number {
          padding: 0 8px;
          text-align: right;
          font-family: 'Fira Code', monospace;
          font-size: 12px;
          line-height: 1.4;
          color: #6b7280;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .line-number:hover {
          background: rgba(79, 70, 229, 0.1);
          color: #9ca3af;
        }

        .line-number.highlighted {
          background: rgba(79, 70, 229, 0.2);
          color: #4f46e5;
          font-weight: 600;
        }

        .content-lines {
          flex: 1;
          overflow: auto;
          padding: 8px 0;
          font-family: 'Fira Code', monospace;
          font-size: 12px;
          line-height: 1.4;
        }

        .content-line {
          padding: 0 12px;
          color: #d1d5db;
          white-space: pre;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .content-line:hover {
          background: rgba(79, 70, 229, 0.05);
        }

        .content-line.highlighted {
          background: rgba(79, 70, 229, 0.15);
          border-left: 2px solid #4f46e5;
          padding-left: 10px;
        }

        /* Scrollbar styling */
        .content-lines::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }

        .content-lines::-webkit-scrollbar-track {
          background: #1a1a2e;
        }

        .content-lines::-webkit-scrollbar-thumb {
          background: #374151;
          border-radius: 3px;
        }

        .content-lines::-webkit-scrollbar-thumb:hover {
          background: #4b5563;
        }
      `}</style>
    </div>
  );
};

export default FileViewer;