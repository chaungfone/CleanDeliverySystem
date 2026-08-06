import { useState, type FormEvent } from 'react';
import { Package, RefreshCw, Layers, Droplets, SlidersHorizontal } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { BranchInventory, InventoryData, InventoryInput } from '../lib/types';
import { ErrorState, LoadingState, formatTime } from '../lib/ui';
import Modal from '../components/Modal';
import { useI18n } from '../i18n';

interface AdjustForm {
  full_bottles: string;
  empty_bottles: string;
  caps_count: string;
  labels_count: string;
  water_liters: string;
}

export default function InventoryManager() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [adjusting, setAdjusting] = useState<BranchInventory | null>(null);
  const [form, setForm] = useState<AdjustForm | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const inventoryQuery = useQuery({
    queryKey: ['admin', 'inventory'],
    queryFn: () => apiFetch<InventoryData>('/admin/inventory'),
  });

  const adjustMutation = useMutation({
    mutationFn: (input: InventoryInput) =>
      apiFetch<BranchInventory>(`/admin/inventory/${adjusting?.branch_id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'inventory'] });
      setAdjusting(null);
      setForm(null);
    },
  });

  function openAdjust(row: BranchInventory) {
    setAdjusting(row);
    setForm({
      full_bottles: String(row.full_bottles ?? 0),
      empty_bottles: String(row.empty_bottles ?? 0),
      caps_count: String(row.caps_count ?? 0),
      labels_count: String(row.labels_count ?? 0),
      water_liters: String(row.water_liters ?? 0),
    });
    setError('');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError('');
    const input: InventoryInput = {
      full_bottles: Math.max(0, Number(form.full_bottles || 0)),
      empty_bottles: Math.max(0, Number(form.empty_bottles || 0)),
      caps_count: Math.max(0, Number(form.caps_count || 0)),
      labels_count: Math.max(0, Number(form.labels_count || 0)),
      water_liters: Math.max(0, Number(form.water_liters || 0)),
    };
    setSubmitting(true);
    try {
      await adjustMutation.mutateAsync(input);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update inventory');
    } finally {
      setSubmitting(false);
    }
  }

  if (inventoryQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (inventoryQuery.isError) {
    return <ErrorState error={inventoryQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  const totals = inventoryQuery.data?.totals;
  const branches = inventoryQuery.data?.branches ?? [];
  const products = inventoryQuery.data?.products ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{t('inventory.title')}</h2>
        <p className="text-neutral-500 text-sm">{t('inventory.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <InventoryCard title={t('inventory.fullBottles')} count={(totals?.full_bottles ?? 0).toLocaleString()} icon={Package} color="text-blue-600" />
        <InventoryCard title={t('inventory.emptyBottles')} count={(totals?.empty_bottles ?? 0).toLocaleString()} icon={RefreshCw} color="text-orange-600" />
        <InventoryCard
          title={t('inventory.capsLabels')}
          count={((totals?.caps_count ?? 0) + (totals?.labels_count ?? 0)).toLocaleString()}
          icon={Layers}
          color="text-teal-600"
        />
        <InventoryCard
          title={t('inventory.purifiedWater')}
          count={`${(totals?.water_liters ?? 0).toLocaleString()} L`}
          icon={Droplets}
          color="text-cyan-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-neutral-90 shadow-sm p-6">
          <h3 className="font-bold mb-4">{t('inventory.stockByBranch')}</h3>
          {branches.length === 0 && (
            <p className="text-sm text-neutral-400 py-8 text-center">{t('inventory.noRecords')}</p>
          )}
          <div className="space-y-4">
            {branches.map((row) => (
              <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 p-3 border border-neutral-90 rounded-lg">
                <div>
                  <span className="font-medium">{row.branch_name}</span>
                  <p className="text-xs text-neutral-400">{formatTime(row.updated_at)}</p>
                </div>
                <div className="flex items-center gap-4 text-sm flex-wrap">
                  <span>
                    {t('inventory.fullColon')}: <b className="text-primary">{row.full_bottles.toLocaleString()}</b>
                  </span>
                  <span>
                    {t('inventory.emptyColon')}: <b>{row.empty_bottles.toLocaleString()}</b>
                  </span>
                  <span>
                    {t('inventory.waterColon')}: <b>{row.water_liters.toLocaleString()} L</b>
                  </span>
                  <button
                    onClick={() => openAdjust(row)}
                    className="p-2 border border-neutral-90 rounded-lg text-neutral-500 hover:bg-neutral-99"
                    title={t('inventory.adjustStock')}
                  >
                    <SlidersHorizontal className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-neutral-90 shadow-sm p-6">
          <h3 className="font-bold mb-4">{t('inventory.productStock')}</h3>
          {products.length === 0 && (
            <p className="text-sm text-neutral-400 py-8 text-center">{t('inventory.noProducts')}</p>
          )}
          <div className="space-y-2">
            {products.map((product) => (
              <div key={product.id} className="flex flex-wrap items-center justify-between gap-3 p-3 border border-neutral-90 rounded-lg">
                <span className="font-medium">{product.name}</span>
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-neutral-500">
                    {Number(product.price).toLocaleString()} {t('common.mmk')}
                  </span>
                  <span className={product.stock_quantity === 0 ? 'text-red-600 font-bold' : 'font-medium'}>
                    {product.stock_quantity.toLocaleString()} {t('inventory.inStock')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Modal
        open={adjusting !== null}
        title={`${t('inventory.adjustStock')} — ${adjusting?.branch_name ?? ''}`}
        onClose={() => {
          setAdjusting(null);
          setForm(null);
        }}
      >
        {form && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label={t('inventory.fullBottles')}>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.full_bottles}
                  onChange={(e) => setForm({ ...form, full_bottles: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label={t('inventory.emptyBottles')}>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.empty_bottles}
                  onChange={(e) => setForm({ ...form, empty_bottles: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label={t('inventory.capsCount')}>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.caps_count}
                  onChange={(e) => setForm({ ...form, caps_count: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label={t('inventory.labelsCount')}>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={form.labels_count}
                  onChange={(e) => setForm({ ...form, labels_count: e.target.value })}
                  className={inputClass}
                />
              </Field>
              <Field label={t('inventory.waterLiters')}>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={form.water_liters}
                  onChange={(e) => setForm({ ...form, water_liters: e.target.value })}
                  className={inputClass}
                />
              </Field>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setAdjusting(null);
                  setForm(null);
                }}
                className="px-4 py-2 border border-neutral-90 rounded-lg text-neutral-500 hover:bg-neutral-99"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-primary text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-60"
              >
                {submitting ? t('common.saving') : t('inventory.saveStock')}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}

function InventoryCard({ title, count, icon: Icon, color }: any) {
  return (
    <div className="bg-white p-4 rounded-xl border border-neutral-90 shadow-sm flex items-center gap-4">
      <div className={`p-3 bg-neutral-99 rounded-lg ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-neutral-500 text-xs font-medium uppercase">{title}</p>
        <h4 className="text-xl font-bold">{count}</h4>
      </div>
    </div>
  );
}

const inputClass =
  'w-full px-3 py-2 border border-neutral-90 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-neutral-600 mb-1">{label}</span>
      {children}
    </label>
  );
}
