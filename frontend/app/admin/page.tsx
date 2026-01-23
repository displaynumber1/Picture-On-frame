'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseService } from '../../services/supabaseService';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type AdminUser = {
  id: string;
  email: string;
  trial_upload_remaining: number;
  subscribed: boolean;
  subscription_expires_at?: string | null;
  is_admin: boolean;
};

type ConfirmState = {
  message: string;
  onConfirm: () => void;
} | null;

export default function AdminPanelPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [total, setTotal] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [subscribedFilter, setSubscribedFilter] = useState('ALL');
  const [adminFilter, setAdminFilter] = useState('ALL');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDays, setBulkDays] = useState(30);
  const [confirmState, setConfirmState] = useState<ConfirmState>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      const profile = await supabaseService.getProfile();
      setIsAdmin(Boolean(profile?.is_admin));
      setAuthChecked(true);
    };
    init();
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const buildFilters = useCallback(() => {
    const params = new URLSearchParams();
    if (statusFilter !== 'ALL') params.set('status', statusFilter);
    if (subscribedFilter !== 'ALL') params.set('subscribed', subscribedFilter === 'true' ? 'true' : 'false');
    if (adminFilter !== 'ALL') params.set('is_admin', adminFilter === 'true' ? 'true' : 'false');
    return params;
  }, [statusFilter, subscribedFilter, adminFilter]);

  const fetchUsers = useCallback(async (nextPage: number) => {
    try {
      setLoading(true);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setToast('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const params = buildFilters();
      params.set('page', String(nextPage));
      params.set('per_page', String(perPage));
      const response = await fetch(`${API_URL}/api/admin/users?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Gagal memuat users.');
      }
      const data = await response.json();
      setUsers(Array.isArray(data?.items) ? data.items : []);
      setTotal(typeof data?.total === 'number' ? data.total : null);
      setPage(nextPage);
      setIsSearching(false);
      setSelectedIds(new Set());
    } catch {
      setToast('Gagal memuat users.');
    } finally {
      setLoading(false);
    }
  }, [perPage, buildFilters]);

  const fetchSearchPage = useCallback(async (nextPage: number) => {
    if (!searchQuery.trim()) {
      return { items: [], total: 0 };
    }
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setToast('Sesi kamu telah berakhir. Silakan login ulang.');
        return { items: [], total: 0 };
      }
      const params = buildFilters();
      params.set('q', searchQuery.trim());
      params.set('page', String(nextPage));
      params.set('per_page', String(perPage));
      const response = await fetch(`${API_URL}/api/admin/users/search?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Gagal mencari users.');
      }
      const data = await response.json();
      return {
        items: Array.isArray(data?.items) ? data.items : [],
        total: typeof data?.total === 'number' ? data.total : null
      };
    } catch {
      setToast('Gagal mencari users.');
      return { items: [], total: 0 };
    }
  }, [searchQuery, perPage, buildFilters]);

  const searchUsers = useCallback(async (nextPage?: number) => {
    if (!searchQuery.trim()) {
      fetchUsers(1);
      return;
    }
    try {
      setLoading(true);
      const targetPage = nextPage ?? page;
      const data = await fetchSearchPage(targetPage);
      setUsers(data.items);
      setTotal(typeof data.total === 'number' ? data.total : null);
      setIsSearching(true);
      setPage(targetPage);
      setSelectedIds(new Set());
    } finally {
      setLoading(false);
    }
  }, [fetchUsers, fetchSearchPage, page, searchQuery]);

  useEffect(() => {
    if (!authChecked || !isAdmin) return;
    fetchUsers(1);
  }, [authChecked, isAdmin, fetchUsers]);

  const confirm = (message: string, onConfirm: () => void) => {
    setConfirmState({ message, onConfirm });
  };

  const handleAction = async (path: string, payload?: Record<string, any>) => {
    try {
      setLoading(true);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setToast('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: payload ? JSON.stringify(payload) : undefined
      });
      if (!response.ok) {
        throw new Error('Update gagal.');
      }
      setToast('User updated successfully');
      if (isSearching) {
        await searchUsers();
      } else {
        await fetchUsers(page);
      }
    } catch {
      setToast('Gagal update user.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectAll = (checked: boolean) => {
    if (!checked) {
      setSelectedIds(new Set());
      return;
    }
    const next = new Set<string>();
    users.forEach((user) => next.add(user.id));
    setSelectedIds(next);
  };

  const toggleSelectUser = (userId: string) => {
    const next = new Set(selectedIds);
    if (next.has(userId)) {
      next.delete(userId);
    } else {
      next.add(userId);
    }
    setSelectedIds(next);
  };

  const handleBulkPro = () => {
    if (selectedIds.size === 0) {
      setToast('Pilih user terlebih dulu.');
      return;
    }
    confirm(`Give ${bulkDays} days Pro for ${selectedIds.size} user?`, () =>
      handleAction('/api/admin/users/bulk-set-subscription', {
        user_ids: Array.from(selectedIds),
        active: true,
        days: bulkDays
      })
    );
  };

  const handleBulkResetTrial = () => {
    if (selectedIds.size === 0) {
      setToast('Pilih user terlebih dulu.');
      return;
    }
    confirm(`Reset trial untuk ${selectedIds.size} user?`, () =>
      handleAction('/api/admin/users/bulk-reset-trial', {
        user_ids: Array.from(selectedIds)
      })
    );
  };

  const exportCsv = () => {
    const rows = [
      ['email', 'trial_remaining', 'subscribed', 'expires_at', 'is_admin'].join(','),
      ...users.map((user) => [
        user.email || '',
        user.trial_upload_remaining,
        user.subscribed,
        user.subscription_expires_at || '',
        user.is_admin
      ].map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ];
    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `admin-users-${isSearching ? 'search' : 'page'}-${page}.csv`;
    link.click();
  };

  const exportAllSearchCsv = async () => {
    if (!searchQuery.trim()) {
      setToast('Gunakan pencarian dulu.');
      return;
    }
    try {
      setLoading(true);
      const all: AdminUser[] = [];
      let currentPage = 1;
      while (true) {
        const data = await fetchSearchPage(currentPage);
        if (!data.items.length) break;
        all.push(...data.items);
        if (data.items.length < perPage) break;
        currentPage += 1;
        if (currentPage > 50) break;
      }
      if (all.length === 0) {
        setToast('Tidak ada data untuk diexport.');
        return;
      }
      const rows = [
        ['email', 'trial_remaining', 'subscribed', 'expires_at', 'is_admin'].join(','),
        ...all.map((user) => [
          user.email || '',
          user.trial_upload_remaining,
          user.subscribed,
          user.subscription_expires_at || '',
          user.is_admin
        ].map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      ];
      const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `admin-users-search-all.csv`;
      link.click();
    } finally {
      setLoading(false);
    }
  };

  const totalPages = useMemo(() => {
    if (!total) return null;
    return Math.max(1, Math.ceil(total / perPage));
  }, [perPage, total]);

  if (!authChecked) {
    return <div className="p-6 text-sm text-gray-500">Memeriksa akses...</div>;
  }

  if (!isAdmin) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 space-y-3">
          <h1 className="text-xl font-semibold text-gray-900">Admin Panel</h1>
          <p className="text-sm text-gray-500">Akses ditolak. Akun kamu bukan admin.</p>
          <button
            onClick={() => router.push('/app')}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Kembali ke Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-semibold text-gray-900">Admin Panel</h1>
          <p className="text-sm text-gray-500">Manage users, trials, and subscriptions</p>
        </div>
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <h2 className="text-lg font-semibold text-gray-900">User Management</h2>
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by email"
              className="border border-gray-200 rounded-xl px-4 py-2 text-sm text-gray-700 focus:outline-none"
            />
            <button
              onClick={() => searchUsers()}
              className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm"
            >
              Search
            </button>
            <button
              onClick={() => fetchUsers(1)}
              className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
            >
              Reset
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700"
          >
            <option value="ALL">All status</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="inactive">Inactive</option>
          </select>
          <select
            value={subscribedFilter}
            onChange={(event) => setSubscribedFilter(event.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700"
          >
            <option value="ALL">All subscribed</option>
            <option value="true">Subscribed</option>
            <option value="false">Not subscribed</option>
          </select>
          <select
            value={adminFilter}
            onChange={(event) => setAdminFilter(event.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700"
          >
            <option value="ALL">All admin</option>
            <option value="true">Admin</option>
            <option value="false">Non admin</option>
          </select>
          <button
            onClick={() => (isSearching ? searchUsers(1) : fetchUsers(1))}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Apply Filter
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              value={bulkDays}
              onChange={(event) => setBulkDays(Number(event.target.value || 0))}
              className="border border-gray-200 rounded-xl px-3 py-2 w-24 text-sm text-gray-700"
            />
            <span>days</span>
          </div>
          <button
            onClick={handleBulkPro}
            className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm"
          >
            Give Pro (Bulk)
          </button>
          <button
            onClick={handleBulkResetTrial}
            className="border border-red-200 text-red-600 hover:bg-red-50 rounded-xl px-4 py-2 text-sm"
          >
            Reset Trial (Bulk)
          </button>
          <button
            onClick={exportCsv}
            className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
          >
            Export CSV
          </button>
          {isSearching && (
            <button
              onClick={exportAllSearchCsv}
              className="border border-indigo-200 text-indigo-600 hover:bg-indigo-50 rounded-xl px-4 py-2 text-sm"
            >
              Export Search (All)
            </button>
          )}
          <span className="text-xs text-gray-500">Selected: {selectedIds.size}</span>
        </div>

        {toast && (
          <div className="text-sm text-emerald-600">{toast}</div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-400 uppercase tracking-wide">
              <tr className="text-left">
                <th className="py-3">
                  <input
                    type="checkbox"
                    checked={users.length > 0 && selectedIds.size === users.length}
                    onChange={(event) => toggleSelectAll(event.target.checked)}
                  />
                </th>
                <th className="py-3">Email</th>
                <th className="py-3">Trial remaining</th>
                <th className="py-3">Subscribed</th>
                <th className="py-3">Expires at</th>
                <th className="py-3">Admin</th>
                <th className="py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7} className="py-6 text-gray-500">Memuat data...</td>
                </tr>
              )}
              {!loading && users.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-6 text-gray-500">Belum ada user.</td>
                </tr>
              )}
              {!loading && users.map((user) => (
                <tr key={user.id} className="border-t border-gray-100">
                  <td className="py-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(user.id)}
                      onChange={() => toggleSelectUser(user.id)}
                    />
                  </td>
                  <td className="py-4 text-gray-900">{user.email || '—'}</td>
                  <td className="py-4 text-gray-700">{user.trial_upload_remaining}</td>
                  <td className="py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.subscribed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {user.subscribed ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="py-4 text-gray-600">
                    {user.subscription_expires_at ? new Date(user.subscription_expires_at).toLocaleDateString('id-ID') : '—'}
                  </td>
                  <td className="py-4 text-gray-700">{user.is_admin ? 'Yes' : 'No'}</td>
                  <td className="py-4">
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => confirm('Are you sure reset trial for this user?', () => handleAction(`/api/admin/users/${user.id}/reset-trial`))}
                        className="border border-red-200 text-red-600 hover:bg-red-50 rounded-xl px-4 py-2 text-xs"
                      >
                        Reset Trial
                      </button>
                      <button
                        onClick={() => confirm('Give 30 days Pro for this user?', () => handleAction(`/api/admin/users/${user.id}/set-subscription`, { active: true, days: 30 }))}
                        className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-xs"
                      >
                        Give 30 Days Pro
                      </button>
                      <button
                        onClick={() => confirm('Toggle admin for this user?', () => handleAction(`/api/admin/users/${user.id}/set-admin`, { is_admin: !user.is_admin }))}
                        className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-xs text-gray-700"
                      >
                        Toggle Admin
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages && !isSearching && (
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>Page {page} of {totalPages}</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchUsers(Math.max(1, page - 1))}
                className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2"
                disabled={page <= 1}
              >
                Prev
              </button>
              <button
                onClick={() => fetchUsers(Math.min(totalPages, page + 1))}
                className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2"
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          </div>
        )}
        {isSearching && (
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Page {page}
              {typeof total === 'number' ? ` · Total ${total}` : ''}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => searchUsers(Math.max(1, page - 1))}
                className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2"
                disabled={page <= 1}
              >
                Prev
              </button>
              <button
                onClick={() => searchUsers(page + 1)}
                className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {confirmState && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/40">
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 max-w-sm w-full space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Confirm</h3>
            <p className="text-sm text-gray-600">{confirmState.message}</p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  confirmState.onConfirm();
                  setConfirmState(null);
                }}
                className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm"
              >
                Yes, Continue
              </button>
              <button
                onClick={() => setConfirmState(null)}
                className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
