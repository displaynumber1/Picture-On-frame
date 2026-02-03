'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lightbulb, Upload } from 'lucide-react';
import { ROUTES } from '../../../lib/routes';
import type {
  AdminAuditLog,
  AdminAutopostLog,
  AdminMidtransStatus,
  AdminSubscriptionInfo,
  AutopostDashboardItem,
  AutopostFeedbackWeights,
  AutopostInsights,
  EngagementTemplates,
  MetricsUploadResult,
  TrendsPreview
} from './dashboardTypes';
const DashboardView: React.FC<{
  items: AutopostDashboardItem[];
  loading: boolean;
  error: string | null;
  displayName: string;
  avatarUrl: string | null;
  onBack: () => void;
  onLogout: () => void;
  onTopUp: () => void;
  dashboardErrorNeedsTopUp: boolean;
  onRetry: (id: number) => void;
  onRecheck: () => void;
  onRegenerate: (id: number) => void;
  regeneratingId: number | null;
  trialRemaining: number | null;
  isSubscribed: boolean;
  subscribedUntil: string | null;
  proStatus: 'active' | 'expired' | 'inactive' | 'pending';
  renewWindow: boolean;
  expiresInDays: number | null;
  onUploadClick: () => void;
  onUploadChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  uploadInputRef: React.RefObject<HTMLInputElement>;
  trendsPreview: TrendsPreview | null;
  trendsLoading: boolean;
  trendsMessage: string | null;
  onTrendsUploadClick: () => void;
  onTrendsUploadChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onTrendsRefresh: () => void;
  trendsUploadRef: React.RefObject<HTMLInputElement>;
  isAdmin: boolean;
  trendsSearch: string;
  onTrendsSearchChange: (value: string) => void;
  trendsPage: number;
  trendsPageSize: number;
  onTrendsPageChange: (page: number) => void;
  trendsCategory: string;
  onTrendsCategoryChange: (value: string) => void;
  importStatus: { status: string; processed: number; total: number; valid: number; invalid: number } | null;
  importErrors: string[];
  categoryOptions: Array<{ value: string; label: string }>;
  onDownloadTemplate: () => void;
  onDownloadAllTrends: () => void;
  autoRetryImport: boolean;
  onToggleAutoRetry: (value: boolean) => void;
  templates: EngagementTemplates | null;
  templatesLoading: boolean;
  templatesError: string | null;
  onCopyTemplate: (text: string) => void;
  hashtagRegex: string;
  importErrorRef: React.RefObject<HTMLDivElement>;
  errorRowSet: Set<number>;
  errorPages: number[];
  onCopyErrors: () => void;
  onExportErrorsCsv: () => void;
  insights: AutopostInsights | null;
  insightsLoading: boolean;
  insightsError: string | null;
  onAddCompetitor: () => void;
  competitors: Array<{ id: number; title: string; url?: string; notes?: string }>;
  showOnlyErrors: boolean;
  onToggleShowOnlyErrors: (value: boolean) => void;
  hideErrorHighlight: boolean;
  onToggleHideErrorHighlight: (value: boolean) => void;
  errorRowsInPage: number[];
  adminLogs: AdminAutopostLog[];
  adminLogsLoading: boolean;
  adminLogsError: string | null;
  onAdminLogsRefresh: () => void;
  adminLogsStatus: string;
  onAdminLogsStatusChange: (value: string) => void;
  adminLogsUserQuery: string;
  onAdminLogsUserQueryChange: (value: string) => void;
  adminLogsDateFrom: string;
  onAdminLogsDateFromChange: (value: string) => void;
  adminLogsDateTo: string;
  onAdminLogsDateToChange: (value: string) => void;
  adminLogsLimit: number;
  onAdminLogsLimitChange: (value: number) => void;
  filteredAdminLogs: AdminAutopostLog[];
  midtransStatus: AdminMidtransStatus | null;
  midtransStatusLoading: boolean;
  midtransStatusError: string | null;
  onMidtransStatusRefresh: () => void;
  metricsVideoId: string;
  onMetricsVideoIdChange: (value: string) => void;
  metricsUploadResult: MetricsUploadResult;
  metricsUploading: boolean;
  metricsUploadRef: React.RefObject<HTMLInputElement>;
  onMetricsUploadClick: () => void;
  onMetricsUploadChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  feedbackWeights: AutopostFeedbackWeights | null;
  feedbackWeightsLoading: boolean;
  feedbackWeightsError: string | null;
  feedbackWeightsQuery: string;
  onFeedbackWeightsQueryChange: (value: string) => void;
  onFeedbackWeightsRefresh: () => void;
  subscriptionQuery: string;
  subscriptionInfo: AdminSubscriptionInfo | null;
  subscriptionLoading: boolean;
  subscriptionError: string | null;
  subscriptionStatus: string | null;
  onSubscriptionQueryChange: (value: string) => void;
  onSubscriptionLookup: () => void;
  onSubscriptionUpdate: (payload: Record<string, any>) => void;
  adminAuditLogs: AdminAuditLog[];
  adminAuditLoading: boolean;
  adminAuditError: string | null;
  onAdminAuditRefresh: () => void;
}> = ({
  items,
  loading,
  error,
  displayName,
  avatarUrl,
  onBack,
  onLogout,
  onTopUp,
  dashboardErrorNeedsTopUp,
  onRetry,
  onRecheck,
  onRegenerate,
  regeneratingId,
  trialRemaining,
  isSubscribed,
  subscribedUntil,
  proStatus,
  renewWindow,
  expiresInDays,
  onUploadClick,
  onUploadChange,
  uploadInputRef,
  trendsPreview,
  trendsLoading,
  trendsMessage,
  onTrendsUploadClick,
  onTrendsUploadChange,
  onTrendsRefresh,
  trendsUploadRef,
  isAdmin,
  trendsSearch,
  onTrendsSearchChange,
  trendsPage,
  trendsPageSize,
  onTrendsPageChange,
  trendsCategory,
  onTrendsCategoryChange,
  importStatus,
  importErrors,
  categoryOptions,
  onDownloadTemplate,
  onDownloadAllTrends,
  autoRetryImport,
  onToggleAutoRetry,
  templates,
  templatesLoading,
  templatesError,
  onCopyTemplate,
  hashtagRegex,
  importErrorRef,
  errorRowSet,
  errorPages,
  onCopyErrors,
  onExportErrorsCsv,
  insights,
  insightsLoading,
  insightsError,
  onAddCompetitor,
  competitors,
  showOnlyErrors,
  onToggleShowOnlyErrors,
  hideErrorHighlight,
  onToggleHideErrorHighlight,
  errorRowsInPage,
  adminLogs,
  adminLogsLoading,
  adminLogsError,
  onAdminLogsRefresh,
  adminLogsStatus,
  onAdminLogsStatusChange,
  adminLogsUserQuery,
  onAdminLogsUserQueryChange,
  adminLogsDateFrom,
  onAdminLogsDateFromChange,
  adminLogsDateTo,
  onAdminLogsDateToChange,
  adminLogsLimit,
  onAdminLogsLimitChange,
  filteredAdminLogs,
  midtransStatus,
  midtransStatusLoading,
  midtransStatusError,
  onMidtransStatusRefresh,
  metricsVideoId,
  onMetricsVideoIdChange,
  metricsUploadResult,
  metricsUploading,
  metricsUploadRef,
  onMetricsUploadClick,
  onMetricsUploadChange,
  feedbackWeights,
  feedbackWeightsLoading,
  feedbackWeightsError,
  feedbackWeightsQuery,
  onFeedbackWeightsQueryChange,
  onFeedbackWeightsRefresh,
  subscriptionQuery,
  subscriptionInfo,
  subscriptionLoading,
  subscriptionError,
  subscriptionStatus,
  onSubscriptionQueryChange,
  onSubscriptionLookup,
  onSubscriptionUpdate,
  adminAuditLogs,
  adminAuditLoading,
  adminAuditError,
  onAdminAuditRefresh
}) => {
  const router = useRouter();
  const [showMetricsInfo, setShowMetricsInfo] = useState(false);
  const [showUploadInfo, setShowUploadInfo] = useState(false);
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [adminAuditActor, setAdminAuditActor] = useState('');
  const [adminAuditTarget, setAdminAuditTarget] = useState('');
  const [adminAuditAction, setAdminAuditAction] = useState('ALL');
  const isTrialExpired = !isSubscribed && typeof trialRemaining === 'number' && trialRemaining <= 0;
  const handleBillingNavigate = () => {
    router.replace(ROUTES.billing);
  };
  const formatCountdown = (nextCheckAt?: string | null) => {
    if (!nextCheckAt) return '';
    const diff = new Date(nextCheckAt).getTime() - Date.now();
    if (Number.isNaN(diff)) return '';
    if (diff <= 0) return 'now';
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
    return `${minutes}m ${seconds}s`;
  };
  const formatSchedule = (scheduledAt?: string | null, nextCheckAt?: string | null) => {
    if (scheduledAt) {
      const dt = new Date(scheduledAt);
      if (!Number.isNaN(dt.getTime())) {
        return dt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
      }
    }
    return formatCountdown(nextCheckAt);
  };
  const getHashtagList = (hashtags?: string | null) =>
    (hashtags || '')
      .split(/\s+/)
      .map((tag) => tag.trim())
      .filter(Boolean);
  const renderSourceBadge = (source?: string | null) => {
    if (!source) return null;
    const isAi = source === 'ai_generated';
    return (
      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${isAi ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
        {isAi ? 'AI' : 'User'}
      </span>
    );
  };
  const statusLabel = (status: string) => {
    if (status === 'WAITING_RECHECK') return 'WAITING';
    return status;
  };
  const statusClasses = (status: string) => {
    switch (status) {
      case 'POSTED':
        return 'bg-green-100 text-green-700';
      case 'FAILED':
        return 'bg-red-100 text-red-700';
      case 'WAITING_RECHECK':
        return 'bg-yellow-100 text-yellow-700';
      case 'QUEUED':
        return 'bg-blue-100 text-blue-700';
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };
  return (
    <div className="min-h-screen bg-slate-100">
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-black text-[10px] tracking-wider">
              PRO
            </div>
            <span className="text-lg font-bold text-slate-800">AI Auto-Posting</span>
          </div>
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <div className="flex flex-wrap items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-200 overflow-hidden flex items-center justify-center text-[10px] font-bold text-slate-600">
                {avatarUrl ? (
                  <img src={avatarUrl} alt={displayName} className="w-full h-full object-cover" />
                ) : (
                  <span>{displayName?.trim()?.[0]?.toUpperCase() || 'U'}</span>
                )}
              </div>
              <span className="text-sm text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
                Hi, {displayName}
              </span>
              {isAdmin && (
                <span className="text-[10px] font-semibold uppercase tracking-widest bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full">
                  Admin
                </span>
              )}
              {proStatus === 'pending' ? (
                <span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-1 rounded-full bg-yellow-100 text-yellow-700">
                  Pro Pending
                </span>
              ) : proStatus === 'expired' ? (
                <span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-1 rounded-full bg-red-100 text-red-700">
                  Pro Expired
                </span>
              ) : (
                <span className={`text-[10px] font-semibold uppercase tracking-widest px-2 py-1 rounded-full ${isSubscribed ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'}`}>
                  {isSubscribed ? 'Pro Active' : 'Free'}
                </span>
              )}
              {isSubscribed && subscribedUntil && (
                <span className="text-[10px] font-semibold px-2 py-1 rounded-full bg-gray-50 text-gray-500">
                  Aktif sampai {new Date(subscribedUntil).toLocaleDateString('id-ID')}
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={onBack}
                className="px-4 py-2 rounded-full bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition"
              >
                Back to Studio
              </button>
              <button
                onClick={handleBillingNavigate}
                className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition"
              >
                Billing
              </button>
              <button
                onClick={onLogout}
                className="px-4 py-2 rounded-full bg-slate-200 text-slate-700 text-sm font-semibold hover:bg-slate-300 transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {proStatus === 'active' && renewWindow && (
          <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-amber-700">Masa Pro hampir habis</div>
              <div className="text-xs text-amber-700/80">
                {typeof expiresInDays === 'number'
                  ? `Sisa ${expiresInDays} hari. Perpanjang sekarang agar layanan tidak terputus.`
                  : 'Perpanjang sekarang agar layanan tidak terputus.'}
              </div>
            </div>
            <button
              onClick={handleBillingNavigate}
              className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm"
            >
              Perpanjang Sekarang
            </button>
          </div>
        )}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl p-6 text-white flex flex-col gap-4 md:flex-row md:items-center md:justify-between shadow-lg">
          <div>
            <h2 className="text-xl font-bold">Upload Video</h2>
            <p className="text-sm text-white/80">Boost video kamu biar engagement postingan makin naik </p>
            <span className="inline-flex mt-2 px-3 py-1 rounded-full bg-white/15 text-[10px] font-semibold tracking-wide">
              Biaya upload: 90 coins
            </span>
          </div>
          <div className="relative flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowUploadInfo((prev) => !prev)}
              className="flex items-center gap-1 px-3 py-2 bg-white/20 hover:bg-white/30 rounded-xl text-xs font-semibold"
            >
              <Lightbulb size={14} />
              Info Penting
            </button>
            <button
              onClick={onUploadClick}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-xl text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isTrialExpired}
            >
              <Upload size={16} />
              Upload Video
            </button>
            {showUploadInfo && (
              <div className="absolute left-0 top-full mt-2 w-72 rounded-lg border border-white/20 bg-white p-3 text-[11px] text-slate-700 shadow-lg">
                <div className="font-semibold text-slate-800 mb-2">Info Penting</div>
                <ul className="list-disc pl-4 space-y-1">
                  <li>Upload video minimal HD 720p (recommended 1080p atau di atasnya).</li>
                  <li>Video sudah ada Sound/Lagu (Minimal ada Voice Over agar hasil maksimal).</li>
                  <li>1 akun TikTok 1 niche (wajib).</li>
                </ul>
              </div>
            )}
          </div>
          <input
            ref={uploadInputRef}
            type="file"
            accept="video/*"
            className="hidden"
            onChange={onUploadChange}
          />
        </div>
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">Panduan Fitur Auto-Posting</h3>
            <a
              href={ROUTES.helpAutopost}
              className="text-xs text-indigo-600 hover:text-indigo-700"
            >
              Lihat panduan lengkap disini 
            </a>
          </div>
          <div className="text-xs text-slate-600 space-y-1">
            <div>Fitur Auto-Posting adalah automasi browser untuk posting secara otomatis (tanpa simpan password) untuk meningkatkan engagement.</div>
            <div>AI kami akan melakukan: upload  analyze  queue  auto post  cleanup untuk mendapatkan engagement tinggi dari video yang di posting.</div>
            <div>Wajib login TikTok di browser dan jangan logout selama AI kami bekerja.</div>
            <div>Keamanan: Kami tidak akses DM, saldo, atau data sensitif lainnya dari akun kamu.</div>
          </div>
        </div>
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-700">Trend CSV</h3>
              <p className="text-xs text-slate-500">
                Dataset hashtag tren untuk RAG (preview + admin upload).
                <span
                  className="ml-2 inline-flex items-center justify-center w-4 h-4 text-[10px] rounded-full bg-slate-100 text-slate-500 cursor-default"
                  title={`Regex: ${hashtagRegex || '-'} | Whitelist: ${categoryOptions.map(c => c.value).join(', ')}`}
                >
                  i
                </span>
              </p>
              <div className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg p-3">
                <div>Saat mengunduh data tiktok, user hanya perlu mencentang:</div>
                <div> Postingan</div>
                <div> TikTok Shop</div>
                <div>(Opsional: Komentar, Suka & Favorit)</div>
                <div className="mt-1">Kami tidak memerlukan DM, Dompet, atau data sensitif lainnya.</div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={onDownloadTemplate}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Download Template
              </button>
              <button
                onClick={onDownloadAllTrends}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Download Semua Data
              </button>
              <button
                onClick={onTrendsRefresh}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Refresh
              </button>
              <button
                onClick={onTrendsUploadClick}
                disabled={!isAdmin}
                className="px-3 py-1.5 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Upload CSV
              </button>
            </div>
          </div>
          <input
            ref={trendsUploadRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={onTrendsUploadChange}
          />
          {trendsLoading && <div className="text-xs text-slate-500">Memuat...</div>}
          {trendsMessage && <div className="text-xs text-slate-500">{trendsMessage}</div>}
          {!trendsLoading && trendsPreview && (
            <div className="text-xs text-slate-500 mb-3">
              Total rows: {trendsPreview.total}
            </div>
          )}
          <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-2">
            <input
              value={trendsSearch}
              onChange={(e) => onTrendsSearchChange(e.target.value)}
              placeholder="Cari hashtag / kategori..."
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200"
            />
            <select
              value={trendsCategory}
              onChange={(e) => onTrendsCategoryChange(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200"
            >
              <option value="">Semua kategori</option>
              {categoryOptions.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
            <input
              id="auto-retry-import"
              type="checkbox"
              checked={autoRetryImport}
              onChange={(e) => onToggleAutoRetry(e.target.checked)}
            />
            <label htmlFor="auto-retry-import">Auto-retry import setelah upload</label>
          </div>
          <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
            <input
              id="show-only-errors"
              type="checkbox"
              checked={showOnlyErrors}
              onChange={(e) => onToggleShowOnlyErrors(e.target.checked)}
            />
            <label htmlFor="show-only-errors">Show only error rows</label>
            {errorRowsInPage.length > 0 && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px]">
                {errorRowsInPage.length} errors on page
              </span>
            )}
          </div>
          <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
            <input
              id="hide-error-highlight"
              type="checkbox"
              checked={hideErrorHighlight}
              onChange={(e) => onToggleHideErrorHighlight(e.target.checked)}
            />
            <label htmlFor="hide-error-highlight">Hide error highlight</label>
          </div>
          {importStatus && (
            <div className="mb-3 text-xs text-slate-500">
              Import status: {importStatus.status} ({importStatus.processed}/{importStatus.total})  valid {importStatus.valid}  invalid {importStatus.invalid}
            </div>
          )}
          {importStatus && importStatus.total > 0 && (
            <div className="mb-3 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all"
                style={{
                  width: `${Math.min(100, Math.round((importStatus.processed / importStatus.total) * 100))}%`
                }}
              />
            </div>
          )}
          {importErrors.length > 0 && (
            <div
              ref={importErrorRef}
              className="mb-3 max-h-24 overflow-auto text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg p-2"
            >
              {importErrors.map((err, idx) => (
                <div key={`${err}-${idx}`}>{err}</div>
              ))}
            </div>
          )}
          {importErrors.length > 0 && (
            <div className="mb-3 flex items-center gap-2 text-xs">
              <button
                onClick={onCopyErrors}
                className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
              >
                Copy errors
              </button>
              <button
                onClick={onExportErrorsCsv}
                className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
              >
                Export errors CSV
              </button>
            </div>
          )}
          {!trendsLoading && trendsPreview && (
            <div className="max-h-48 overflow-auto border border-slate-100 rounded-lg">
              <div className="grid grid-cols-[120px_1fr_80px] gap-3 px-3 py-2 text-[10px] font-semibold uppercase text-slate-400 bg-slate-50">
                <span>Category</span>
                <span>Hashtag</span>
                <span>Weight</span>
              </div>
              {trendsPreview.rows.map((row, idx) => {
                const rowNumber = (trendsPage - 1) * trendsPageSize + idx + 1;
                const hasError = errorRowSet.has(rowNumber);
                if (showOnlyErrors && !hasError) {
                  return null;
                }
                return (
                  <div
                    key={`${row.hashtag}-${idx}`}
                    className={`grid grid-cols-[120px_1fr_80px] gap-3 px-3 py-2 text-xs border-t border-slate-100 ${hasError && !hideErrorHighlight ? 'bg-red-50' : ''}`}
                  >
                    <span className="text-slate-500">{row.category || '-'}</span>
                    <span className="text-slate-700">{row.hashtag || '-'}</span>
                    <span className="text-slate-500">{row.weight ?? '-'}</span>
                  </div>
                );
              })}
            </div>
          )}
          {importErrors.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span>
                Jump to page with error
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px]">
                  {importErrors.length} errors  {errorPages.length} pages
                </span>
              </span>
              {errorPages.map((page: number) => (
                <button
                  key={`page-${page}`}
                  onClick={() => onTrendsPageChange(page)}
                  className={`px-2 py-1 rounded border border-slate-200 hover:bg-slate-50 ${page === trendsPage ? 'bg-slate-100' : ''}`}
                >
                  {page}
                </button>
              ))}
              {errorPages.length > 0 && (
                <button
                  onClick={() => {
                    const currentIndex = errorPages.indexOf(trendsPage);
                    const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % errorPages.length : 0;
                    onTrendsPageChange(errorPages[nextIndex]);
                  }}
                  className="px-2 py-1 rounded border border-red-200 text-red-700 hover:bg-red-50"
                >
                  Next error page
                </button>
              )}
            </div>
          )}
          {!trendsLoading && trendsPreview && (
            <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
              <span>
                Page {trendsPage} of {Math.max(1, Math.ceil(trendsPreview.total / trendsPageSize))}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onTrendsPageChange(Math.max(1, trendsPage - 1))}
                  className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={trendsPage <= 1}
                >
                  Prev
                </button>
                <button
                  onClick={() => {
                    const totalPages = Math.max(1, Math.ceil(trendsPreview.total / trendsPageSize));
                    if (trendsPage < totalPages) {
                      onTrendsPageChange(trendsPage + 1);
                    }
                  }}
                  className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={trendsPage >= Math.max(1, Math.ceil(trendsPreview.total / trendsPageSize))}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-100 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="text-lg font-semibold text-gray-900"> AI Video Queue</span>
              <p className="text-sm text-gray-500 mt-1">
                AI sedang menganalisis dan mengoptimasi video kamu agar performanya maksimal.
              </p>
              {!isSubscribed && (
                <div className="mt-2">
                  {isTrialExpired ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-red-50 text-red-600">
                       Trial habis  Upgrade ke Pro
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-yellow-100 text-yellow-700">
                       Sisa trial: {trialRemaining ?? 0} dari 3 upload gratis
                    </span>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={onRecheck}
              className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
            >
              Recheck Now
            </button>
          </div>
          {loading && (
            <div className="px-6 py-6 space-y-3">
              <div className="text-sm text-gray-500"> AI sedang memproses video kamu...</div>
              {[...Array(3)].map((_, idx) => (
                <div key={`skeleton-${idx}`} className="grid grid-cols-1 md:grid-cols-[1fr_2fr_1fr_1fr_1fr_1.4fr] gap-3 items-center">
                  <div className="h-4 bg-gray-100 rounded animate-pulse" />
                  <div className="h-4 bg-gray-100 rounded animate-pulse" />
                  <div className="h-4 bg-gray-100 rounded animate-pulse w-20" />
                  <div className="h-4 bg-gray-100 rounded animate-pulse w-16" />
                  <div className="h-4 bg-gray-100 rounded animate-pulse w-24" />
                  <div className="h-8 bg-gray-100 rounded animate-pulse" />
                </div>
              ))}
            </div>
          )}
          {error && (
            <div className="px-6 py-6 text-sm text-red-600">
              {dashboardErrorNeedsTopUp ? (
                <span className="flex flex-wrap items-center gap-2">
                  <span>{error.replace('Top Up', '').trim()}</span>
                  <button
                    onClick={onTopUp}
                    className="text-indigo-600 hover:text-indigo-800 font-semibold underline"
                  >
                    Top Up
                  </button>
                </span>
              ) : (
                error
              )}
            </div>
          )}
          {!loading && !error && items.length === 0 && (
            <div className="px-6 py-6 text-sm text-gray-500">Belum ada video.</div>
          )}
          {!loading && !error && (
            <>
              <div className="hidden md:block">
                <div className="grid grid-cols-[1fr_2fr_1fr_1fr_1fr_1.4fr] gap-3 px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  <span>Video ID</span>
                  <span>Video</span>
                  <span>AI Status</span>
                  <span>FYP Score</span>
                  <span>Scheduled / Recheck</span>
                  <span>Action</span>
                </div>
                {items.map((row) => (
                  <div key={`desktop-${row.id}`} className="border-t border-gray-100">
                    <div className="grid grid-cols-[1fr_2fr_1fr_1fr_1fr_1.4fr] gap-3 px-6 py-4 text-sm items-center hover:bg-gray-50">
                      <span className="font-medium text-gray-600">#{row.id}</span>
                      <span className="font-medium text-gray-800 truncate">{row.video_name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full inline-flex items-center w-fit ${statusClasses(row.status)}`}>
                        {statusLabel(row.status)}
                      </span>
                      <span className="text-gray-700">{typeof row.score === 'number' ? row.score.toFixed(1) : ''}</span>
                      <span className="text-gray-500">{formatSchedule(row.scheduled_at, row.next_check_at)}</span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setExpandedRowId(expandedRowId === row.id ? null : row.id)}
                          className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
                        >
                          Lihat Detail
                        </button>
                        <button
                          onClick={() => onRegenerate(row.id)}
                          className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm disabled:opacity-60"
                          disabled={regeneratingId === row.id || isTrialExpired}
                        >
                           Regenerate AI
                        </button>
                      </div>
                    </div>
                    {expandedRowId === row.id && (
                      <div className="px-6 pb-5">
                        <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 text-xs text-gray-700 space-y-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold">Hook:</span>
                            <span>{row.hook_text || ''}</span>
                            {renderSourceBadge(row.hook_source)}
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold">CTA:</span>
                            <span>{row.cta_text || ''}</span>
                            {renderSourceBadge(row.cta_source)}
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold">Hashtags:</span>
                            {getHashtagList(row.hashtags).length > 0 ? (
                              getHashtagList(row.hashtags).map((tag) => (
                                <span key={tag} className="px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                                  {tag}
                                </span>
                              ))
                            ) : (
                              <span></span>
                            )}
                            {renderSourceBadge(row.hashtags_source)}
                          </div>
                          <div className="space-y-1">
                            <span className="font-semibold">Score reasons:</span>
                            <ul className="grid gap-1">
                              {(row.score_reasons || []).length > 0 ? (
                                row.score_reasons?.map((reason, idx) => (
                                  <li key={`reason-${row.id}-${idx}`} className="flex items-start gap-2">
                                    <span className="text-emerald-500"></span>
                                    <span>{reason.replace(/\(\s*<=\s*10\s*kata\s*\)/gi, '').trim()}</span>
                                  </li>
                                ))
                              ) : (
                                <li className="text-gray-500"></li>
                              )}
                            </ul>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-gray-500">
                            <span className="font-semibold text-gray-600">AI Confidence:</span>
                            <span>
                              {typeof row.score === 'number'
                                ? row.score >= 8
                                  ? 'High'
                                  : row.score >= 6
                                    ? 'Medium'
                                    : 'Low'
                                : ''}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="block md:hidden px-4 pb-4 space-y-4">
                {items.map((row) => (
                  <div key={`mobile-${row.id}`} className="rounded-2xl border border-gray-100 bg-white shadow-sm p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="text-sm font-semibold text-gray-900 truncate">{row.video_name}</div>
                        <span className={`text-xs px-2 py-1 rounded-full inline-flex items-center w-fit ${statusClasses(row.status)}`}>
                          {statusLabel(row.status)}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-gray-500">FYP Score</div>
                        <div className="text-lg font-semibold text-gray-900">
                          {typeof row.score === 'number' ? row.score.toFixed(1) : ''}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      Scheduled: {formatSchedule(row.scheduled_at, row.next_check_at)}
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      <button
                        onClick={() => setExpandedRowId(expandedRowId === row.id ? null : row.id)}
                        className="border border-gray-200 hover:bg-gray-50 rounded-xl px-4 py-2 text-sm text-gray-700"
                      >
                        Lihat Detail
                      </button>
                      <button
                        onClick={() => onRegenerate(row.id)}
                        className="bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl px-4 py-2 text-sm disabled:opacity-60"
                        disabled={regeneratingId === row.id || isTrialExpired}
                      >
                         Regenerate AI
                      </button>
                    </div>
                    {expandedRowId === row.id && (
                      <div className="rounded-xl border border-gray-100 bg-gray-50 p-3 text-xs text-gray-700 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold">Hook:</span>
                          <span>{row.hook_text || ''}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold">CTA:</span>
                          <span>{row.cta_text || ''}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold">Hashtags:</span>
                          {getHashtagList(row.hashtags).length > 0 ? (
                            getHashtagList(row.hashtags).map((tag) => (
                              <span key={`${row.id}-${tag}`} className="px-2 py-0.5 rounded-full bg-white border border-gray-200 text-gray-600">
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span></span>
                          )}
                        </div>
                        <div className="space-y-1">
                          <span className="font-semibold">Score reasons:</span>
                          <ul className="grid gap-1">
                            {(row.score_reasons || []).length > 0 ? (
                              row.score_reasons?.map((reason, idx) => (
                                <li key={`mobile-reason-${row.id}-${idx}`} className="flex items-start gap-2">
                                  <span className="text-emerald-500"></span>
                                  <span>{reason.replace(/\(\s*<=\s*10\s*kata\s*\)/gi, '').trim()}</span>
                                </li>
                              ))
                            ) : (
                              <li className="text-gray-500"></li>
                            )}
                          </ul>
                        </div>
                        <div className="text-[11px] text-gray-500">
                          <span className="font-semibold text-gray-600">AI Confidence:</span>{' '}
                          {typeof row.score === 'number'
                            ? row.score >= 8
                              ? 'High'
                              : row.score >= 6
                                ? 'Medium'
                                : 'Low'
                            : ''}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
        {isAdmin && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">Midtrans Status</span>
                <button
                  onClick={onMidtransStatusRefresh}
                  className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                >
                  Refresh
                </button>
              </div>
              {midtransStatusLoading && (
                <div className="px-6 py-6 text-sm text-slate-500">Memuat status Midtrans...</div>
              )}
              {midtransStatusError && (
                <div className="px-6 py-6 text-sm text-red-600">{midtransStatusError}</div>
              )}
              {!midtransStatusLoading && !midtransStatusError && midtransStatus && (
                <div className="px-6 py-5 space-y-4">
                  <div className="flex flex-wrap gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${midtransStatus.midtrans_is_production ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                      {midtransStatus.midtrans_is_production ? 'Production Mode' : 'Sandbox Mode'}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${midtransStatus.server_key_configured ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                      Server Key {midtransStatus.server_key_configured ? 'OK' : 'Missing'}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${midtransStatus.client_key_configured ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                      Client Key {midtransStatus.client_key_configured ? 'OK' : 'Missing'}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {Object.entries(midtransStatus.packages || {}).map(([pkgId, pkg]) => {
                      const pkgData = pkg as { price: number; coins: number };
                      return (
                        <div key={pkgId} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-slate-600">
                          <span className="font-semibold text-slate-700">{pkgId}</span>
                          <span>Rp {Number(pkgData.price).toLocaleString('id-ID')}  {pkgData.coins} coins</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm font-semibold text-slate-700">Feedback Weights (AI Learning)</span>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={feedbackWeightsQuery}
                    onChange={(event) => onFeedbackWeightsQueryChange(event.target.value)}
                    placeholder="User ID / email"
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                  <button
                    onClick={onFeedbackWeightsRefresh}
                    className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                  >
                    Refresh
                  </button>
                </div>
              </div>
              {feedbackWeightsLoading && (
                <div className="px-6 py-6 text-sm text-slate-500">Memuat feedback weights...</div>
              )}
              {feedbackWeightsError && (
                <div className="px-6 py-6 text-sm text-red-600">{feedbackWeightsError}</div>
              )}
              {!feedbackWeightsLoading && !feedbackWeightsError && feedbackWeights && (
                <div className="px-6 py-5 space-y-4 text-xs text-slate-600">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-700">User:</span>
                    <span>{feedbackWeights.user_id}</span>
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 text-[10px] font-semibold">
                      Strength {feedbackWeights.learning_strength.toFixed(2)}
                    </span>
                  </div>
                  {(['hook', 'cta', 'hashtag'] as const).map((type) => (
                    <div key={type} className="grid gap-2">
                      <span className="uppercase text-[10px] font-semibold text-slate-400">{type}  User</span>
                      <div className="flex flex-wrap gap-2">
                        {feedbackWeights.weights?.[type] &&
                          Object.entries(feedbackWeights.weights[type] || {}).map(([key, value]) => (
                            <span
                              key={`${type}-user-${key}`}
                              className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-[11px]"
                            >
                              {key}  {Number(value).toFixed(2)}
                            </span>
                          ))}
                        {!feedbackWeights.weights?.[type] && (
                          <span className="text-slate-400">Belum ada data.</span>
                        )}
                      </div>
                      <span className="uppercase text-[10px] font-semibold text-slate-400 mt-2">{type}  Global</span>
                      <div className="flex flex-wrap gap-2">
                        {feedbackWeights.global_weights?.[type] &&
                          Object.entries(feedbackWeights.global_weights[type] || {}).map(([key, value]) => (
                            <span
                              key={`${type}-global-${key}`}
                              className="px-2 py-1 rounded-full bg-indigo-50 text-indigo-600 text-[11px]"
                            >
                              {key}  {Number(value).toFixed(2)}
                            </span>
                          ))}
                        {!feedbackWeights.global_weights?.[type] && (
                          <span className="text-slate-400">Belum ada data.</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <span className="text-sm font-semibold text-slate-700">Trial & Subscription Control</span>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={subscriptionQuery}
                    onChange={(event) => onSubscriptionQueryChange(event.target.value)}
                    placeholder="User ID / email"
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                  <button
                    onClick={onSubscriptionLookup}
                    className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                  >
                    Lookup
                  </button>
                </div>
              </div>
              {subscriptionLoading && (
                <div className="px-6 py-6 text-sm text-slate-500">Memuat status user...</div>
              )}
              {subscriptionError && (
                <div className="px-6 py-6 text-sm text-red-600">{subscriptionError}</div>
              )}
              {!subscriptionLoading && !subscriptionError && subscriptionInfo && (
                <div className="px-6 py-5 space-y-3 text-xs text-slate-600">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-700">User:</span>
                    <span>{subscriptionInfo.user_id}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`px-2 py-1 rounded-full text-[10px] font-semibold ${subscriptionInfo.subscribed ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                      {subscriptionInfo.subscribed ? 'Subscribed' : 'Free Trial'}
                    </span>
                    <span className="px-2 py-1 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">
                      Trial tersisa: {subscriptionInfo.trial_upload_remaining}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => onSubscriptionUpdate({ user_id: subscriptionInfo.user_id, subscribed: true })}
                      className="px-3 py-1.5 text-xs rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                    >
                      Set Pro
                    </button>
                    <button
                      onClick={() => onSubscriptionUpdate({ user_id: subscriptionInfo.user_id, subscribed: false })}
                      className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
                    >
                      Set Free
                    </button>
                    <button
                      onClick={() => onSubscriptionUpdate({ user_id: subscriptionInfo.user_id, trial_upload_remaining: 3 })}
                      className="px-3 py-1.5 text-xs rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100"
                    >
                      Reset Trial (3)
                    </button>
                    <button
                      onClick={() => onSubscriptionUpdate({ user_id: subscriptionInfo.user_id, trial_upload_remaining: 0 })}
                      className="px-3 py-1.5 text-xs rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100"
                    >
                      Set Trial 0
                    </button>
                  </div>
                  {subscriptionStatus && (
                    <div className="text-[11px] text-emerald-600">{subscriptionStatus}</div>
                  )}
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-700">Admin Autopost Logs</span>
              <div className="flex items-center gap-2">
                <input
                  value={adminLogsUserQuery}
                  onChange={(event) => onAdminLogsUserQueryChange(event.target.value)}
                  placeholder="Cari user..."
                  className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                />
                <input
                  type="date"
                  value={adminLogsDateFrom}
                  onChange={(event) => onAdminLogsDateFromChange(event.target.value)}
                  className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                />
                <input
                  type="date"
                  value={adminLogsDateTo}
                  onChange={(event) => onAdminLogsDateToChange(event.target.value)}
                  className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                />
                <select
                  value={adminLogsStatus}
                  onChange={(event) => onAdminLogsStatusChange(event.target.value)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                >
                  <option value="ALL">Semua status</option>
                  <option value="QUEUED">QUEUED</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="WAITING_RECHECK">WAITING_RECHECK</option>
                  <option value="POSTED">POSTED</option>
                  <option value="FAILED">FAILED</option>
                </select>
                <select
                  value={adminLogsLimit}
                  onChange={(event) => onAdminLogsLimitChange(Number(event.target.value))}
                  className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <button
                  onClick={onAdminLogsRefresh}
                  className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                >
                  Refresh
                </button>
              </div>
            </div>
            <div className="grid grid-cols-[1.2fr_1.6fr_1fr_0.8fr_1fr] gap-3 px-6 py-3 text-xs font-semibold text-slate-400 uppercase">
              <span>User</span>
              <span>Video</span>
              <span>Status</span>
              <span>Score</span>
              <span>Engagement</span>
            </div>
            {adminLogsLoading && (
              <div className="px-6 py-6 text-sm text-slate-500">Memuat log...</div>
            )}
            {adminLogsError && (
              <div className="px-6 py-6 text-sm text-red-600">{adminLogsError}</div>
            )}
            {!adminLogsLoading && !adminLogsError && filteredAdminLogs.length === 0 && (
              <div className="px-6 py-6 text-sm text-slate-500">Belum ada aktivitas.</div>
            )}
            {!adminLogsLoading && !adminLogsError && filteredAdminLogs.map((row: AdminAutopostLog) => (
              <div key={`admin-log-${row.id}`} className="grid grid-cols-[1.2fr_1.6fr_1fr_0.8fr_1fr] gap-3 px-6 py-4 text-sm border-t border-slate-100 items-center">
                <span className="text-slate-600 truncate">{row.user_id}</span>
                <span className="text-slate-700 truncate">{row.video_name}</span>
                <span className={`text-xs px-2 py-1 rounded-full inline-flex items-center w-fit ${statusClasses(row.status)}`}>
                  {statusLabel(row.status)}
                </span>
                <span className="text-slate-600">{typeof row.score === 'number' ? row.score.toFixed(1) : ''}</span>
                <span className="text-slate-500">
                  {row.views ?? 0}V  {row.likes ?? 0}L  {row.comments ?? 0}C  {row.shares ?? 0}S
                </span>
              </div>
            ))}
            </div>
            <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">Admin Audit Log</span>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={adminAuditActor}
                    onChange={(event) => setAdminAuditActor(event.target.value)}
                    placeholder="Actor"
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                  />
                  <input
                    value={adminAuditTarget}
                    onChange={(event) => setAdminAuditTarget(event.target.value)}
                    placeholder="Target"
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                  />
                  <select
                    value={adminAuditAction}
                    onChange={(event) => setAdminAuditAction(event.target.value)}
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 focus:outline-none"
                  >
                    <option value="ALL">Semua aksi</option>
                    <option value="subscription_update">subscription_update</option>
                  </select>
                  <button
                    onClick={onAdminAuditRefresh}
                    className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
                  >
                    Refresh
                  </button>
                  <button
                    onClick={() => {
                      const csv = [
                        ['id', 'actor', 'action', 'target', 'details', 'created_at'].join(','),
                        ...adminAuditLogs.map((row) => [
                          row.id,
                          row.actor_email || row.actor_user_id,
                          row.action,
                          row.target_user_id || '',
                          JSON.stringify(row.details || {}),
                          row.created_at || ''
                        ].map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
                      ].join('\n');
                      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                      const link = document.createElement('a');
                      link.href = URL.createObjectURL(blob);
                      link.download = 'admin-audit-logs.csv';
                      link.click();
                    }}
                    className="px-3 py-1.5 text-xs rounded-lg bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition"
                  >
                    Export CSV
                  </button>
                </div>
              </div>
              {adminAuditLoading && (
                <div className="px-6 py-6 text-sm text-slate-500">Memuat audit log...</div>
              )}
              {adminAuditError && (
                <div className="px-6 py-6 text-sm text-red-600">{adminAuditError}</div>
              )}
              {!adminAuditLoading && !adminAuditError && adminAuditLogs.length === 0 && (
                <div className="px-6 py-6 text-sm text-slate-500">Belum ada aktivitas admin.</div>
              )}
              {!adminAuditLoading && !adminAuditError && adminAuditLogs.map((row: AdminAuditLog) => (
                <div key={`audit-${row.id}`} className="grid grid-cols-[1.2fr_1.2fr_1fr_1.2fr] gap-3 px-6 py-4 text-xs border-t border-slate-100 items-center">
                  <span className="text-slate-600 truncate">{row.actor_email || row.actor_user_id}</span>
                  <span className="text-slate-700">{row.action}</span>
                  <span className="text-slate-600 truncate">{row.target_user_id || ''}</span>
                  <span className="text-slate-500 truncate">
                    {row.details?.subscribed !== undefined
                      ? `subscribed=${row.details.subscribed} trial=${row.details.trial_upload_remaining}`
                      : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-700">Upload Data TikTok</h3>
              <p className="text-xs text-slate-500">
                Upload file metrics (JSON/TXT) agar sistem menganalisis performa dan memberi rekomendasi berikutnya.
              </p>
            </div>
            <button
              onClick={onMetricsUploadClick}
              className="px-3 py-1.5 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition disabled:opacity-60"
              disabled={metricsUploading || isTrialExpired}
            >
              {metricsUploading ? 'Uploading...' : 'Upload Data'}
            </button>
          </div>
          <div className="mb-3">
            <a
              href={ROUTES.help}
              className="text-xs text-indigo-600 hover:text-indigo-700"
            >
              Lihat panduan unduh data tiktok kamu disini 
            </a>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
            <input
              value={metricsVideoId}
              onChange={(event) => onMetricsVideoIdChange(event.target.value)}
              placeholder="video_id (opsional)"
              className="px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <span>Format: JSON atau TXT (harus berisi `video_id`).</span>
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-slate-600">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="font-semibold text-slate-700 mb-1">Contoh JSON</div>
              <pre className="whitespace-pre-wrap text-slate-600">{`{
  "video_id": 123,
  "views": 1200,
  "likes": 45,
  "comments": 8,
  "shares": 3,
  "posted_at": "2026-01-18T10:30:00"
}`}</pre>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="font-semibold text-slate-700 mb-1">Contoh TXT</div>
              <pre className="whitespace-pre-wrap text-slate-600">{`video_id: 123
views: 1200
likes: 45
comments: 8
shares: 3
posted_at: 2026-01-18T10:30:00`}</pre>
            </div>
          </div>
          <input
            ref={metricsUploadRef}
            type="file"
            accept=".json,.txt,text/plain,application/json"
            className="hidden"
            onChange={onMetricsUploadChange}
          />
          {metricsUploadResult.status === 'success' && (
            <div className="mt-3 text-xs text-emerald-600">{metricsUploadResult.message}</div>
          )}
          {metricsUploadResult.status === 'error' && (
            <div className="mt-3 text-xs text-red-600">{metricsUploadResult.message}</div>
          )}
        </div>
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">Template Hook & CTA</h3>
            {templatesLoading && <span className="text-xs text-slate-500">Memuat...</span>}
          </div>
          {templatesError && <div className="text-xs text-red-600 mb-2">{templatesError}</div>}
          {templates && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <div className="font-semibold text-slate-600 mb-2">Hooks</div>
                {templates.hooks.map((text, idx) => (
                  <div key={`hook-${idx}`} className="flex items-start gap-2 mb-2">
                    <span className="text-slate-500">{idx + 1}.</span>
                    <span className="text-slate-700 flex-1">{text}</span>
                    <button
                      onClick={() => onCopyTemplate(text)}
                      className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
                    >
                      Copy
                    </button>
                  </div>
                ))}
              </div>
              <div>
                <div className="font-semibold text-slate-600 mb-2">CTA</div>
                {templates.ctas.map((text, idx) => (
                  <div key={`cta-${idx}`} className="flex items-start gap-2 mb-2">
                    <span className="text-slate-500">{idx + 1}.</span>
                    <span className="text-slate-700 flex-1">{text}</span>
                    <button
                      onClick={() => onCopyTemplate(text)}
                      className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
                    >
                      Copy
                    </button>
                  </div>
                ))}
              </div>
              <div>
                <div className="font-semibold text-slate-600 mb-2">Captions</div>
                {templates.captions.map((text, idx) => (
                  <div key={`cap-${idx}`} className="flex items-start gap-2 mb-2">
                    <span className="text-slate-500">{idx + 1}.</span>
                    <span className="text-slate-700 flex-1">{text}</span>
                    <button
                      onClick={() => onCopyTemplate(text)}
                      className="px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
                    >
                      Copy
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">Engagement Insights</h3>
            {insightsLoading && <span className="text-xs text-slate-500">Memuat...</span>}
          </div>
          {insightsError && <div className="text-xs text-red-600 mb-2">{insightsError}</div>}
          {insights && (
            <div className="space-y-3 text-xs text-slate-600">
              <div>
                <div className="font-semibold text-slate-700 mb-1">Fatigue Alerts</div>
                {insights.fatigue_alerts.length === 0 ? (
                  <div className="text-slate-500">Tidak ada alert.</div>
                ) : (
                  insights.fatigue_alerts.map((alert, idx) => (
                    <div key={`fatigue-${idx}`}> {alert.text}</div>
                  ))
                )}
              </div>
              <div>
                <div className="font-semibold text-slate-700 mb-1">Trend Decay</div>
                <div className="text-slate-500">
                  {insights.trend_decay.status} ( {insights.trend_decay.delta})
                </div>
              </div>
              <div>
                <div className="font-semibold text-slate-700 mb-1">Best Posting Times</div>
                {insights.best_times.length === 0 ? (
                  <div className="text-slate-500">Belum ada data.</div>
                ) : (
                  insights.best_times.map((t, idx) => (
                    <div key={`time-${idx}`}> {t.hour}:00  ER {t.engagement_rate}</div>
                  ))
                )}
              </div>
              <div>
                <div className="font-semibold text-slate-700 mb-1">Retention</div>
                <div className="text-slate-500">
                  Drop-off: {insights.retention_summary.dropoff_second ?? '-'}s
                </div>
              </div>
              <div>
                <div className="font-semibold text-slate-700 mb-1">Recommendations</div>
                {insights.recommendations.length === 0 ? (
                  <div className="text-slate-500">Tidak ada.</div>
                ) : (
                  insights.recommendations.map((rec, idx) => (
                    <div key={`rec-${idx}`}> {rec}</div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        {isAdmin && (
          <div className="bg-white rounded-2xl shadow-md border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Competitor Snapshot</h3>
              <button
                onClick={onAddCompetitor}
                className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Add Competitor
              </button>
            </div>
            {competitors.length === 0 ? (
              <div className="text-xs text-slate-500">Belum ada competitor.</div>
            ) : (
              <div className="space-y-2 text-xs text-slate-600">
                {competitors.map((c) => (
                  <div key={c.id} className="border border-slate-100 rounded-lg p-2">
                    <div className="font-semibold text-slate-700">{c.title}</div>
                    {c.url && <div className="text-slate-500">{c.url}</div>}
                    {c.notes && <div className="text-slate-500">{c.notes}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
export default DashboardView;
