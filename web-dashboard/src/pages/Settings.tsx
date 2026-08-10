import { Server, User, BookOpen, ShieldCheck, RefreshCw, LogOut, Globe } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../lib/auth';
import { useI18n, type Lang } from '../i18n';
import API_BASE_URL from '../lib/api';

const DOCS_URL = `${new URL(API_BASE_URL).origin}/docs`;

export default function Settings() {
  const { user, logout } = useAuth();
  const { t, lang, setLang } = useI18n();
  const queryClient = useQueryClient();

  function handleRefresh() {
    queryClient.invalidateQueries();
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('settings.title')}</h2>
        <p className="text-neutral-500 text-sm mt-0.5">{t('settings.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Environment */}
        <div className="card p-6">
          <h3 className="font-bold flex items-center gap-2 mb-5 text-neutral-900">
            <span className="p-1.5 rounded-lg bg-primary-100">
              <Server className="w-4 h-4 text-primary-600" />
            </span>
            {t('settings.systemEnv')}
          </h3>
          <div className="space-y-3 text-sm">
            <Row label={`${t('settings.apiBase')}:`} value={API_BASE_URL} mono />
            <Row label={`${t('common.role')}:`} value="ADMIN" />
            <div className="flex items-center justify-between border border-neutral-90 rounded-xl p-3 hover:bg-neutral-99 transition-colors">
              <span className="text-neutral-500">
                <Globe className="w-4 h-4 inline mr-2" />
                {lang === 'en' ? 'English' : 'မြန်မာ'}
              </span>
              <button
                onClick={() => setLang(lang === 'en' ? 'my' : ('en' as Lang))}
                className="px-3 py-1.5 rounded-lg bg-primary-100 text-primary-700 font-medium hover:bg-primary-200 transition-colors"
              >
                {lang === 'en' ? 'မြန်မာ' : 'English'}
              </button>
            </div>
          </div>
        </div>

        {/* Current User */}
        <div className="card p-6">
          <h3 className="font-bold flex items-center gap-2 mb-5 text-neutral-900">
            <span className="p-1.5 rounded-lg bg-secondary-100">
              <User className="w-4 h-4 text-secondary-600" />
            </span>
            {t('settings.currentUser')}
          </h3>
          {user ? (
            <div className="space-y-3 text-sm">
              <Row label={`${t('common.name')}:`} value={user.full_name} />
              <Row label={`${t('common.phone')}:`} value={user.phone_number} mono />
              <Row label={`${t('common.role')}:`} value={user.role} />
              <Row label={`${t('settings.signedIn')}:`} value={new Date(user.created_at).toLocaleString()} />
              <div className="border-t border-neutral-90 pt-3">
                <p className="text-neutral-400 text-xs">{t('settings.userId')}</p>
                <p className="font-mono text-xs text-neutral-600 break-all">{user.id}</p>
              </div>
            </div>
          ) : (
            <p className="text-neutral-400 text-sm">{t('login.notAdmin')}</p>
          )}
        </div>

        {/* Backend & Docs */}
        <div className="card p-6">
          <h3 className="font-bold flex items-center gap-2 mb-5 text-neutral-900">
            <span className="p-1.5 rounded-lg bg-teal-50">
              <BookOpen className="w-4 h-4 text-teal-600" />
            </span>
            {t('settings.backendDocs')}
          </h3>
          <div className="space-y-3">
            <a
              href={DOCS_URL}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between border border-neutral-90 rounded-xl p-3 hover:bg-neutral-99 hover:border-primary-200 transition-colors"
            >
              <span className="text-sm font-medium">{t('settings.openApiDocs')}</span>
              <span className="text-xs text-neutral-400 font-mono">/docs</span>
            </a>
            <div className="flex items-center justify-between border border-neutral-90 rounded-xl p-3">
              <span className="text-sm font-medium flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-green-600" />
                {t('settings.health')}
              </span>
              <span className="text-xs font-bold text-green-700 bg-green-50 px-2 py-1 rounded-full">200 OK</span>
            </div>
          </div>
        </div>

        {/* Account Actions */}
        <div className="card p-6">
          <h3 className="font-bold mb-5 text-neutral-900">{t('settings.accountActions')}</h3>
          <div className="space-y-3">
            <button
              onClick={handleRefresh}
              className="w-full flex items-center gap-3 px-4 py-3 border border-neutral-90 rounded-xl text-sm font-medium text-neutral-700 hover:bg-neutral-99 transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-primary-600" />
              {t('settings.refreshData')}
              <span className="ml-auto text-xs text-neutral-400">{t('settings.refreshHint')}</span>
            </button>
            <button
              onClick={logout}
              className="w-full flex items-center gap-3 px-4 py-3 border border-red-100 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {t('nav.logout')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-neutral-500 shrink-0">{label}</span>
      <span className={mono ? 'font-mono text-xs text-neutral-700 break-all text-right' : 'font-medium text-neutral-800 text-right'}>
        {value}
      </span>
    </div>
  );
}
