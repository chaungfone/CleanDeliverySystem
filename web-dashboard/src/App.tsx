import { Suspense, lazy, useState } from 'react';
import { Navigate, BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import type { ReactNode } from 'react';
import Sidebar from './components/Sidebar';
import { useAuth } from './lib/auth';
import { getToken } from './lib/api';
import { useI18n } from './i18n';
import { Loader2 } from 'lucide-react';

// Route-level code splitting: each page becomes its own lazy chunk so the
// initial bundle stays small and heavy deps (e.g. victory charts) load on demand.
const DashboardOverview = lazy(() => import('./pages/DashboardOverview'));
const OrderManagement = lazy(() => import('./pages/OrderManagement'));
const LiveFleetTracker = lazy(() => import('./pages/LiveFleetTracker'));
const InventoryManager = lazy(() => import('./pages/InventoryManager'));
const BranchManagement = lazy(() => import('./pages/BranchManagement'));
const Products = lazy(() => import('./pages/Products'));
const Staff = lazy(() => import('./pages/Staff'));
const Settings = lazy(() => import('./pages/Settings'));
const Login = lazy(() => import('./pages/Login'));

function PageLoader() {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-neutral-99 flex flex-col items-center justify-center text-neutral-400 animate-fade-in" role="status">
      <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-3" />
      <span className="text-sm font-medium">{t('common.loading')}</span>
    </div>
  );
}

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const { t } = useI18n();
  if (loading) {
    return <PageLoader />;
  }
  if (!user || !getToken()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function DashboardLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  return (
    <div className="min-h-screen bg-neutral-99">
      <Sidebar mobileOpen={drawerOpen} onOpen={() => setDrawerOpen(true)} onClose={() => setDrawerOpen(false)} />
      <main aria-label="Main content" className="lg:pl-64 p-4 sm:p-6 lg:p-8 pt-20 lg:pt-8 max-w-[1600px]">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<DashboardOverview />} />
            <Route path="/orders" element={<OrderManagement />} />
            <Route path="/fleet" element={<LiveFleetTracker />} />
            <Route path="/inventory" element={<InventoryManager />} />
            <Route path="/products" element={<Products />} />
            <Route path="/branches" element={<BranchManagement />} />
            <Route path="/staff" element={<Staff />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route
            path="/login"
            element={
              <main aria-label="Main content" className="min-h-screen">
                <Login />
              </main>
            }
          />
          <Route
            path="/*"
            element={
              <Protected>
                <DashboardLayout />
              </Protected>
            }
          />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
