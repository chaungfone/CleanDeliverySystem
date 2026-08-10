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

const CHART_TOOLTIP = {
  contentStyle: {
    borderRadius: 12,
    border: '1px solid #E4E8EF',
    boxShadow: '0 10px 24px -6px rgba(16,24,40,0.12)',
    fontSize: 13,
  },
};

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
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('dashboard.title')}</h2>
        <p className="text-neutral-500 text-sm mt-0.5">{t('dashboard.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <StatCard
          title={t('dashboard.revenue')}
          value={`${formatMoney(analytics?.total_revenue ?? '0')} MMK`}
          icon={DollarSign}
          trend={`${analytics?.delivered_volume ?? 0} ${t('dashboard.deliveredCount')}`}
          gradient="from-primary-500 to-primary-600"
        />
        <StatCard
          title={t('dashboard.bottlesDelivered')}
          value={String(analytics?.delivered_volume ?? 0)}
          icon={Package}
          subValue={`${t('dashboard.period')}: ${analytics?.period ?? 'daily'}`}
          gradient="from-secondary-500 to-secondary-600"
        />
        <StatCard
          title={t('dashboard.activeDrivers')}
          value={String(analytics?.active_drivers ?? 0)}
          icon={Truck}
          subValue={t('dashboard.reportingLocation')}
          gradient="from-amber-400 to-orange-500"
        />
        <StatCard
          title={t('dashboard.pendingDeliveries')}
          value={String(analytics?.pending_deliveries ?? 0)}
          icon={Clock}
          subValue={t('dashboard.awaitingDelivery')}
          gradient="from-slate-400 to-slate-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-bold text-neutral-900 mb-6">{t('dashboard.salesTrend')}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series}>
                <defs>
                  <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#1976D2" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#1976D2" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E8EF" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4B5563' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#4B5563' }} axisLine={false} tickLine={false} width={60} />
                <Tooltip {...CHART_TOOLTIP} />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#1976D2"
                  strokeWidth={2.5}
                  fill="url(#revenueFill)"
                  name={t('dashboard.revenueLabel')}
                  activeDot={{ r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-bold text-neutral-900 mb-6">{t('dashboard.ordersPerDay')}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E8EF" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4B5563' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#4B5563' }} axisLine={false} tickLine={false} width={60} />
                <Tooltip {...CHART_TOOLTIP} cursor={{ fill: 'rgba(25,118,210,0.06)' }} />
                <Bar dataKey="orders" fill="#009688" radius={[6, 6, 0, 0]} maxBarSize={42} name={t('dashboard.ordersLabel')} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, subValue, gradient }: any) {
  return (
    <div className="card p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} shadow-pop`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <span className="text-xs font-bold text-green-700 bg-green-50 px-2 py-1 rounded-full">
            {trend}
          </span>
        )}
      </div>
      <p className="text-neutral-500 text-sm font-medium">{title}</p>
      <h4 className="text-2xl font-bold mt-1 text-neutral-900 tracking-tight">{value}</h4>
      {subValue && <p className="text-xs text-neutral-400 mt-1">{subValue}</p>}
    </div>
  );
}
