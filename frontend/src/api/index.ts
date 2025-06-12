import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  ChatRequest,
  ChatResponse,
  FilesResponse,
  IngestRequest,
  IngestResponse,
  CorpusStatus,
  FileInfo,
  SearchResult
} from '../types';

// Research project types
export interface ResearchProject {
  id: string;
  name: string;
  description: string;
  created: string;
  updated: string;
  filesCount: number;
  chunksCount: number;
  tags: string[];
  settings: Record<string, any>;
}

export interface CreateProjectRequest {
  name: string;
  description: string;
  tags?: string[];
  settings?: Record<string, any>;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  tags?: string[];
  settings?: Record<string, any>;
}

// Configure axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// Query API
export const queryApi = {
  search: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post('/search', request);
    return response.data;
  },

  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat', request);
    return response.data;
  },

  chatStream: async (
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onSources: (sources: SearchResult[]) => void,
    onError: (error: string) => void,
    onComplete: (metadata: any) => void
  ): Promise<void> => {
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available for response stream');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
          // Process complete SSE events
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('event:')) {
            // Event type information - currently not used but could be for future event handling
            continue;
          }
          
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim());
              
              // Handle different event types based on data structure
              if (data.sources) {
                onSources(data.sources);
              } else if (data.content) {
                onChunk(data.content);
              } else if (data.error) {
                onError(data.error);
                return;
              } else if (data.response_time_ms !== undefined) {
                onComplete(data);
                return;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      onError(error instanceof Error ? error.message : 'Unknown streaming error');
    }
  },

  findSimilar: async (chunkId: string, limit: number = 5): Promise<any> => {
    const response = await api.get(`/similar/${chunkId}`, {
      params: { limit }
    });
    return response.data;
  }
};

// Files API
export const filesApi = {
  list: async (limit: number = 50, offset: number = 0): Promise<FilesResponse> => {
    const response = await api.get('/files', {
      params: { limit, offset }
    });
    return response.data;
  },

  getInfo: async (fileId: string): Promise<FileInfo> => {
    const response = await api.get(`/files/${fileId}`);
    return response.data;
  },

  getContent: async (filename: string, maxLength: number = 10000): Promise<any> => {
    const response = await api.get(`/files/${encodeURIComponent(filename)}/content?max_length=${maxLength}`);
    return response.data;
  },

  open: async (fileId: string): Promise<void> => {
    await api.post(`/files/open/${fileId}`);
  },  openFolder: async (folderPath: string): Promise<any> => {
    try {
      const response = await api.post('/files/open-folder', {
        folder_path: folderPath
      });
      return response.data;
    } catch (error: any) {
      console.error('Failed to open folder:', error);
      
      // Enhanced error handling with specific messages
      if (error.response?.status === 403) {
        throw new Error('Permission denied: Cannot access this folder');
      } else if (error.response?.status === 404) {
        throw new Error('Folder not found');
      } else if (error.response?.status === 400) {
        throw new Error('Invalid folder path');
      } else {
        throw new Error(error.response?.data?.detail || 'Failed to open folder');
      }
    }
  },

  getChunks: async (fileId: string): Promise<any> => {
    const response = await api.get(`/files/${fileId}/chunks`);
    return response.data;
  },

  delete: async (fileId: string): Promise<void> => {
    await api.delete(`/files/${fileId}`);
  }
};

// Ingestion API
export const ingestApi = {
  ingestFolder: async (request: IngestRequest): Promise<IngestResponse> => {
    const response = await api.post('/ingest/folder', request);
    return response.data;
  },

  ingestFile: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/ingest/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  ingestUrl: async (url: string): Promise<any> => {
    const formData = new FormData();
    formData.append('url', url);
    
    const response = await api.post('/ingest/url', formData);
    return response.data;
  },

  getStatus: async (): Promise<CorpusStatus> => {
    const response = await api.get('/ingest/status');
    return response.data;
  },

  clearCorpus: async (): Promise<void> => {
    await api.delete('/ingest/clear');
  }
};

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string; message: string }> => {
    const response = await api.get('/health');
    return response.data;
  }
};

// Analytics API
export const analyticsApi = {
  getOverview: async (): Promise<any> => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },

  getSearchStats: async (): Promise<any> => {
    const response = await api.get('/analytics/search-stats');
    return response.data;
  },

  getDocumentStats: async (): Promise<any> => {
    const response = await api.get('/analytics/document-stats');
    return response.data;
  }
};

// Browser Automation API
export const browserApi = {
  launch: async (searchQuery?: string, url?: string): Promise<any> => {
    const response = await api.post('/browser/launch', {
      search_query: searchQuery,
      url: url,
      private: true,
      headless: false
    });
    return response.data;
  },

  startResearchSession: async (searchQuery?: string): Promise<any> => {
    const response = await api.post('/browser/research-session', {
      search_query: searchQuery,
      monitor_clipboard: true
    });
    return response.data;
  },

  getStatus: async (): Promise<any> => {
    const response = await api.get('/browser/status');
    return response.data;
  },

  close: async (): Promise<any> => {
    const response = await api.post('/browser/close');
    return response.data;
  },

  startClipboardMonitoring: async (): Promise<any> => {
    const response = await api.post('/clipboard/start-monitoring');
    return response.data;
  },

  getWorkflowStatus: async (): Promise<any> => {
    const response = await api.get('/automation/workflow-status');
    return response.data;
  },

  getSessionStatus: async (sessionId: string): Promise<any> => {
    const response = await api.get(`/research-session/${sessionId}/status`);
    return response.data;
  },

  ingestSessionContent: async (sessionId: string): Promise<any> => {
    const response = await api.post(`/research-session/${sessionId}/ingest`);
    return response.data;
  },
  stopSession: async (sessionId: string): Promise<any> => {
    const response = await api.delete(`/research-session/${sessionId}`);
    return response.data;
  }
};

// Projects API
export const projectsApi = {
  list: async (): Promise<ResearchProject[]> => {
    const response = await api.get('/projects');
    return response.data;
  },

  get: async (projectId: string): Promise<ResearchProject> => {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  create: async (request: CreateProjectRequest): Promise<ResearchProject> => {
    const response = await api.post('/projects', request);
    return response.data;
  },

  update: async (projectId: string, request: UpdateProjectRequest): Promise<ResearchProject> => {
    const response = await api.put(`/projects/${projectId}`, request);
    return response.data;
  },

  delete: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },

  getFiles: async (projectId: string): Promise<any> => {
    const response = await api.get(`/projects/${projectId}/files`);
    return response.data;
  },

  addFile: async (projectId: string, fileId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/files/${fileId}`);
  },

  removeFile: async (projectId: string, fileId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/files/${fileId}`);
  },

  getStats: async (): Promise<any> => {
    const response = await api.get('/projects/stats');
    return response.data;
  }
};

// Export the configured axios instance for custom requests
export default api;
