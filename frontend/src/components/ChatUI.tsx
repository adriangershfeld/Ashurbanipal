import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import type { ChatUIProps, ChatMessage } from '../types';

const ChatUI: React.FC<ChatUIProps> = ({ 
  onSendMessage, 
  messages, 
  loading = false 
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !loading) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-ui">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <Bot size={48} className="welcome-icon" />
            <h3>Ask me anything about your documents</h3>
            <p>I'll search through your corpus and provide contextual answers.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))
        )}
        
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <Loader2 size={16} className="spinning" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-container">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            className="chat-input"
            rows={1}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || loading}
            className="send-button"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
      
      <style jsx>{`
        .chat-ui {
          display: flex;
          flex-direction: column;
          height: 100%;
          max-height: 600px;
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .chat-welcome {
          text-align: center;
          padding: 40px 20px;
          color: #6b7280;
        }
        
        .welcome-icon {
          margin-bottom: 16px;
          opacity: 0.7;
        }
        
        .chat-welcome h3 {
          margin: 0 0 8px 0;
          color: #9ca3af;
        }
        
        .chat-welcome p {
          margin: 0;
          font-size: 14px;
        }
        
        .chat-input-form {
          padding: 16px 20px;
          border-top: 1px solid #374151;
        }
        
        .chat-input-container {
          display: flex;
          align-items: flex-end;
          gap: 12px;
          background: #1a1a2e;
          border: 2px solid #16213e;
          border-radius: 12px;
          padding: 8px 12px;
          transition: border-color 0.2s ease;
        }
        
        .chat-input-container:focus-within {
          border-color: #4f46e5;
        }
        
        .chat-input {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: #f3f4f6;
          font-size: 14px;
          line-height: 1.5;
          resize: none;
          min-height: 20px;
          max-height: 120px;
          padding: 8px 0;
        }
        
        .chat-input::placeholder {
          color: #6b7280;
        }
        
        .send-button {
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px;
          cursor: pointer;
          transition: background-color 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .send-button:hover:not(:disabled) {
          background: #4338ca;
        }
        
        .send-button:disabled {
          background: #374151;
          cursor: not-allowed;
        }
        
        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #6b7280;
          font-style: italic;
        }
        
        .spinning {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

interface ChatMessageProps {
  message: ChatMessage;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="message-content">
        {message.content}
      </div>
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
      
      <style jsx>{`
        .message {
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }
        
        .message.user {
          flex-direction: row-reverse;
        }
        
        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .message.user .message-avatar {
          background: #4f46e5;
          color: white;
        }
        
        .message.assistant .message-avatar {
          background: #374151;
          color: #9ca3af;
        }
        
        .message-content {
          background: #1a1a2e;
          padding: 12px 16px;
          border-radius: 16px;
          max-width: 70%;
          word-wrap: break-word;
          line-height: 1.5;
          color: #f3f4f6;
        }
        
        .message.user .message-content {
          background: #4f46e5;
          color: white;
        }
        
        .message-timestamp {
          font-size: 11px;
          color: #6b7280;
          align-self: flex-end;
          margin-bottom: 4px;
        }
        
        .message.user .message-timestamp {
          order: -1;
          margin-right: 8px;
        }
        
        .message.assistant .message-timestamp {
          margin-left: 8px;
        }
      `}</style>
    </div>
  );
};

export default ChatUI;
