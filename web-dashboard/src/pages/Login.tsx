import { useState, type FormEvent, useEffect } from 'react';
import { Box, Phone, KeyRound, LogIn, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ADMIN_ROLES, useAuth } from '../lib/auth';
import { useI18n } from '../i18n';
import { LangSwitchCompact } from '../components/Sidebar';

export default function Login() {
  const { login, verifyOtp, user } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [debugOtp, setDebugOtp] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      navigate('/', { replace: true });
    }
  }, [user, navigate]);

  async function handleRequestOtp(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login(phone);
      if (res.debug_otp) setDebugOtp(res.debug_otp);
      setStep('otp');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('login.failRequestOtp'));
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await verifyOtp(phone, otp);
      // Redirect happens automatically via useEffect [user]
    } catch (err) {
      setError(err instanceof Error ? err.message : t('login.failVerify'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-neutral-99 flex items-center justify-center p-6 relative">
      <div className="absolute top-4 right-4">
        <LangSwitchCompact />
      </div>
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl border border-neutral-90 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-accent rounded-xl">
              <Box className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-primary">Clean Delivery</h1>
              <p className="text-sm text-neutral-500">{t('login.adminDashboard')}</p>
            </div>
          </div>

          {step === 'phone' ? (
            <form onSubmit={handleRequestOtp} className="mt-8 space-y-4">
              <label className="block text-sm font-medium text-neutral-600">{t('login.phoneNumber')}</label>
              <div className="relative">
                <Phone className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder={t('login.phonePlaceholder')}
                  required
                  pattern="^\+?[0-9]{9,15}$"
                  className="w-full pl-10 pr-4 py-2.5 border border-neutral-90 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              {error && <ErrorMessage message={error} />}
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-primary text-white py-2.5 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
              >
                <LogIn className="w-4 h-4" />
                {loading ? t('login.sending') : t('login.requestOtp')}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="mt-8 space-y-4">
              <p className="text-sm text-neutral-600">
                {t('login.enterCode')} <b>{phone}</b>
              </p>
              <div className="relative">
                <KeyRound className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder={t('login.otpPlaceholder')}
                  maxLength={6}
                  required
                  pattern="^[0-9]{6}$"
                  className="w-full pl-10 pr-4 py-2.5 border border-neutral-90 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              {debugOtp && (
                <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>
                    {t('login.debugOtp')} <b className="font-mono">{debugOtp}</b>
                  </span>
                </div>
              )}
              {loading && <p className="text-xs text-neutral-400 text-center">{t('login.verifyingHint')}</p>}
              {error && <ErrorMessage message={error} />}
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-primary text-white py-2.5 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
              >
                <LogIn className="w-4 h-4" />
                {loading ? t('login.verifying') : t('login.signIn')}
              </button>
              <button
                type="button"
                onClick={() => setStep('phone')}
                className="w-full text-center text-sm text-neutral-400 hover:text-neutral-600"
              >
                {t('common.back')}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
