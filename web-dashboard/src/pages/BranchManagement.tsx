import { useState, type FormEvent } from 'react';
import { MapPin, Plus, Pencil, Trash2 } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { Branch, BranchData, BranchInput } from '../lib/types';
import { ErrorState, LoadingState } from '../lib/ui';
import Modal from '../components/Modal';
import { useI18n } from '../i18n';

interface BranchFormState {
  id: string | null;
  name: string;
  address: string;
  latitude: string;
  longitude: string;
  is_active: boolean;
}

const EMPTY_FORM: BranchFormState = {
  id: null,
  name: '',
  address: '',
  latitude: '',
  longitude: '',
  is_active: true,
};

export default function BranchManagement() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<BranchFormState>(EMPTY_FORM);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const branchesQuery = useQuery({
    queryKey: ['admin', 'branches'],
    queryFn: () => apiFetch<BranchData>('/admin/branches'),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'branches'] });
    queryClient.invalidateQueries({ queryKey: ['admin', 'inventory'] });
  };

  const saveMutation = useMutation({
    mutationFn: (input: BranchInput) => {
      if (form.id) {
        return apiFetch<Branch>(`/admin/branches/${form.id}`, {
          method: 'PATCH',
          body: JSON.stringify(input),
        });
      }
      return apiFetch<Branch>('/admin/branches', {
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
    mutationFn: (branchId: string) =>
      apiFetch<void>(`/admin/branches/${branchId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  function openCreate() {
    setForm(EMPTY_FORM);
    setError('');
    setModalOpen(true);
  }

  function openEdit(branch: Branch) {
    setForm({
      id: branch.id,
      name: branch.name,
      address: branch.address,
      latitude: '',
      longitude: '',
      is_active: branch.is_active,
    });
    setError('');
    setModalOpen(true);
  }

  function handleDelete(branch: Branch) {
    if (window.confirm(t('branches.deleteConfirm'))) {
      deleteMutation.mutate(branch.id);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!form.name.trim() || !form.address.trim()) {
      setError(t('branches.nameAddressRequired'));
      return;
    }
    const lat = form.latitude.trim();
    const lng = form.longitude.trim();
    if (!form.id && (lat === '' || lng === '')) {
      setError(t('branches.coordsRequired'));
      return;
    }
    if (lat !== '' || lng !== '') {
      const latNum = Number(lat);
      const lngNum = Number(lng);
      if (
        Number.isNaN(latNum) ||
        Number.isNaN(lngNum) ||
        latNum < -90 ||
        latNum > 90 ||
        lngNum < -180 ||
        lngNum > 180
      ) {
        setError(t('branches.invalidCoords'));
        return;
      }
    }

    const input: BranchInput = {
      name: form.name.trim(),
      address: form.address.trim(),
      latitude: Number(lat),
      longitude: Number(lng),
      is_active: form.is_active,
    };

    setSubmitting(true);
    try {
      await saveMutation.mutateAsync(input);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save branch');
    } finally {
      setSubmitting(false);
    }
  }

  if (branchesQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (branchesQuery.isError) {
    return <ErrorState error={branchesQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  const branches = branchesQuery.data?.branches ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">{t('branches.title')}</h2>
          <p className="text-neutral-500 text-sm">{t('branches.subtitle')}</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          {t('branches.addBranch')}
        </button>
      </div>

      <div className="bg-white p-6 rounded-xl border border-neutral-90 shadow-sm">
        <h3 className="font-bold flex items-center gap-2 mb-6">
          <MapPin className="w-5 h-5 text-primary" />
          {t('branches.branchesCount')} ({branches.length})
        </h3>
        {branches.length === 0 && (
          <p className="text-sm text-neutral-400 py-8 text-center">{t('branches.noBranches')}</p>
        )}
        <div className="space-y-4">
          {branches.map((branch) => (
            <div
              key={branch.id}
              className="flex flex-wrap items-center justify-between gap-3 p-4 bg-neutral-99 rounded-xl border border-neutral-90"
            >
              <div>
                <h4 className="font-bold">{branch.name}</h4>
                <p className="text-xs text-neutral-500">{branch.address}</p>
                <p className="text-xs text-neutral-400 mt-0.5">
                  {branch.staff.length} {t('branches.staffCount')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs font-bold px-2 py-1 rounded-md ${
                    branch.is_active ? 'text-green-700 bg-green-50' : 'text-neutral-700 bg-neutral-90'
                  }`}
                >
                  {branch.is_active ? t('common.active') : t('common.inactive')}
                </span>
                <button onClick={() => openEdit(branch)} className="p-2 hover:bg-neutral-90 rounded-lg" title={t('common.edit')}>
                  <Pencil className="w-4 h-4 text-neutral-500" />
                </button>
                <button onClick={() => handleDelete(branch)} className="p-2 hover:bg-red-50 rounded-lg" title={t('common.delete')}>
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Modal
        open={modalOpen}
        title={form.id ? t('branches.editTitle') : t('branches.addTitle')}
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label={`${t('branches.branchName')} *`}>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className={inputClass}
              placeholder="e.g. Yangon Main"
            />
          </Field>
          <Field label={`${t('branches.address')} *`}>
            <input
              type="text"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              required
              className={inputClass}
              placeholder="e.g. Downtown, Yangon"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label={t('branches.latitude')}>
              <input
                type="number"
                step="any"
                min="-90"
                max="90"
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                className={inputClass}
                placeholder={form.id ? t('branches.keepCurrent') : 'e.g. 16.8409'}
              />
            </Field>
            <Field label={t('branches.longitude')}>
              <input
                type="number"
                step="any"
                min="-180"
                max="180"
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                className={inputClass}
                placeholder={form.id ? t('branches.keepCurrent') : 'e.g. 96.1735'}
              />
            </Field>
          </div>
          {form.id && <p className="text-xs text-neutral-400">{t('branches.coordsHint')}</p>}
          <label className="flex items-center gap-2 text-sm font-medium text-neutral-600">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="w-4 h-4 accent-primary"
            />
            {t('branches.isActive')}
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 border border-neutral-90 rounded-lg text-neutral-500 hover:bg-neutral-99"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-primary text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-60"
            >
              {submitting ? t('common.saving') : form.id ? t('common.saveChanges') : t('branches.createBranch')}
            </button>
          </div>
        </form>
      </Modal>
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
