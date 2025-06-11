// API Types for the Local AI Research Assistant

export interface SearchResult {
  content: string;
  source_file: string;
  chunk_id: string;
  similarity_score: number;
  metadata: Record<string, string | number | boolean>;
}

export interface QueryRequest {
  query: string;
  limit?: number;
  similarity_threshold?: number;
}

export interface QueryResponse {
  results: SearchResult[];
  total_results: number;
  query_time_ms: number;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  use_rag?: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SearchResult[];
  response_time_ms?: number;
}

export interface ChatResponse {
  response: string;
  sources?: SearchResult[];
  response_time_ms: number;
}

export interface FileInfo {
  filename: string;
  filepath: string;
  size: number;
  modified_date: string;
  file_type: string;
  chunks_count: number;
}

export interface FilesResponse {
  files: FileInfo[];
  total_files: number;
}

export interface IngestRequest {
  folder_path: string;
  file_types?: string[];
  recursive?: boolean;
}

export interface IngestResponse {
  status: string;
  files_processed: number;
  chunks_created: number;
  processing_time_ms: number;
}

export interface CorpusStatus {
  corpus_size: number;
  total_documents: number;
  total_chunks: number;
  last_updated: string | null;
  ingestion_in_progress: boolean;
}

// UI Component Types
export interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export interface ResultListProps {
  results: SearchResult[];
  loading?: boolean;
  onResultClick?: (result: SearchResult) => void;
}

export interface ChatUIProps {
  onSendMessage: (message: string) => void;
  messages: ChatMessage[];
  loading?: boolean;
  onStreamMessage?: (message: string) => void;
}

export interface FileViewerProps {
  file?: FileInfo;
  content?: string;
  onClose: () => void;
}

// Application State Types
export interface AppState {
  searchResults: SearchResult[];
  chatMessages: ChatMessage[];
  selectedFile: FileInfo | null;
  corpusStatus: CorpusStatus | null;
  isSearching: boolean;
  isChatting: boolean;
  error: string | null;
}

export type SearchMode = 'semantic' | 'chat' | 'files';

export interface SearchFilters {
  fileTypes: string[];
  dateRange: {
    start: string | null;
    end: string | null;
  };
  minSimilarity: number;
}
