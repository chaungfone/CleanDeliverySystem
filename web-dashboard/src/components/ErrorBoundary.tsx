import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, ExternalLink } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  message: string;
  detail?: string;
  retryLabel?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

function looksLikeChunkLoadError(error: Error | null): boolean {
  if (!error) return false;
  const s = `${error.message} ${error.name} ${String(error)}`.toLowerCase();
  return (
    s.includes('failed to fetch dynamically imported module') ||
    s.includes('loading chunk') ||
    s.includes('chunkloaderror') ||
    s.includes('imported module') ||
    s.includes('could not find module') ||
    s.includes('failed to resolve module specifier')
  );
}

function looksLikeVercelProtectionError(error: Error | null): boolean {
  if (!error) return false;
  const s = `${error.message} ${error.name} ${String(error)}`.toLowerCase();
  return (
    s.includes('protected deployment') ||
    s.includes('deployment protection') ||
    s.includes('vercel') ||
    s.includes('451')
  );
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Page render error:', error, info);
  }

  handleRetry = () => {
    if (looksLikeChunkLoadError(this.state.error)) {
      const reload = () => {
        try {
          const url = new URL(window.location.href);
          url.searchParams.set('_v', String(Date.now()));
          window.location.assign(url.toString());
        } catch {
          window.location.reload();
        }
      };
      try {
        const keys = Object.keys(window.localStorage || {});
        keys.filter((k) => /chunk|vite|webpack|manifest/i.test(k)).forEach((k) => {
          try { window.localStorage.removeItem(k); } catch { /* ignore */ }
        });
        if (window.caches && typeof window.caches.keys === 'function') {
          window.caches.keys().then((names) => Promise.all(
            names.filter((n) => /vite|workbox|sw/.test(n)).map((n) => window.caches.delete(n)),
          )).finally(reload);
          return;
        }
      } catch { /* ignore */ }
      reload();
      return;
    }
    this.setState({ error: null });
  };

  openInNewTab = () => {
    window.open(window.location.href, '_blank', 'noopener,noreferrer');
  };

  render() {
    const { children, message, detail, retryLabel } = this.props;
    if (!this.state.error) return children;

    const isChunk = looksLikeChunkLoadError(this.state.error);
    const isVercelGate = looksLikeVercelProtectionError(this.state.error);
    const effectiveDetail = detail ?? String(this.state.error.message ?? this.state.error);
    const effectiveMessage =
      isChunk ? 'ဒီ page ကို ဖွင့်ရန် မလုံလောက်သေးပါ (Build အသစ်နဲ့ chunk ကွဲနေပါတယ်)'
      : isVercelGate ? 'Vercel Deployment Protection — ကိုယ်တိုင်ဝင်ရောက်ခွင့်ပြုပေးပါ'
      : message;
    const effectiveRetryLabel =
      isChunk ? 'Cache ရှင်းပြီး Page ပြန်ဖွင့်မည်'
      : isVercelGate ? 'Dashboard ကို Tab အသစ်ဖွင့်မည်'
      : retryLabel;

    return (
      <div className="flex items-center justify-center py-24 px-4 animate-fade-in">
        <div className="w-full max-w-md card p-8 text-center">
          <div className={`w-12 h-12 mx-auto mb-4 rounded-full flex items-center justify-center ${isVercelGate ? 'bg-amber-50' : 'bg-red-50'}`}>
            <AlertTriangle className={`w-6 h-6 ${isVercelGate ? 'text-amber-500' : 'text-red-500'}`} />
          </div>
          <h2 className="text-lg font-bold text-neutral-900">{effectiveMessage}</h2>
          <p className="text-sm text-neutral-500 mt-2 whitespace-pre-wrap break-words">
            {effectiveDetail}
          </p>

          {isVercelGate && (
            <div className="mt-4 text-xs text-left p-3 rounded-md bg-amber-50 border border-amber-100 text-amber-800">
              <p className="font-semibold mb-1">လုပ်ဆောင်ရန် (Vercel Dashboard):</p>
              <ol className="list-decimal list-inside space-y-0.5">
                <li>အောက်က "Tab အသစ်ဖွင့်မည်" ကို နှိပ်ပါ</li>
                <li>Password ပေးထားရင် Password ဖြည့်ပါ</li>
                <li>မလိုအပ်ပါက Project → Settings → Deployment Protection သို့သွားပါ</li>
                <li><strong>Password Protection → Disable</strong> နှင့် <strong>Standard Protection → Off</strong> လုပ်ပါ</li>
                <li>ပြီးရင် ဒီ Dashboard ကို refresh လုပ်ပြီး ပြန်ဝင်ပါ</li>
              </ol>
            </div>
          )}

          {isChunk && (
            <p className="mt-3 text-xs text-neutral-500">
              အကြောင်းအရင်း: Deploy အသစ်လုပ်ပြီးနောက် Browser Cache ထဲမှာ old chunk hash ကျန်နေပါတယ်။
              တစ်ချက် reload လုပ်လိုက်ရုံနဲ့ အဆင်ပြေသွားမှာ ဖြစ်ပါတယ်။
            </p>
          )}

          <div className="mt-6 flex flex-col sm:flex-row gap-2 justify-center">
            {effectiveRetryLabel && (
              isVercelGate ? (
                <>
                  <button onClick={this.openInNewTab} className="btn-primary inline-flex items-center justify-center gap-2">
                    <ExternalLink className="w-4 h-4" />
                    {effectiveRetryLabel}
                  </button>
                  <button onClick={this.handleRetry} className="btn-secondary inline-flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Refresh လုပ်မည်
                  </button>
                </>
              ) : (
                <button onClick={this.handleRetry} className="btn-primary inline-flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  {effectiveRetryLabel}
                </button>
              )
            )}
          </div>
        </div>
      </div>
    );
  }
}
