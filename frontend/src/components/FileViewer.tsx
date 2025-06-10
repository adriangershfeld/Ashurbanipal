import React from 'react';
import { X, FileText, Calendar, HardDrive } from 'lucide-react';
import type { FileViewerProps } from '../types';

const FileViewer: React.FC<FileViewerProps> = ({ file, content, onClose }) => {
  if (!file) return null;

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="file-viewer-overlay">
      <div className="file-viewer">
        <header className="file-viewer-header">
          <div className="file-info">
            <FileText size={20} />
            <div>
              <h2 className="file-name">{file.filename}</h2>
              <p className="file-path">{file.filepath}</p>
            </div>
          </div>
          <button onClick={onClose} className="close-button">
            <X size={20} />
          </button>
        </header>

        <div className="file-metadata">
          <div className="metadata-item">
            <HardDrive size={16} />
            <span>{formatFileSize(file.size)}</span>
          </div>
          <div className="metadata-item">
            <Calendar size={16} />
            <span>{formatDate(file.modified_date)}</span>
          </div>
          <div className="metadata-item">
            <FileText size={16} />
            <span>{file.chunks_count} chunks</span>
          </div>
          <div className="metadata-item">
            <span className="file-type-badge">{file.file_type.toUpperCase()}</span>
          </div>
        </div>

        <div className="file-content">
          {content ? (
            <div className="content-display">
              <h3>Content Preview</h3>
              <div className="content-text">
                {content}
              </div>
            </div>
          ) : (
            <div className="no-content">
              <FileText size={48} className="no-content-icon" />
              <p>Content preview not available</p>
              <p className="no-content-subtitle">
                This file has been indexed but content preview is not supported for this file type.
              </p>
            </div>
          )}
        </div>

        <footer className="file-viewer-footer">
          <button className="action-button secondary" onClick={onClose}>
            Close
          </button>
          <button className="action-button primary">
            Open in System
          </button>
        </footer>
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

        .file-viewer {
          background: #0f0f23;
          border: 1px solid #374151;
          border-radius: 12px;
          width: 100%;
          max-width: 800px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .file-viewer-header {
          padding: 20px;
          border-bottom: 1px solid #374151;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .file-info {
          display: flex;
          align-items: center;
          gap: 12px;
          flex: 1;
        }

        .file-name {
          margin: 0 0 4px 0;
          color: #f3f4f6;
          font-size: 18px;
          font-weight: 600;
        }

        .file-path {
          margin: 0;
          color: #6b7280;
          font-size: 14px;
          font-family: monospace;
        }

        .close-button {
          background: transparent;
          border: none;
          color: #6b7280;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.2s ease;
        }

        .close-button:hover {
          background: #374151;
          color: #f3f4f6;
        }

        .file-metadata {
          padding: 16px 20px;
          border-bottom: 1px solid #374151;
          display: flex;
          flex-wrap: wrap;
          gap: 20px;
        }

        .metadata-item {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
          font-size: 14px;
        }

        .file-type-badge {
          background: #4f46e5;
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .file-content {
          flex: 1;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .content-display {
          padding: 20px;
          height: 100%;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .content-display h3 {
          margin: 0 0 16px 0;
          color: #f3f4f6;
          font-size: 16px;
          font-weight: 600;
        }

        .content-text {
          flex: 1;
          background: #1a1a2e;
          border: 1px solid #374151;
          border-radius: 8px;
          padding: 16px;
          color: #d1d5db;
          font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
          font-size: 14px;
          line-height: 1.6;
          overflow: auto;
          white-space: pre-wrap;
        }

        .no-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          color: #6b7280;
          text-align: center;
          padding: 20px;
        }

        .no-content-icon {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .no-content p {
          margin: 4px 0;
        }

        .no-content-subtitle {
          font-size: 14px;
          opacity: 0.8;
        }

        .file-viewer-footer {
          padding: 20px;
          border-top: 1px solid #374151;
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }

        .action-button {
          padding: 8px 16px;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .action-button.secondary {
          background: transparent;
          border: 1px solid #374151;
          color: #9ca3af;
        }

        .action-button.secondary:hover {
          background: #374151;
          color: #f3f4f6;
        }

        .action-button.primary {
          background: #4f46e5;
          border: 1px solid #4f46e5;
          color: white;
        }

        .action-button.primary:hover {
          background: #4338ca;
          border-color: #4338ca;
        }
      `}</style>
    </div>
  );
};

export default FileViewer;
