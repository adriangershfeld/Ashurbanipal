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
  Filter
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
  uploading: boolean;
  onClose: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload, uploading, onClose }) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
    }
  };

  return (
    <div className="file-upload-overlay">
      <div className="file-upload-modal">
        <div className="upload-header">
          <h3>Upload Files</h3>
          <button className="close-button" onClick={onClose} disabled={uploading}>
            <X size={20} />
          </button>
        </div>

        <div className="upload-content">
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
          </div>
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
          }

          .upload-content {
            padding: 20px;
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

export default FileViewer;