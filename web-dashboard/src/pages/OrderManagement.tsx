import { useMemo, useState } from 'react';
import { Search, Filter, CheckCircle2, Clock, Truck, Download, XCircle } from 'lucide-react';
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
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('orders.title')}</h2>
          <p className="text-neutral-500 text-sm mt-0.5">{t('orders.subtitle')}</p>
        </div>
        <button onClick={handleExport} className="btn-primary">
          <Download className="w-4 h-4" />
          {t('orders.exportCsv')}
        </button>
      </div>

      <div className="card p-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        <div className="relative flex-1">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('orders.searchPlaceholder')}
            className="input input-with-icon"
            aria-label={t('common.search')}
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-neutral-400" aria-hidden />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="select w-auto"
            aria-label={t('common.filter')}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s === 'ALL' ? t('common.all') : s}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-card">
        <div className="table-wrap">
          <table className="w-full text-left min-w-[760px]">
            <thead className="table-head">
              <tr>
                <th>{t('orders.orderId')}</th>
                <th>{t('orders.customer')}</th>
                <th>{t('orders.status')}</th>
                <th>{t('orders.driver')}</th>
                <th>{t('orders.amount')}</th>
                <th>{t('orders.time')}</th>
                <th className="text-right">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-neutral-400">
                    {t('orders.noOrders')}
                  </td>
                </tr>
              )}
              {filtered.map((order) => (
                <tr key={order.id} className="table-row">
                  <td className="table-cell font-bold text-primary-600 text-xs whitespace-nowrap">{order.id}</td>
                  <td className="table-cell font-medium">
                    <div>{order.customer_name ?? '—'}</div>
                    {order.customer_phone && <div className="text-xs text-neutral-400">{order.customer_phone}</div>}
                  </td>
                  <td className="table-cell">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="table-cell">
                    {order.status === 'PENDING' && !assigning ? (
                      <button
                        onClick={() => setAssigning(order.id)}
                        className="text-xs font-semibold text-primary-600 border border-primary-200 px-2.5 py-1 rounded-lg hover:bg-primary-50 transition-colors"
                      >
                        {t('orders.assignDriver')}
                      </button>
                    ) : assigning === order.id ? (
                      <select
                        className="select w-auto text-xs py-1.5"
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
                  <td className="table-cell font-semibold whitespace-nowrap">
                    {formatMoney(order.total_amount)} {t('common.mmk')}
                  </td>
                  <td className="table-cell text-neutral-500 whitespace-nowrap">{formatTime(order.created_at)}</td>
                  <td className="table-cell text-right">
                    <span className="text-xs text-neutral-400 whitespace-nowrap">
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
    PENDING: { color: 'text-orange-700 bg-orange-50', dot: 'bg-orange-500', icon: Clock },
    CONFIRMED: { color: 'text-yellow-700 bg-yellow-50', dot: 'bg-yellow-500', icon: Clock },
    ASSIGNED: { color: 'text-blue-700 bg-blue-50', dot: 'bg-blue-500', icon: Truck },
    IN_TRANSIT: { color: 'text-primary-700 bg-primary-100', dot: 'bg-primary-500', icon: Truck },
    DELIVERED: { color: 'text-green-700 bg-green-50', dot: 'bg-green-500', icon: CheckCircle2 },
    CANCELLED: { color: 'text-red-700 bg-red-50', dot: 'bg-red-500', icon: XCircle },
  };
  const config = configs[status] ?? { color: 'text-neutral-700 bg-neutral-90', dot: 'bg-neutral-400', icon: Clock };
  const Icon = config.icon;

  return (
    <span className={`badge ${config.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {status}
    </span>
  );
}
