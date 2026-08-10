import { useState, type FormEvent, useEffect } from 'react';
import { Droplets, Phone, KeyRound, LogIn, AlertCircle, Truck, Package, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ADMIN_ROLES, useAuth } from '../lib/auth';
import { useI18n } from '../i18n';
import { LangSwitchCompact } from '../components/Sidebar';

export default function Login() {
  const { login, verifyOtp, demoLogin, user } = useAuth();
  const navigate = useNavigate();
  const { t, lang } = useI18n();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [debugOtp, setDebugOtp] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && ADMIN_ROLES.includes(user.role)) {
      navigate('/', { replace: true });
    }
  }, [user, navigate]);

  async function handleRequestOtp(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Try the real backend flow with a short timeout first.
      const res = await login(phone, { timeoutMs: 8000 });
      if (res.debug_otp) {
        await verifyOtp(phone, res.debug_otp);
        return;
      }
      setDebugOtp('');
      setStep('otp');
    } catch {
      // Backend OTP flow unavailable → temporary auto demo login so the UI
      // can be used end-to-end. Remove once OTP login is live in production.
      demoLogin(phone);
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
    <div className="min-h-screen bg-neutral-99 flex">
      {/* Brand panel (desktop) */}
      <aside className="hidden lg:flex w-1/2 relative overflow-hidden bg-gradient-to-br from-primary-700 via-primary-600 to-secondary-600 flex-col justify-between p-12">
        <div className="pointer-events-none absolute -left-24 -top-24 w-96 h-96 rounded-full bg-white/10" />
        <div className="pointer-events-none absolute right-0 bottom-0 translate-x-1/3 translate-y-1/3 w-[28rem] h-[28rem] rounded-full bg-white/10" />
        <div className="pointer-events-none absolute left-1/3 top-1/2 w-64 h-64 rounded-full bg-white/5" />

        <div className="relative flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center ring-1 ring-white/25">
            <Droplets className="w-6 h-6 text-white fill-white/20" />
          </div>
          <div className="leading-tight">
            <h1 className="text-2xl font-bold text-white tracking-tight">Clean Delivery</h1>
            <p className="text-primary-100 text-sm">{t('login.adminDashboard')}</p>
          </div>
        </div>

        <div className="relative max-w-md">
          <h2 className="text-4xl font-bold text-white leading-tight tracking-tight">
            {lang === 'my' ? 'သန့်ရှင်းသောရေ၊\nထိရောက်သော ပို့ဆောင်မှု' : 'Clean water.\nDelivered right.'}
          </h2>
          <p className="mt-4 text-primary-100 text-lg leading-relaxed">
            {lang === 'my'
              ? 'ဌာနခွဲများ၊ အော်ဒါများနှင့် ယာဉ်မောင်းများကို တစ်နေရာတည်းမှ စီမံခန့်ခွဲပါ။'
              : 'Manage branches, orders, and drivers from one place.'}
          </p>

          <ul className="mt-10 space-y-5">
            <li className="flex items-center gap-4 text-white">
              <span className="w-10 h-10 rounded-xl bg-white/15 ring-1 ring-white/20 flex items-center justify-center shrink-0">
                <Truck className="w-5 h-5" />
              </span>
              <div>
                <p className="font-semibold">{lang === 'my' ? 'တိုက်ရိုက် ယာဉ်ခြေရာခံ' : 'Live fleet tracking'}</p>
                <p className="text-primary-100 text-sm">{lang === 'my' ? 'ပို့ဆောင်မှု အခြေအနေ တစ်ချက်ကြည့်ရင်သိရ' : 'See every delivery in real time'}</p>
              </div>
            </li>
            <li className="flex items-center gap-4 text-white">
              <span className="w-10 h-10 rounded-xl bg-white/15 ring-1 ring-white/20 flex items-center justify-center shrink-0">
                <Package className="w-5 h-5" />
              </span>
              <div>
                <p className="font-semibold">{lang === 'my' ? 'ပစ္စည်းစာရင်း ထိန်းချုပ်မှု' : 'Inventory control'}</p>
                <p className="text-primary-100 text-sm">{lang === 'my' ? 'ပုလင်း၊ အဖုံးနှင့် ရေလီတာများကို ချိန်ညှိပါ' : 'Reconcile bottles, caps and water'}</p>
              </div>
            </li>
            <li className="flex items-center gap-4 text-white">
              <span className="w-10 h-10 rounded-xl bg-white/15 ring-1 ring-white/20 flex items-center justify-center shrink-0">
                <MapPin className="w-5 h-5" />
              </span>
              <div>
                <p className="font-semibold">{lang === 'my' ? 'ဌာနခွဲ အလိုက် စီမံခန့်ခွဲ' : 'Branch operations'}</p>
                <p className="text-primary-100 text-sm">{lang === 'my' ? 'ဌာနခွဲတိုင်း၏ ကိန်းဂဏန်းများကို စောင့်ကြည့်ပါ' : 'Monitor every branch at a glance'}</p>
              </div>
            </li>
          </ul>
        </div>

        <p className="relative text-primary-200 text-sm">© {new Date().getFullYear()} Clean Delivery Logistics</p>
      </aside>

      {/* Form panel */}
      <main className="flex-1 flex items-center justify-center p-6 relative" aria-label="Sign in">
        <div className="absolute top-4 right-4">
          <LangSwitchCompact />
        </div>
        <div className="w-full max-w-md animate-fade-in-up">
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-600 to-secondary-600">
              <Droplets className="w-6 h-6 text-white fill-white/20" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-primary-700 tracking-tight">Clean Delivery</h1>
              <p className="text-sm text-neutral-500">{t('login.adminDashboard')}</p>
            </div>
          </div>

          <div className="card p-8 sm:p-10">
            <h2 className="text-2xl font-bold text-neutral-900 tracking-tight">
              {step === 'phone' ? t('login.phoneNumber') : t('login.enterCode')}
            </h2>
            <p className="text-sm text-neutral-500 mt-1 mb-8">
              {step === 'phone'
                ? lang === 'my' ? 'ဆက်လက်ရန် သင့်ဖုန်းနံပါတ်ဖြင့် OTP တောင်းယူပါ' : 'Request a one-time code to continue.'
                : `${t('login.enterCode')} ${phone}`}
            </p>

            {step === 'phone' ? (
              <form onSubmit={handleRequestOtp} className="space-y-5">
                <label className="block">
                  <span className="field-label">{t('login.phoneNumber')}</span>
                  <div className="relative">
                    <Phone className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
                    <input
                      type="tel"
                      name="phone_number"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder={t('login.phonePlaceholder')}
                      required
                      pattern="^\+?[0-9]{9,15}$"
                      className="input input-with-icon"
                      autoComplete="tel"
                    />
                  </div>
                </label>
                {error && <ErrorMessage message={error} />}
                <button type="submit" disabled={loading} className="btn-primary w-full">
                  <LogIn className="w-4 h-4" />
                  {loading ? t('login.sending') : t('login.requestOtp')}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-5">
                <label className="block">
                  <span className="field-label">OTP</span>
                  <div className="relative">
                    <KeyRound className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
                    <input
                      type="text"
                      name="otp"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                      placeholder={t('login.otpPlaceholder')}
                      maxLength={6}
                      required
                      pattern="^[0-9]{6}$"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      className="input input-with-icon font-mono tracking-[0.4em] text-center pl-10"
                    />
                  </div>
                </label>
                {debugOtp && (
                  <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>
                      {t('login.debugOtp')} <b className="font-mono">{debugOtp}</b>
                    </span>
                  </div>
                )}
                {loading && <p className="text-xs text-neutral-400 text-center animate-pulse">{t('login.verifyingHint')}</p>}
                {error && <ErrorMessage message={error} />}
                <button type="submit" disabled={loading} className="btn-primary w-full">
                  <LogIn className="w-4 h-4" />
                  {loading ? t('login.verifying') : t('login.signIn')}
                </button>
                <button
                  type="button"
                  onClick={() => setStep('phone')}
                  className="w-full text-center text-sm text-neutral-400 hover:text-neutral-600 transition-colors"
                >
                  {t('common.back')}
                </button>
              </form>
            )}
          </div>

          <p className="text-center text-xs text-neutral-400 mt-6">
            {lang === 'my' ? 'စီမံခန့်ခွဲသူ အကောင့်သာ ဝင်ရောက်နိုင်ပါသည်။' : 'Authorized administrators only.'}
          </p>
        </div>
      </main>
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl p-3 animate-fade-in" role="alert">
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
