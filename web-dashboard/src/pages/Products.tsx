import { useState, type FormEvent } from 'react';
import { Package, Plus, Pencil, Trash2 } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { Product, ProductInput } from '../lib/types';
import { ErrorState, LoadingState, asArray, formatMoney } from '../lib/ui';
import Modal from '../components/Modal';
import { useI18n } from '../i18n';

interface FormState {
  id: string | null;
  name: string;
  description: string;
  price: string;
  deposit_fee: string;
  stock_quantity: string;
}

const EMPTY_FORM: FormState = {
  id: null,
  name: '',
  description: '',
  price: '',
  deposit_fee: '0',
  stock_quantity: '0',
};

export default function Products() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const productsQuery = useQuery({
    queryKey: ['admin', 'products'],
    queryFn: () => apiFetch<Product[]>('/admin/products'),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'products'] });
    queryClient.invalidateQueries({ queryKey: ['admin', 'inventory'] });
  };

  const saveMutation = useMutation({
    mutationFn: (input: ProductInput) => {
      if (form.id) {
        return apiFetch<Product>(`/admin/products/${form.id}`, {
          method: 'PATCH',
          body: JSON.stringify(input),
        });
      }
      return apiFetch<Product>('/admin/products', {
        method: 'POST',
        body: JSON.stringify(input),
      });
    },
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
      setForm(EMPTY_FORM);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (productId: string) =>
      apiFetch<void>(`/admin/products/${productId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  function openCreate() {
    setForm(EMPTY_FORM);
    setError('');
    setModalOpen(true);
  }

  function openEdit(product: Product) {
    setForm({
      id: product.id,
      name: product.name,
      description: product.description ?? '',
      price: String(product.price ?? ''),
      deposit_fee: String(product.deposit_fee ?? '0'),
      stock_quantity: String(product.stock_quantity ?? '0'),
    });
    setError('');
    setModalOpen(true);
  }

  function handleDelete(product: Product) {
    if (window.confirm(t('products.deleteConfirm'))) {
      deleteMutation.mutate(product.id);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!form.name.trim()) {
      setError(t('products.nameRequired'));
      return;
    }
    if (form.price === '' || Number(form.price) < 0) {
      setError(t('products.validPrice'));
      return;
    }
    setSubmitting(true);
    try {
      await saveMutation.mutateAsync({
        name: form.name.trim(),
        description: form.description.trim() || null,
        price: Number(form.price),
        deposit_fee: Number(form.deposit_fee || 0),
        stock_quantity: Number(form.stock_quantity || 0),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save product');
    } finally {
      setSubmitting(false);
    }
  }

  if (productsQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (productsQuery.isError) {
    return <ErrorState error={productsQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  const products = asArray<Product>(productsQuery.data);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('products.title')}</h2>
          <p className="text-neutral-500 text-sm mt-0.5">{t('products.subtitle')}</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <Plus className="w-4 h-4" />
          {t('products.addProduct')}
        </button>
      </div>

      <div className="table-card">
        <div className="table-wrap">
          <table className="w-full text-left min-w-[640px]">
            <thead className="table-head">
              <tr>
                <th>{t('common.name')}</th>
                <th>{t('products.price')}</th>
                <th>{t('products.deposit')}</th>
                <th>{t('products.stock')}</th>
                <th className="text-right">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {products.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-neutral-400">
                    {t('products.noProducts')}
                  </td>
                </tr>
              )}
              {products.map((product) => (
                <tr key={product.id} className="table-row">
                  <td className="table-cell">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-primary-100 shrink-0">
                        <Package className="w-4 h-4 text-primary-600" />
                      </div>
                      <div>
                        <div className="font-semibold text-neutral-900">{product.name}</div>
                        {product.description && (
                          <div className="text-xs text-neutral-400 line-clamp-1">{product.description}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="table-cell font-medium whitespace-nowrap">
                    {formatMoney(product.price)} {t('common.mmk')}
                  </td>
                  <td className="table-cell text-neutral-500 whitespace-nowrap">
                    {formatMoney(product.deposit_fee)} {t('common.mmk')}
                  </td>
                  <td className="table-cell">
                    <span
                      className={`badge ${
                        product.stock_quantity === 0
                          ? 'text-red-700 bg-red-50'
                          : 'text-green-700 bg-green-50'
                      }`}
                    >
                      {Number(product.stock_quantity ?? 0).toLocaleString()}
                    </span>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => openEdit(product)}
                        className="p-2 rounded-lg text-neutral-500 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                        title={t('common.edit')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(product)}
                        className="p-2 rounded-lg text-red-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                        title={t('common.delete')}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        open={modalOpen}
        title={form.id ? t('products.editTitle') : t('products.addTitle')}
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label={`${t('common.name')} *`}>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="input"
              placeholder={t('products.namePlaceholder')}
            />
          </Field>
          <Field label={t('products.description')}>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="textarea"
              rows={2}
              placeholder={t('products.descPlaceholder')}
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label={`${t('products.priceMmk')} *`}>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                required
                className="input"
                placeholder="0"
              />
            </Field>
            <Field label={t('products.depositFee')}>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.deposit_fee}
                onChange={(e) => setForm({ ...form, deposit_fee: e.target.value })}
                className="input"
                placeholder="0"
              />
            </Field>
          </div>
          <Field label={t('products.stockQuantity')}>
            <input
              type="number"
              min="0"
              step="1"
              value={form.stock_quantity}
              onChange={(e) => setForm({ ...form, stock_quantity: e.target.value })}
              className="input"
              placeholder="0"
            />
          </Field>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-xl px-3 py-2" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="btn-ghost">
              {t('common.cancel')}
            </button>
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? t('common.saving') : form.id ? t('products.saveChanges') : t('products.createProduct')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="field-label">{label}</span>
      {children}
    </label>
  );
}
