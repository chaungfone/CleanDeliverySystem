import { useState } from 'react';
import { Navigate, BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import type { ReactNode } from 'react';
import Sidebar from './components/Sidebar';
import DashboardOverview from './pages/DashboardOverview';
import OrderManagement from './pages/OrderManagement';
import LiveFleetTracker from './pages/LiveFleetTracker';
import InventoryManager from './pages/InventoryManager';
import BranchManagement from './pages/BranchManagement';
import Products from './pages/Products';
import Staff from './pages/Staff';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { useAuth } from './lib/auth';
import { getToken } from './lib/api';
import { useI18n } from './i18n';

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-99 flex items-center justify-center text-neutral-400">
        {t('common.loading')}
      </div>
    );
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
      <Sidebar mobileOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <main className="lg:pl-64 p-4 sm:p-6 lg:p-8 pt-20 lg:pt-8">
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
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <Protected>
              <DashboardLayout />
            </Protected>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
