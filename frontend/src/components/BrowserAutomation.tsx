import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Play, 
  Square, 
  Monitor, 
  Database, 
  Clock, 
  FileText,
  Download,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { browserApi } from '../api';

interface ResearchSession {
  id: string;
  start_time: number;
  captured_items: number;
  browser_running: boolean;
  clipboard_monitoring: boolean;
}

interface WorkflowStatus {
  browser: {
    running: boolean;
    processes: number;
  };
  sessions: {
    active: number;
    details: ResearchSession[];
  };
  clipboard_monitoring: {
    active_watchers: number;
    total_captured: number;
  };
}

interface BrowserAutomationProps {
  onSessionUpdate?: (sessions: ResearchSession[]) => void;
}

const BrowserAutomation: React.FC<BrowserAutomationProps> = ({ onSessionUpdate }) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Auto-refresh status every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadWorkflowStatus();
    }, 10000);

    // Initial load
    loadWorkflowStatus();

    return () => clearInterval(interval);
  }, []);

  const loadWorkflowStatus = async () => {
    try {
      const status = await browserApi.getWorkflowStatus();
      setWorkflowStatus(status);
      setLastUpdate(new Date());
      
      if (onSessionUpdate && status.sessions) {
        onSessionUpdate(status.sessions.details);
      }
    } catch (error) {
      console.error('Failed to load workflow status:', error);
    }
  };

  const handleStartSession = async () => {
    try {
      setLoading(true);
      const result = await browserApi.startResearchSession(searchQuery || undefined);
      
      if (result.success) {
        setActiveSession(result.session_id);
        await loadWorkflowStatus();
        setSearchQuery('');
      }
    } catch (error) {
      console.error('Failed to start research session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopSession = async (sessionId: string) => {
    try {
      setLoading(true);
      await browserApi.stopSession(sessionId);
      
      if (activeSession === sessionId) {
        setActiveSession(null);
      }
      
      await loadWorkflowStatus();
    } catch (error) {
      console.error('Failed to stop session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleIngestSession = async (sessionId: string) => {
    try {
      setLoading(true);
      const result = await browserApi.ingestSessionContent(sessionId);
      
      if (result.status === 'completed') {
        console.log(`Ingested ${result.items_processed} items, ${result.chunks_created} chunks`);
        await loadWorkflowStatus();
      }
    } catch (error) {
      console.error('Failed to ingest session content:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (startTime: number) => {
    const duration = Date.now() / 1000 - startTime;
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <div className="browser-automation">
      <div className="automation-header">
        <h2>Browser Automation</h2>
        <div className="status-info">
          <span className="last-updated">
            <Clock size={14} />
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
          <button 
            className="refresh-btn"
            onClick={loadWorkflowStatus}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
          </button>
        </div>
      </div>

      {/* Overall Status */}
      {workflowStatus && (
        <div className="status-overview">
          <div className="status-card">
            <Globe size={20} />
            <div className="status-details">
              <span className="status-label">Browser</span>
              <span className={`status-value ${workflowStatus.browser.running ? 'active' : 'inactive'}`}>
                {workflowStatus.browser.running ? 'Running' : 'Stopped'}
              </span>
            </div>
          </div>

          <div className="status-card">
            <Monitor size={20} />
            <div className="status-details">
              <span className="status-label">Sessions</span>
              <span className="status-value">
                {workflowStatus.sessions.active} active
              </span>
            </div>
          </div>

          <div className="status-card">
            <Database size={20} />
            <div className="status-details">
              <span className="status-label">Captured</span>
              <span className="status-value">
                {workflowStatus.clipboard_monitoring.total_captured} items
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Start New Session */}
      <div className="session-control">
        <h3>Start Research Session</h3>
        <div className="session-form">
          <input
            type="text"
            placeholder="Search query (optional)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button 
            className="start-btn"
            onClick={handleStartSession}
            disabled={loading}
          >
            <Play size={16} />
            Start Session
          </button>
        </div>
      </div>

      {/* Active Sessions */}
      {workflowStatus?.sessions.details && workflowStatus.sessions.details.length > 0 && (
        <div className="active-sessions">
          <h3>Active Sessions</h3>
          <div className="sessions-list">
            {workflowStatus.sessions.details.map((session) => (
              <div key={session.id} className="session-card">
                <div className="session-header">
                  <div className="session-info">
                    <span className="session-id">
                      Session {session.id.split('_')[1]}
                    </span>
                    <span className="session-duration">
                      {formatDuration(session.start_time)}
                    </span>
                  </div>
                  <div className="session-status">
                    {session.browser_running && (
                      <span className="status-indicator browser">
                        <Globe size={12} />
                        Browser
                      </span>
                    )}
                    {session.clipboard_monitoring && (
                      <span className="status-indicator clipboard">
                        <Monitor size={12} />
                        Clipboard
                      </span>
                    )}
                  </div>
                </div>

                <div className="session-stats">
                  <div className="stat">
                    <FileText size={14} />
                    <span>{session.captured_items} items captured</span>
                  </div>
                </div>

                <div className="session-actions">
                  <button
                    className="action-btn ingest"
                    onClick={() => handleIngestSession(session.id)}
                    disabled={loading || session.captured_items === 0}
                    title="Ingest captured content into corpus"
                  >
                    <Download size={14} />
                    Ingest
                  </button>
                  <button
                    className="action-btn stop"
                    onClick={() => handleStopSession(session.id)}
                    disabled={loading}
                    title="Stop session"
                  >
                    <Square size={14} />
                    Stop
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help Text */}
      {(!workflowStatus?.sessions.details || workflowStatus.sessions.details.length === 0) && (
        <div className="help-section">
          <AlertCircle size={24} />
          <h4>No Active Sessions</h4>
          <p>
            Start a research session to automatically monitor clipboard content 
            while browsing. Captured content can be ingested into your corpus.
          </p>
        </div>
      )}

      <style jsx>{`
        .browser-automation {
          padding: 24px;
          background: #0f172a;
          min-height: 100vh;
          color: #e2e8f0;
        }

        .automation-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }

        .automation-header h2 {
          color: #f1f5f9;
          margin: 0;
          font-size: 28px;
          font-weight: 600;
        }

        .status-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .last-updated {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #64748b;
          font-size: 12px;
        }

        .refresh-btn {
          background: none;
          border: 1px solid #334155;
          color: #64748b;
          padding: 8px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: all 0.2s ease;
        }

        .refresh-btn:hover {
          border-color: #4f46e5;
          color: #4f46e5;
        }

        .refresh-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .status-overview {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .status-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .status-card svg {
          color: #4f46e5;
          flex-shrink: 0;
        }

        .status-details {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .status-label {
          color: #64748b;
          font-size: 12px;
          font-weight: 500;
        }

        .status-value {
          color: #f1f5f9;
          font-size: 16px;
          font-weight: 600;
        }

        .status-value.active {
          color: #10b981;
        }

        .status-value.inactive {
          color: #6b7280;
        }

        .session-control {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 32px;
        }

        .session-control h3 {
          color: #f1f5f9;
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .session-form {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .search-input {
          flex: 1;
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
          padding: 12px 16px;
          color: #e2e8f0;
          font-size: 14px;
        }

        .search-input:focus {
          outline: none;
          border-color: #4f46e5;
        }

        .search-input::placeholder {
          color: #64748b;
        }

        .start-btn {
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

        .start-btn:hover:not(:disabled) {
          background: #4338ca;
        }

        .start-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .active-sessions h3 {
          color: #f1f5f9;
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .sessions-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .session-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
        }

        .session-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .session-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .session-id {
          color: #f1f5f9;
          font-weight: 600;
          font-size: 16px;
        }

        .session-duration {
          color: #64748b;
          font-size: 12px;
        }

        .session-status {
          display: flex;
          gap: 8px;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 4px;
          background: rgba(79, 70, 229, 0.1);
          border: 1px solid rgba(79, 70, 229, 0.3);
          border-radius: 6px;
          padding: 4px 8px;
          font-size: 11px;
          color: #a5b4fc;
        }

        .session-stats {
          margin-bottom: 16px;
        }

        .stat {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #64748b;
          font-size: 14px;
        }

        .stat svg {
          color: #4f46e5;
        }

        .session-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          background: none;
          border: 1px solid #334155;
          color: #64748b;
          border-radius: 6px;
          padding: 8px 12px;
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .action-btn:hover:not(:disabled) {
          border-color: #4f46e5;
          color: #4f46e5;
        }

        .action-btn.ingest:hover:not(:disabled) {
          border-color: #10b981;
          color: #10b981;
        }

        .action-btn.stop:hover:not(:disabled) {
          border-color: #ef4444;
          color: #ef4444;
        }

        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .help-section {
          text-align: center;
          padding: 48px 24px;
          color: #64748b;
        }

        .help-section svg {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .help-section h4 {
          color: #94a3b8;
          margin: 0 0 12px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .help-section p {
          margin: 0;
          line-height: 1.6;
          max-width: 400px;
          margin: 0 auto;
        }
      `}</style>
    </div>
  );
};

export default BrowserAutomation;
