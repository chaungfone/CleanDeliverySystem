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

function LangSwitch() {
  const { lang, setLang } = useI18n();
  const next: Lang = lang === 'en' ? 'my' : 'en';
  return (
    <button
      onClick={() => setLang(next)}
      className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-neutral-500 hover:bg-neutral-99 hover:text-neutral-900 transition-colors"
      title={lang === 'en' ? 'Switch to မြန်မာ' : 'Switch to English'}
    >
      <Languages className="w-5 h-5" />
      <span className="font-medium">{lang === 'en' ? 'မြန်မာ' : 'English'}</span>
    </button>
  );
}

function NavList() {
  const { t } = useI18n();
  return (
    <nav className="flex-1 p-4 space-y-2">
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
              isActive
                ? 'bg-accent text-primary'
                : 'text-neutral-500 hover:bg-neutral-99 hover:text-neutral-900'
            )
          }
        >
          <item.icon className="w-5 h-5 shrink-0" />
          <span className="font-medium">{t(item.nameKey)}</span>
        </NavLink>
      ))}
    </nav>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <div className="p-4 border-t border-neutral-90 space-y-1">
      {user && (
        <p className="text-xs text-neutral-400 px-4 truncate">
          {t('nav.signedInAs')} <b className="text-neutral-600">{user.full_name}</b>
        </p>
      )}
      <LangSwitch />
      <button
        onClick={logout}
        className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-neutral-500 hover:bg-neutral-99 hover:text-red-600 transition-colors"
      >
        <LogOut className="w-5 h-5" />
        <span className="font-medium">{t('nav.logout')}</span>
      </button>
    </div>
  );
}

function Brand() {
  return (
    <div className="p-6 border-b border-neutral-90">
      <h1 className="text-xl font-bold text-primary flex items-center gap-2">
        <Box className="w-6 h-6 shrink-0" />
        Clean Delivery
      </h1>
    </div>
  );
}

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile top bar */}
      <header className="lg:hidden fixed inset-x-0 top-0 z-40 bg-white border-b border-neutral-90 flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-3">
          <button onClick={onClose} className="p-1 -ml-1 hover:bg-neutral-90 rounded-lg">
            <Menu className="w-6 h-6 text-primary" />
          </button>
          <h1 className="font-bold text-primary flex items-center gap-2">
            <Box className="w-5 h-5" />
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
            'absolute inset-0 bg-black/40 transition-opacity',
            mobileOpen ? 'opacity-100' : 'opacity-0'
          )}
          onClick={onClose}
        />
        <div
          className={cn(
            'absolute inset-y-0 left-0 w-72 max-w-[85vw] bg-white shadow-xl flex flex-col transition-transform duration-300',
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex items-center justify-between pr-3">
            <Brand />
            <button onClick={onClose} className="p-2 hover:bg-neutral-90 rounded-lg">
              <X className="w-5 h-5 text-neutral-400" />
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
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-neutral-90 text-sm font-medium text-neutral-600 hover:bg-neutral-99"
    >
      <Languages className="w-4 h-4" />
      {lang === 'en' ? 'မြန်မာ' : 'EN'}
    </button>
  );
}
