import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  message: string;
  detail?: string;
  retryLabel?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

// Prevents a single page crash from unmounting the whole app into a blank
// screen (there was previously no boundary, so any render error produced an
// empty page). Renders a visible, styled fallback with a retry action instead.
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Page render error:', error, info);
  }

  handleRetry = () => {
    this.setState({ error: null });
  };

  render() {
    const { children, message, detail, retryLabel } = this.props;
    if (!this.state.error) return children;

    return (
      <div className="flex items-center justify-center py-24 px-4 animate-fade-in">
        <div className="w-full max-w-md card p-8 text-center">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-500" />
          </div>
          <h2 className="text-lg font-bold text-neutral-900">{message}</h2>
          <p className="text-sm text-neutral-500 mt-2">
            {detail ?? String(this.state.error.message ?? this.state.error)}
          </p>
          {retryLabel && (
            <button onClick={this.handleRetry} className="btn-primary mt-6">
              {retryLabel}
            </button>
          )}
        </div>
      </div>
    );
  }
}
