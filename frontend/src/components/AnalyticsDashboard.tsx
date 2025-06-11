import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, FileText, Search, Clock, Users, ArrowUp, ArrowDown } from 'lucide-react';
import { analyticsApi } from '../api';

interface AnalyticsData {
  total_documents: number;
  total_chunks: number;
  total_searches: number;
  total_chat_messages: number;
  avg_response_time: number;
  popular_documents: Array<{
    filename: string;
    views: number;
    searches: number;
  }>;
  search_trends: Array<{
    query: string;
    count: number;
    avg_relevance: number;
  }>;
  daily_activity: Array<{
    date: string;
    searches: number;
    chats: number;
  }>;
  document_stats: Array<{
    type: string;
    count: number;
    total_size: number;
  }>;
}

interface AnalyticsDashboardProps {
  loading?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ loading: externalLoading = false }) => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'searches' | 'chats' | 'documents'>('searches');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getOverview();
      setAnalyticsData(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError('Failed to load analytics data');
      // Use mock data as fallback
      setAnalyticsData(getMockData());
    } finally {
      setLoading(false);
    }
  };

  const getMockData = (): AnalyticsData => {
    return {
      total_documents: 47,
      total_chunks: 1240,
      total_searches: 234,
      total_chat_messages: 89,
      avg_response_time: 1.2,
      popular_documents: [
        { filename: 'research_paper_2024.pdf', views: 45, searches: 23 },
        { filename: 'project_proposal.docx', views: 32, searches: 18 },
        { filename: 'technical_specs.md', views: 28, searches: 15 },
        { filename: 'meeting_notes.txt', views: 19, searches: 12 },
      ],
      search_trends: [
        { query: 'machine learning', count: 15, avg_relevance: 0.87 },
        { query: 'neural networks', count: 12, avg_relevance: 0.91 },
        { query: 'data analysis', count: 10, avg_relevance: 0.83 },
        { query: 'project timeline', count: 8, avg_relevance: 0.76 },
      ],
      daily_activity: [
        { date: '2024-06-04', searches: 12, chats: 5 },
        { date: '2024-06-05', searches: 18, chats: 7 },
        { date: '2024-06-06', searches: 15, chats: 4 },
        { date: '2024-06-07', searches: 22, chats: 9 },
        { date: '2024-06-08', searches: 19, chats: 6 },
        { date: '2024-06-09', searches: 25, chats: 11 },
        { date: '2024-06-10', searches: 28, chats: 8 },
      ],
      document_stats: [
        { type: 'PDF', count: 24, total_size: 45.6 },
        { type: 'DOCX', count: 12, total_size: 8.9 },
        { type: 'TXT', count: 8, total_size: 2.1 },
        { type: 'MD', count: 3, total_size: 0.8 },
      ],
    };
  };

  const formatSize = (sizeInMB: number): string => {
    if (sizeInMB < 1) {
      return `${(sizeInMB * 1024).toFixed(1)} KB`;
    } else if (sizeInMB < 1024) {
      return `${sizeInMB.toFixed(1)} MB`;
    } else {
      return `${(sizeInMB / 1024).toFixed(1)} GB`;
    }
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, change, icon, color }) => (
    <div className="stat-card">
      <div className="stat-header">
        <div className={`stat-icon ${color}`}>
          {icon}
        </div>
        {change !== undefined && (
          <div className={`stat-change ${change >= 0 ? 'positive' : 'negative'}`}>
            {change >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
      </div>
    </div>
  );
  if (loading || externalLoading) {
    return (
      <div className="analytics-loading">
        <div className="loading-spinner"></div>
        <span>Loading analytics...</span>
      </div>
    );
  }

  if (error && !analyticsData) {
    return (
      <div className="analytics-error">
        <p>Failed to load analytics data</p>
        <button onClick={loadAnalytics}>Retry</button>
      </div>
    );
  }

  if (!analyticsData) {
    return null;
  }

  return (
    <div className="analytics-dashboard">
      <header className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="time-range-selector">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              className={`range-button ${timeRange === range ? 'active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </header>

      <div className="stats-grid">
        <StatCard
          title="Total Documents"
          value={analyticsData.total_documents}
          change={12}
          icon={<FileText size={20} />}
          color="blue"
        />
        <StatCard
          title="Content Chunks"
          value={analyticsData.total_chunks.toLocaleString()}
          change={8}
          icon={<BarChart3 size={20} />}
          color="green"
        />
        <StatCard
          title="Total Searches"
          value={analyticsData.total_searches}
          change={-3}
          icon={<Search size={20} />}
          color="purple"
        />
        <StatCard
          title="Chat Messages"
          value={analyticsData.total_chat_messages}
          change={25}
          icon={<Users size={20} />}
          color="orange"
        />
        <StatCard
          title="Avg Response Time"
          value={`${analyticsData.avg_response_time}s`}
          change={-15}
          icon={<Clock size={20} />}
          color="red"
        />
        <StatCard
          title="Active Today"
          value="18"
          change={22}
          icon={<TrendingUp size={20} />}
          color="teal"
        />
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <header className="chart-header">
            <h3>Daily Activity</h3>
            <div className="metric-selector">
              {(['searches', 'chats', 'documents'] as const).map((metric) => (
                <button
                  key={metric}
                  className={`metric-button ${selectedMetric === metric ? 'active' : ''}`}
                  onClick={() => setSelectedMetric(metric)}
                >
                  {metric.charAt(0).toUpperCase() + metric.slice(1)}
                </button>
              ))}
            </div>
          </header>
          <div className="activity-chart">            {analyticsData.daily_activity.map((day) => (
              <div key={day.date} className="activity-bar">
                <div 
                  className="bar searches"
                  style={{ 
                    height: `${(day.searches / 30) * 100}%`,
                    opacity: selectedMetric === 'searches' ? 1 : 0.3
                  }}
                  title={`${day.searches} searches`}
                ></div>
                <div 
                  className="bar chats"
                  style={{ 
                    height: `${(day.chats / 15) * 100}%`,
                    opacity: selectedMetric === 'chats' ? 1 : 0.3
                  }}
                  title={`${day.chats} chats`}
                ></div>
                <div className="bar-label">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <header className="chart-header">
            <h3>Popular Documents</h3>
          </header>
          <div className="popular-documents">
            {analyticsData.popular_documents.map((doc, index) => (
              <div key={doc.filename} className="document-item">
                <div className="document-rank">#{index + 1}</div>
                <div className="document-info">
                  <div className="document-name">{doc.filename}</div>
                  <div className="document-stats">
                    {doc.views} views • {doc.searches} searches
                  </div>
                </div>
                <div className="document-bar">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(doc.views / analyticsData.popular_documents[0].views) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <header className="chart-header">
            <h3>Search Trends</h3>
          </header>          <div className="search-trends">
            {analyticsData.search_trends.map((trend) => (
              <div key={trend.query} className="trend-item">
                <div className="trend-query">{trend.query}</div>
                <div className="trend-stats">
                  <span className="trend-count">{trend.count} searches</span>
                  <span className="trend-relevance">{(trend.avg_relevance * 100).toFixed(0)}% relevance</span>
                </div>
                <div className="trend-bar">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(trend.count / analyticsData.search_trends[0].count) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <header className="chart-header">
            <h3>Document Types</h3>
          </header>
          <div className="document-types">
            {analyticsData.document_stats.map((stat) => (
              <div key={stat.type} className="type-item">
                <div className="type-info">
                  <div className="type-name">{stat.type}</div>
                  <div className="type-count">{stat.count} files</div>
                </div>
                <div className="type-size">{formatSize(stat.total_size)}</div>
                <div className="type-bar">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(stat.count / analyticsData.total_documents) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        .analytics-dashboard {
          padding: 24px;
          background: #0f172a;
          min-height: 100vh;
          color: #f1f5f9;
        }

        .analytics-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          height: 50vh;
          color: #64748b;
        }

        .loading-spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #334155;
          border-top: 2px solid #4f46e5;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }

        .dashboard-header h1 {
          margin: 0;
          font-size: 32px;
          font-weight: 600;
          color: #f1f5f9;
        }

        .time-range-selector {
          display: flex;
          gap: 8px;
        }

        .range-button {
          background: #1e293b;
          color: #94a3b8;
          border: 1px solid #334155;
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .range-button:hover {
          color: #f1f5f9;
          border-color: #4f46e5;
        }

        .range-button.active {
          background: #4f46e5;
          color: white;
          border-color: #4f46e5;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }

        .stat-card {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s ease;
        }

        .stat-card:hover {
          border-color: #4f46e5;
          transform: translateY(-2px);
        }

        .stat-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .stat-icon {
          padding: 8px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon.blue { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
        .stat-icon.green { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
        .stat-icon.purple { background: rgba(168, 85, 247, 0.1); color: #a855f7; }
        .stat-icon.orange { background: rgba(251, 146, 60, 0.1); color: #fb923c; }
        .stat-icon.red { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .stat-icon.teal { background: rgba(20, 184, 166, 0.1); color: #14b8a6; }

        .stat-change {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          font-weight: 500;
          padding: 4px 8px;
          border-radius: 6px;
        }

        .stat-change.positive {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }

        .stat-change.negative {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #f1f5f9;
          margin-bottom: 4px;
        }

        .stat-title {
          color: #64748b;
          font-size: 14px;
          font-weight: 500;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 24px;
        }

        .chart-container {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 24px;
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .chart-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #f1f5f9;
        }

        .metric-selector {
          display: flex;
          gap: 4px;
        }

        .metric-button {
          background: none;
          color: #64748b;
          border: 1px solid #334155;
          padding: 4px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .metric-button:hover {
          color: #f1f5f9;
          border-color: #4f46e5;
        }

        .metric-button.active {
          background: #4f46e5;
          color: white;
          border-color: #4f46e5;
        }

        .activity-chart {
          display: flex;
          gap: 8px;
          align-items: end;
          height: 200px;
          padding: 20px 0;
        }

        .activity-bar {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
          position: relative;
        }

        .bar {
          width: 100%;
          border-radius: 4px 4px 0 0;
          transition: all 0.3s ease;
          margin-bottom: 8px;
        }

        .bar.searches {
          background: #4f46e5;
          margin-right: 2px;
        }

        .bar.chats {
          background: #10b981;
          margin-left: 2px;
        }

        .bar-label {
          font-size: 10px;
          color: #64748b;
          text-align: center;
          margin-top: auto;
        }

        .popular-documents,
        .search-trends,
        .document-types {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .document-item,
        .trend-item,
        .type-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: #0f172a;
          border-radius: 8px;
          border: 1px solid #334155;
        }

        .document-rank {
          background: #4f46e5;
          color: white;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          flex-shrink: 0;
        }

        .document-info,
        .type-info {
          flex: 1;
          min-width: 0;
        }

        .document-name,
        .trend-query,
        .type-name {
          color: #f1f5f9;
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .document-stats,
        .trend-stats,
        .type-count {
          color: #64748b;
          font-size: 12px;
          margin-top: 2px;
        }

        .trend-stats {
          display: flex;
          gap: 12px;
        }

        .type-size {
          color: #4f46e5;
          font-weight: 500;
          font-size: 14px;
          flex-shrink: 0;
        }

        .document-bar,
        .trend-bar,
        .type-bar {
          width: 60px;
          height: 4px;
          background: #334155;
          border-radius: 2px;
          overflow: hidden;
          flex-shrink: 0;
        }

        .bar-fill {
          height: 100%;
          background: #4f46e5;
          border-radius: 2px;
          transition: width 0.3s ease;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AnalyticsDashboard;
