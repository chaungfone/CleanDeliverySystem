import { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { DollarSign, Package, Truck, Clock } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { Analytics, Order } from '../lib/types';
import { ErrorState, LoadingState, formatMoney } from '../lib/ui';
import { useI18n } from '../i18n';

function buildDailySeries(orders: Order[]): { name: string; revenue: number; orders: number }[] {
  const days: { name: string; revenue: number; orders: number }[] = [];
  const labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push({ name: labels[d.getDay()], revenue: 0, orders: 0 });
  }
  for (const order of orders) {
    const date = new Date(order.created_at);
    if (Number.isNaN(date.getTime())) continue;
    const today = new Date();
    const diff = Math.floor((today.setHours(0, 0, 0, 0) - date.setHours(0, 0, 0, 0)) / 86400000);
    const idx = 6 - diff;
    if (idx >= 0 && idx < 7) {
      days[idx].revenue += Number(order.total_amount) || 0;
      days[idx].orders += 1;
    }
  }
  return days;
}

export default function DashboardOverview() {
  const { t } = useI18n();
  const analyticsQuery = useQuery({
    queryKey: ['admin', 'analytics'],
    queryFn: () => apiFetch<Analytics>('/admin/dashboard/analytics'),
  });
  const ordersQuery = useQuery({
    queryKey: ['admin', 'orders'],
    queryFn: () => apiFetch<Order[]>('/admin/orders'),
  });

  const series = useMemo(() => buildDailySeries(ordersQuery.data ?? []), [ordersQuery.data]);

  if (analyticsQuery.isLoading || ordersQuery.isLoading) {
    return <LoadingState label={t('common.loading')} />;
  }
  if (analyticsQuery.isError || ordersQuery.isError) {
    return (
      <ErrorState
        error={analyticsQuery.error ?? ordersQuery.error}
        fallback={t('errors.failedToLoad')}
      />
    );
  }

  const analytics = analyticsQuery.data;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">{t('dashboard.title')}</h2>
        <p className="text-neutral-500 text-sm">{t('dashboard.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title={t('dashboard.revenue')}
          value={`${formatMoney(analytics?.total_revenue ?? '0')} MMK`}
          icon={DollarSign}
          trend={`${analytics?.delivered_volume ?? 0} ${t('dashboard.deliveredCount')}`}
        />
        <StatCard
          title={t('dashboard.bottlesDelivered')}
          value={String(analytics?.delivered_volume ?? 0)}
          icon={Package}
          subValue={`${t('dashboard.period')}: ${analytics?.period ?? 'daily'}`}
        />
        <StatCard
          title={t('dashboard.activeDrivers')}
          value={String(analytics?.active_drivers ?? 0)}
          icon={Truck}
          subValue={t('dashboard.reportingLocation')}
        />
        <StatCard
          title={t('dashboard.pendingDeliveries')}
          value={String(analytics?.pending_deliveries ?? 0)}
          icon={Clock}
          subValue={t('dashboard.awaitingDelivery')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl border border-neutral-90 shadow-sm">
          <h3 className="text-lg font-bold mb-6">{t('dashboard.salesTrend')}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="revenue" stroke="#2196F3" fill="#E3F2FD" name={t('dashboard.revenueLabel')} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-neutral-90 shadow-sm">
          <h3 className="text-lg font-bold mb-6">{t('dashboard.ordersPerDay')}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="orders" fill="#009688" radius={[4, 4, 0, 0]} name={t('dashboard.ordersLabel')} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, subValue }: any) {
  return (
    <div className="bg-white p-6 rounded-xl border border-neutral-90 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-accent rounded-lg">
          <Icon className="w-6 h-6 text-primary" />
        </div>
        {trend && (
          <span className="text-xs font-bold text-green-700 bg-green-50 px-2 py-1 rounded-full">
            {trend}
          </span>
        )}
      </div>
      <p className="text-neutral-500 text-sm font-medium">{title}</p>
      <h4 className="text-2xl font-bold mt-1">{value}</h4>
      {subValue && <p className="text-xs text-neutral-400 mt-1">{subValue}</p>}
    </div>
  );
}
