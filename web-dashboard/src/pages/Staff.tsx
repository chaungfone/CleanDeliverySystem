import { useState, type FormEvent } from 'react';
import { Plus, Pencil, Trash2, Phone, Shield, User } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { BranchData, StaffInput, StaffMember } from '../lib/types';
import { ErrorState, LoadingState, formatTime } from '../lib/ui';
import Modal from '../components/Modal';
import { useI18n } from '../i18n';

const ROLES = ['ADMIN', 'DRIVER', 'BRANCH_MANAGER'];

interface StaffFormState {
  id: string | null;
  full_name: string;
  phone_number: string;
  role: string;
  branch_id: string;
}

const EMPTY_FORM: StaffFormState = {
  id: null,
  full_name: '',
  phone_number: '',
  role: 'DRIVER',
  branch_id: '',
};

export default function Staff() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<StaffFormState>(EMPTY_FORM);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const staffQuery = useQuery({
    queryKey: ['admin', 'staff'],
    queryFn: () => apiFetch<StaffMember[]>('/admin/staff'),
  });
  const branchesQuery = useQuery({
    queryKey: ['admin', 'branches'],
    queryFn: () => apiFetch<BranchData>('/admin/branches'),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'staff'] });
    queryClient.invalidateQueries({ queryKey: ['admin', 'branches'] });
  };

  const saveMutation = useMutation({
    mutationFn: (input: StaffInput) => {
      if (form.id) {
        return apiFetch<StaffMember>(`/admin/staff/${form.id}`, {
          method: 'PATCH',
          body: JSON.stringify(input),
        });
      }
      return apiFetch<StaffMember>('/admin/staff', {
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
    mutationFn: (userId: string) => apiFetch<void>(`/admin/staff/${userId}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  function openCreate() {
    setForm(EMPTY_FORM);
    setError('');
    setModalOpen(true);
  }

  function openEdit(staff: StaffMember) {
    setForm({
      id: staff.id,
      full_name: staff.full_name,
      phone_number: staff.phone_number ?? '',
      role: staff.role,
      branch_id: staff.branch_id ?? '',
    });
    setError('');
    setModalOpen(true);
  }

  function handleDelete(staff: StaffMember) {
    if (window.confirm(t('staff.deleteConfirm'))) {
      deleteMutation.mutate(staff.id);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!form.full_name.trim()) {
      setError(t('staff.nameRequired'));
      return;
    }
    if (!form.id && !/^\+?[0-9]{9,15}$/.test(form.phone_number)) {
      setError(t('staff.phoneInvalid'));
      return;
    }

    const input: StaffInput = {
      full_name: form.full_name.trim(),
      role: form.role,
      branch_id: form.branch_id || null,
    };
    if (!form.id) {
      input.phone_number = form.phone_number.trim();
    }

    setSubmitting(true);
    try {
      await saveMutation.mutateAsync(input);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save staff account');
    } finally {
      setSubmitting(false);
    }
  }

  if (staffQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (staffQuery.isError) {
    return <ErrorState error={staffQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  const staff = staffQuery.data ?? [];
  const branches = branchesQuery.data?.branches ?? [];
  const branchName = (id: string | null) => branches.find((b) => b.id === id)?.name ?? t('common.unassigned');

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('staff.title')}</h2>
          <p className="text-neutral-500 text-sm mt-0.5">{t('staff.subtitle')}</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <Plus className="w-4 h-4" />
          {t('staff.addStaff')}
        </button>
      </div>

      <div className="table-card">
        <div className="table-wrap">
          <table className="w-full text-left min-w-[720px]">
            <thead className="table-head">
              <tr>
                <th>{t('common.name')}</th>
                <th>{t('common.phone')}</th>
                <th>{t('common.role')}</th>
                <th>{t('common.branch')}</th>
                <th>{t('common.created')}</th>
                <th className="text-right">{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {staff.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-neutral-400">
                    {t('staff.noStaff')}
                  </td>
                </tr>
              )}
              {staff.map((member) => (
                <tr key={member.id} className="table-row">
                  <td className="table-cell">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center text-white font-bold text-xs uppercase shrink-0">
                        {member.full_name.charAt(0)}
                      </div>
                      <span className="font-semibold text-neutral-900">{member.full_name}</span>
                    </div>
                  </td>
                  <td className="table-cell text-neutral-500 whitespace-nowrap">{member.phone_number ?? '—'}</td>
                  <td className="table-cell">
                    <RoleBadge role={member.role} />
                  </td>
                  <td className="table-cell text-neutral-500">{branchName(member.branch_id)}</td>
                  <td className="table-cell text-neutral-400 text-sm whitespace-nowrap">{formatTime(member.created_at)}</td>
                  <td className="table-cell">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => openEdit(member)}
                        className="p-2 rounded-lg text-neutral-500 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                        title={t('common.edit')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(member)}
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
        title={form.id ? t('staff.editTitle') : t('staff.addTitle')}
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label={`${t('staff.fullName')} *`}>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
              className="input"
              placeholder="e.g. Kyaw Kyaw"
            />
          </Field>
          {!form.id && (
            <Field label={`${t('staff.phoneNumber')} *`}>
              <div className="relative">
                <Phone className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
                <input
                  type="tel"
                  value={form.phone_number}
                  onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                  required
                  pattern="^\+?[0-9]{9,15}$"
                  className="input input-with-icon"
                  placeholder="09xxxxxxxxx"
                />
              </div>
            </Field>
          )}
          <div className="grid grid-cols-2 gap-4">
            <Field label={`${t('common.role')} *`}>
              <div className="relative">
                <Shield className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="select pl-9"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>
            </Field>
            <Field label={t('common.branch')}>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
                <select
                  value={form.branch_id}
                  onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                  className="select pl-9"
                >
                  <option value="">{t('common.unassigned')}</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
            </Field>
          </div>

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
              {submitting ? t('common.saving') : form.id ? t('common.saveChanges') : t('staff.createAccount')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function RoleBadge({ role }: { role: string }) {
  const configs: any = {
    ADMIN: 'text-red-700 bg-red-50',
    DRIVER: 'text-blue-700 bg-blue-50',
    BRANCH_MANAGER: 'text-teal-700 bg-teal-50',
  };
  return (
    <span className={`badge ${configs[role] ?? 'bg-neutral-90 text-neutral-700'}`}>
      {role.replace(/_/g, ' ')}
    </span>
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
