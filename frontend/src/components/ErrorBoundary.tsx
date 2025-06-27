/// <reference types="vite/client" />

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-content">            <AlertTriangle size={48} className="error-icon" />            <h2>Something went wrong</h2>
            <p>The application encountered an unexpected error.</p>
            
            {this.state.error && (
              <details className="error-details">
                <summary>Error Details</summary>
                <pre className="error-stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            
            <button 
              onClick={this.handleReset}
              className="retry-button"
            >
              <RefreshCw size={16} />
              Try Again
            </button>
          </div>

          <style jsx>{`
            .error-boundary {
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              background: #0f0f23;
              color: #cccccc;
              padding: 20px;
            }
            
            .error-content {
              text-align: center;
              max-width: 500px;
            }
            
            .error-icon {
              color: #f87171;
              margin-bottom: 16px;
            }
            
            .error-content h2 {
              color: #f3f4f6;
              margin: 0 0 12px 0;
              font-size: 24px;
            }
            
            .error-content p {
              color: #9ca3af;
              margin: 0 0 24px 0;
              line-height: 1.6;
            }
            
            .error-details {
              margin: 20px 0;
              text-align: left;
            }
            
            .error-details summary {
              cursor: pointer;
              color: #9ca3af;
              margin-bottom: 12px;
            }
            
            .error-stack {
              background: #1a1a2e;
              border: 1px solid #374151;
              border-radius: 6px;
              padding: 16px;
              font-size: 12px;
              color: #f87171;
              overflow: auto;
              max-height: 200px;
            }
            
            .retry-button {
              display: flex;
              align-items: center;
              gap: 8px;
              background: #4f46e5;
              color: white;
              border: none;
              border-radius: 8px;
              padding: 12px 24px;
              cursor: pointer;
              font-weight: 500;
              transition: background-color 0.2s ease;
              margin: 0 auto;
            }
            
            .retry-button:hover {
              background: #4338ca;
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
