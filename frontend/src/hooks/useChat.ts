import { useState, useCallback } from 'react';
import { queryApi } from '../api';
import type { ChatMessage } from '../types';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsChatting(true);
    setError(null);

    try {
      const response = await queryApi.chat({
        message: content.trim(),
        history: messages,
        use_rag: true
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        sources: response.sources,
        response_time_ms: response.response_time_ms
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Chat request failed';
      setError(errorMessage);
      console.error('Chat error:', err);
    } finally {
      setIsChatting(false);
    }
  }, [messages]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isChatting,
    error,
    sendMessage,
    clearMessages
  };
};
