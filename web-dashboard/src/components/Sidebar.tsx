import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingCart,
  Truck,
  Box,
  Users,
  Settings,
  LogOut,
  Package,
  MapPin,
  Languages,
  Menu,
  X,
  Droplets,
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../lib/auth';
import { useI18n, type Lang } from '../i18n';

const navItems = [
  { nameKey: 'nav.overview', path: '/', icon: LayoutDashboard },
  { nameKey: 'nav.orders', path: '/orders', icon: ShoppingCart },
  { nameKey: 'nav.fleet', path: '/fleet', icon: Truck },
  { nameKey: 'nav.inventory', path: '/inventory', icon: Box },
  { nameKey: 'nav.products', path: '/products', icon: Package },
  { nameKey: 'nav.branches', path: '/branches', icon: MapPin },
  { nameKey: 'nav.staff', path: '/staff', icon: Users },
  { nameKey: 'nav.settings', path: '/settings', icon: Settings },
];

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

function BrandMark({ size = 'md' }: { size?: 'sm' | 'md' }) {
  const box = size === 'md' ? 'w-10 h-10 rounded-xl' : 'w-8 h-8 rounded-lg';
  const drop = size === 'md' ? 'w-5 h-5' : 'w-4 h-4';
  return (
    <div className={cn(box, 'bg-white/15 backdrop-blur-sm flex items-center justify-center ring-1 ring-white/25')}>
      <Droplets className={cn(drop, 'text-white fill-white/20')} />
    </div>
  );
}

function Brand() {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-500 to-secondary-600 px-6 py-6">
      {/* soft decorative waves */}
      <div className="pointer-events-none absolute -right-6 -top-8 w-28 h-28 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -right-2 top-10 w-16 h-16 rounded-full bg-white/10" />
      <div className="relative flex items-center gap-3">
        <BrandMark />
        <div className="leading-tight">
          <h1 className="text-lg font-bold text-white tracking-tight">Clean Delivery</h1>
          <p className="text-xs text-primary-100/90">Admin Console</p>
        </div>
      </div>
    </div>
  );
}

function NavList() {
  const { t } = useI18n();
  return (
    <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            cn(
              'group flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium transition-all duration-150',
              isActive
                ? 'bg-primary-100 text-primary-700 shadow-sm'
                : 'text-neutral-500 hover:bg-neutral-99 hover:text-neutral-900'
            )
          }
        >
          {({ isActive }) => (
            <>
              <item.icon
                className={cn(
                  'w-5 h-5 shrink-0 transition-colors',
                  isActive ? 'text-primary-600' : 'text-neutral-400 group-hover:text-primary-500'
                )}
              />
              <span className="truncate">{t(item.nameKey)}</span>
              {isActive && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-500" />}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

function LangSwitch() {
  const { lang, setLang } = useI18n();
  const next: Lang = lang === 'en' ? 'my' : 'en';
  return (
    <button
      onClick={() => setLang(next)}
      className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-neutral-500 hover:bg-neutral-99 hover:text-neutral-900 transition-colors"
      title={lang === 'en' ? 'Switch to မြန်မာ' : 'Switch to English'}
    >
      <Languages className="w-5 h-5" />
      <span className="font-medium">{lang === 'en' ? 'မြန်မာ' : 'English'}</span>
    </button>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <div className="px-3 py-4 border-t border-neutral-90 space-y-1">
      {user && (
        <div className="flex items-center gap-3 px-3.5 py-2 mb-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center text-white text-xs font-bold uppercase shrink-0">
            {user.full_name.charAt(0)}
          </div>
          <div className="min-w-0 leading-tight">
            <p className="text-xs font-semibold text-neutral-800 truncate">{user.full_name}</p>
            <p className="text-[11px] text-neutral-400">{t('nav.signedInAs')}</p>
          </div>
        </div>
      )}
      <LangSwitch />
      <button
        onClick={logout}
        className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-neutral-500 hover:bg-red-50 hover:text-red-600 transition-colors"
      >
        <LogOut className="w-5 h-5" />
        <span className="font-medium">{t('nav.logout')}</span>
      </button>
    </div>
  );
}

interface SidebarProps {
  mobileOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
}

export default function Sidebar({ mobileOpen, onOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile top bar */}
      <header className="lg:hidden fixed inset-x-0 top-0 z-40 bg-white/90 backdrop-blur border-b border-neutral-90 flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-3">
          <button onClick={onOpen} className="p-1 -ml-1 hover:bg-neutral-90 rounded-lg" aria-label="Open navigation">
            <Menu className="w-6 h-6 text-primary-600" />
          </button>
          <h1 className="font-bold text-primary-700 flex items-center gap-2">
            <Droplets className="w-5 h-5 fill-primary-100" />
            Clean Delivery
          </h1>
        </div>
        <LangSwitchCompact />
      </header>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 bg-white border-r border-neutral-90 flex-col">
        <Brand />
        <NavList />
        <SidebarFooter />
      </aside>

      {/* Mobile drawer */}
      <div className={cn('lg:hidden fixed inset-0 z-50', mobileOpen ? '' : 'pointer-events-none')}>
        <div
          className={cn(
            'absolute inset-0 bg-black/40 backdrop-blur-[2px] transition-opacity duration-300',
            mobileOpen ? 'opacity-100' : 'opacity-0'
          )}
          onClick={onClose}
        />
        <div
          className={cn(
            'absolute inset-y-0 left-0 w-72 max-w-[85vw] bg-white shadow-drawer flex flex-col transition-transform duration-300',
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}
          role="dialog"
          aria-modal="true"
        >
          <div className="relative">
            <Brand />
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg bg-white/15 text-white hover:bg-white/25"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <NavList />
          <SidebarFooter />
        </div>
      </div>
    </>
  );
}

export function LangSwitchCompact() {
  const { lang, setLang } = useI18n();
  return (
    <button
      onClick={() => setLang(lang === 'en' ? 'my' : 'en')}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-neutral-90 text-sm font-medium text-neutral-600 hover:bg-neutral-99 transition-colors"
    >
      <Languages className="w-4 h-4" />
      {lang === 'en' ? 'မြန်မာ' : 'EN'}
    </button>
  );
}
