import { useMemo, useState } from 'react';
import { Search, Filter, CheckCircle2, Clock, Truck, Download } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, downloadFile } from '../lib/api';
import type { Driver, Order } from '../lib/types';
import { ErrorState, LoadingState, formatMoney, formatTime } from '../lib/ui';
import { useI18n } from '../i18n';

const STATUSES = ['ALL', 'PENDING', 'CONFIRMED', 'ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED'];

export default function OrderManagement() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [assigning, setAssigning] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: ['admin', 'orders'],
    queryFn: () => apiFetch<Order[]>('/admin/orders'),
  });
  const driversQuery = useQuery({
    queryKey: ['admin', 'drivers'],
    queryFn: () => apiFetch<Driver[]>('/admin/drivers'),
  });

  const assignMutation = useMutation({
    mutationFn: ({ orderId, driverId }: { orderId: string; driverId: string }) =>
      apiFetch<Order>(`/admin/orders/${orderId}/assign`, {
        method: 'POST',
        body: JSON.stringify({ driver_id: driverId }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'orders'] });
    },
  });

  const filtered = useMemo(() => {
    const rows = ordersQuery.data ?? [];
    return rows.filter((order) => {
      if (statusFilter !== 'ALL' && order.status !== statusFilter) return false;
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        order.id.toLowerCase().includes(q) ||
        (order.customer_name ?? '').toLowerCase().includes(q) ||
        (order.driver_name ?? '').toLowerCase().includes(q)
      );
    });
  }, [ordersQuery.data, search, statusFilter]);

  async function handleExport() {
    try {
      await downloadFile('/admin/reports/sales/csv', `sales_report_${new Date().toISOString().slice(0, 10)}.csv`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Export failed');
    }
  }

  if (ordersQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (ordersQuery.isError) {
    return <ErrorState error={ordersQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">{t('orders.title')}</h2>
          <p className="text-neutral-500 text-sm">{t('orders.subtitle')}</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          <Download className="w-4 h-4" />
          {t('orders.exportCsv')}
        </button>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 bg-white p-4 rounded-xl border border-neutral-90 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('orders.searchPlaceholder')}
            className="w-full pl-10 pr-4 py-2 border border-neutral-90 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-neutral-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-neutral-90 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s === 'ALL' ? t('common.all') : s}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-neutral-90 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[720px]">
            <thead className="bg-neutral-99 border-b border-neutral-90 text-sm text-neutral-500">
              <tr>
                <th className="px-6 py-4 font-medium">{t('orders.orderId')}</th>
                <th className="px-6 py-4 font-medium">{t('orders.customer')}</th>
                <th className="px-6 py-4 font-medium">{t('orders.status')}</th>
                <th className="px-6 py-4 font-medium">{t('orders.driver')}</th>
                <th className="px-6 py-4 font-medium">{t('orders.amount')}</th>
                <th className="px-6 py-4 font-medium">{t('orders.time')}</th>
                <th className="px-6 py-4 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-90">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center text-neutral-400">
                    {t('orders.noOrders')}
                  </td>
                </tr>
              )}
              {filtered.map((order) => (
                <tr key={order.id} className="hover:bg-neutral-99 transition-colors">
                  <td className="px-6 py-4 font-bold text-primary text-xs">{order.id}</td>
                  <td className="px-6 py-4 font-medium">
                    <div>{order.customer_name ?? '—'}</div>
                    {order.customer_phone && <div className="text-xs text-neutral-400">{order.customer_phone}</div>}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="px-6 py-4">
                    {order.status === 'PENDING' && !assigning ? (
                      <button
                        onClick={() => setAssigning(order.id)}
                        className="text-xs font-medium text-primary border border-primary/30 px-2 py-1 rounded-md hover:bg-accent"
                      >
                        {t('orders.assignDriver')}
                      </button>
                    ) : assigning === order.id ? (
                      <select
                        className="text-xs px-2 py-1 border border-neutral-90 rounded-md bg-white"
                        value=""
                        onChange={async (e) => {
                          const driverId = e.target.value;
                          setAssigning(null);
                          if (driverId) {
                            assignMutation.mutate({ orderId: order.id, driverId });
                          }
                        }}
                        onBlur={() => setAssigning(null)}
                        autoFocus
                      >
                        <option value="" disabled>
                          {t('orders.selectDriver')}
                        </option>
                        {(driversQuery.data ?? []).map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.full_name}
                          </option>
                        ))}
                        {(driversQuery.data ?? []).length === 0 && (
                          <option value="">{t('orders.noDrivers')}</option>
                        )}
                      </select>
                    ) : (
                      <span className={order.driver_name ? 'text-neutral-700' : 'text-red-500 font-medium'}>
                        {order.driver_name ?? t('common.unassigned')}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-medium">
                    {formatMoney(order.total_amount)} {t('common.mmk')}
                  </td>
                  <td className="px-6 py-4 text-neutral-500">{formatTime(order.created_at)}</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-xs text-neutral-300">
                      {order.items.length} {t('orders.itemsCount')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const configs: any = {
    PENDING: { color: 'text-orange-600 bg-orange-50', icon: Clock },
    CONFIRMED: { color: 'text-yellow-600 bg-yellow-50', icon: Clock },
    ASSIGNED: { color: 'text-blue-600 bg-blue-50', icon: Truck },
    IN_TRANSIT: { color: 'text-primary bg-accent', icon: Truck },
    DELIVERED: { color: 'text-green-600 bg-green-50', icon: CheckCircle2 },
    CANCELLED: { color: 'text-red-600 bg-red-50', icon: CheckCircle2 },
  };
  const config = configs[status] ?? { color: 'text-neutral-600 bg-neutral-90', icon: Clock };
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${config.color}`}>
      <Icon className="w-3.5 h-3.5" />
      {status}
    </span>
  );
}
