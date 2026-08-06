import { AlertCircle, WifiOff, ShieldAlert, ServerCrash, SearchX, Clock } from 'lucide-react';
import { useI18n } from '../i18n';
import { ApiError } from './api';

export function LoadingState({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-20 text-neutral-400 animate-pulse">
      {label}
    </div>
  );
}

interface ResolvedError {
  icon: any;
  message: string;
  detail?: string;
}

function describeError(err: unknown, fallback: string, t: (key: string) => string): ResolvedError {
  if (err instanceof ApiError) {
    switch (err.status) {
      case 0:
        return /timed out/i.test(err.message)
          ? { icon: Clock, message: t('errors.timeout'), detail: err.message }
          : { icon: WifiOff, message: t('errors.network'), detail: err.message };
      case 401:
        return { icon: ShieldAlert, message: t('errors.unauthorized'), detail: err.message };
      case 403:
        return { icon: ShieldAlert, message: t('errors.forbidden'), detail: err.message };
      case 404:
        return { icon: SearchX, message: t('errors.notFound'), detail: err.message };
      default:
        if (err.status >= 500) {
          return { icon: ServerCrash, message: t('errors.server'), detail: err.message };
        }
        return { icon: AlertCircle, message: fallback, detail: err.message };
    }
  }
  return { icon: WifiOff, message: t('errors.network'), detail: err instanceof Error ? err.message : undefined };
}

interface ErrorStateProps {
  error?: unknown;
  fallback?: string;
  message?: string;
}

export function ErrorState({ error, fallback = '', message }: ErrorStateProps) {
  const { t } = useI18n();
  const resolved: ResolvedError =
    error != null
      ? describeError(error, fallback, t)
      : { icon: AlertCircle, message: message ?? fallback };
  const Icon = resolved.icon;
  return (
    <div className="flex items-center justify-center py-20 px-4">
      <div className="flex items-start gap-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 max-w-lg">
        <Icon className="w-5 h-5 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">{resolved.message}</p>
          {resolved.detail && (
            <p className="text-xs text-red-400 mt-1 break-words">
              {t('errors.details')}: {resolved.detail}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function formatMoney(value: string | number): string {
  const num = typeof value === 'string' ? Number(value) : value;
  if (Number.isNaN(num)) return '0';
  return num.toLocaleString('en-US');
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
