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
  FileInfo
} from '../types';

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

  open: async (fileId: string): Promise<void> => {
    await api.post(`/files/open/${fileId}`);
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

// Export the configured axios instance for custom requests
export default api;
