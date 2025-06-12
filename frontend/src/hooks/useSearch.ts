import { useState, useCallback, useRef } from 'react';
import { queryApi } from '../api';
import type { SearchResult } from '../types';

export const useSearch = () => {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    setIsSearching(true);
    setError(null);

    try {
      const response = await queryApi.query(
        { query: query.trim() },
        { signal: abortControllerRef.current.signal }
      );
      setResults(response.results);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMessage = err.response?.data?.detail || 'Search failed';
        setError(errorMessage);
        console.error('Search error:', err);
      }
    } finally {
      setIsSearching(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    results,
    isSearching,
    error,
    search,
    clearResults
  };
};
