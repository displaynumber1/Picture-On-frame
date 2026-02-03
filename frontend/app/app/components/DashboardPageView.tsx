'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Session } from '@supabase/supabase-js';
import { 
  Upload, 
  Sparkles, 
  Image as ImageIcon, 
  Camera, 
  Layers, 
  Sun, 
  Maximize, 
  Loader2,
  Download,
  LayoutGrid,
  Edit3,
  Package,
  CheckCircle2,
  User,
  Lock,
  Hand,
  Tag,
  Monitor,
  Video,
  Copy,
  Check,
  LogOut,
  Wallet,
  Coins,
  X,
  Lightbulb,
  Save,
  List
} from 'lucide-react';
import { generateProductPhoto, generateProductVideo } from '../../../services/geminiService';
import { generateImagesWithFal, buildPromptFromOptions, createVideoFromImage, createVideoBatchFromImage, createKlingVideoFromImage } from '../../../services/falService';
import { supabaseService } from '../../../services/supabaseService';
import { midtransService } from '../../../services/midtransService';
import { ROUTES } from '../../../lib/routes';
import DashboardView from './DashboardView';
// IdentitySelector: import and render in generate form area when needed.
import IdentitySelector, { type IdentityMode } from '../../../components/IdentitySelector';
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
import { 
  BACKGROUND_OPTIONS, 
  STYLE_OPTIONS, 
  LIGHTING_OPTIONS, 
  ASPECT_RATIOS, 
  CAMERA_ANGLES,
  MODEL_TYPES,
  CATEGORY_OPTIONS,
  INTERACTION_OPTIONS,
  CONTENT_TYPES,
  POSE_MAP
} from '../../../constants';
import { AppState, GenerationOptions, ImageData, GenerationResult } from '../../../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

declare global {
  interface Window {
    aistudio?: {
      hasSelectedApiKey: () => Promise<boolean>;
      openSelectKey: () => Promise<void>;
    };
  }
}

const INITIAL_OPTIONS: GenerationOptions = {
  background: BACKGROUND_OPTIONS[0],
  customBackgroundPrompt: '',
  pose: '', // Will be set by effect
  customPosePrompt: '',
  style: STYLE_OPTIONS[0],
  customStylePrompt: '',
  lighting: LIGHTING_OPTIONS[0],
  customLightingPrompt: '',
  aspectRatio: ASPECT_RATIOS[0],
  cameraAngle: CAMERA_ANGLES[0],
  contentType: CONTENT_TYPES[0], // Model
  modelType: MODEL_TYPES[0],
  category: CATEGORY_OPTIONS[0],
  interactionType: INTERACTION_OPTIONS[INTERACTION_OPTIONS.length - 1], // Tanpa Interaksi (last item)
  backgroundColor: '#ffffff'
};

const SectionHeader: React.FC<{ icon: any, title: string, step: string }> = ({ icon: Icon, title, step }) => (
  <div className="flex items-center gap-3 mb-5">
    <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600">
      <Icon size={16} />
    </div>
    <div className="flex flex-col">
      <span className="text-[9px] font-bold text-purple-400 tracking-[0.2em] uppercase">Step {step}</span>
      <h3 className="text-[11px] font-extrabold tracking-tight uppercase text-gray-800 transition-colors duration-300 cursor-default hover:text-purple-600">{title}</h3>
    </div>
  </div>
);

const OptionChip: React.FC<{ label: string, isSelected: boolean, onClick: () => void }> = ({ label, isSelected, onClick }) => {
  // Filter out empty or whitespace-only labels
  if (!label || typeof label !== 'string' || label.trim() === '') {
    return null;
  }
  
  const baseClasses = "px-4 py-1.5 text-[10px] font-bold tracking-tight rounded-xl transition-all duration-300 border";
  const selectedClasses = "bg-purple-600 text-white border-purple-600 shadow-md shadow-purple-200 hover:bg-purple-700 hover:shadow-purple-300";
  const unselectedClasses = "bg-white text-gray-800 border-gray-200 hover:border-purple-300 hover:bg-white hover:shadow-md hover:shadow-purple-100";
  
  return (
    <button
      type="button"
      onClick={onClick}
      className={`${baseClasses} ${isSelected ? selectedClasses : unselectedClasses}`}
    >
      {label.trim()}
    </button>
  );
};

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button 
      onClick={handleCopy}
      className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-purple-600"
      title="Salin Prompt"
    >
      {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
    </button>
  );
};

type VariantPreset = {
  id: string;
  name: string;
  options: GenerationOptions;
  createdAt: string;
};

export default function App() {
  const router = useRouter();
  const IMAGE_BATCH_COINS = 75;
  const PRO_VIDEO_COINS = 185;
  const toSafeErrorMessage = (error: any, fallback: string) => {
    const message = typeof error?.message === 'string' ? error.message : '';
    if (/pal\.ai|fal\.ai|fal/gi.test(message)) {
      return 'Error generated: Periksa inputan kamu';
    }
    const safeMessages = new Set([
      'Sesi Anda telah berakhir. Silakan login ulang.',
      'Maaf coin anda tidak mencukupi, silahkan lakukan top-up',
      'Tidak ada video yang dihasilkan. Silakan coba lagi.'
    ]);
    return safeMessages.has(message) ? message : fallback;
  };

  const refreshSubscriptionStatus = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/billing/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const data = await response.json();
      const status = data?.status || 'inactive';
      setProStatus(status);
      setSubscribedUntil(data?.subscribed_until || null);
      setIsSubscribed(Boolean(data?.subscribed));
      setRenewWindow(Boolean(data?.renew_window));
      setExpiresInDays(typeof data?.expires_in_days === 'number' ? data.expires_in_days : null);
    } catch {
      // silent
    }
  }, []);

  const handleUpgradeClick = async () => {
    try {
      setUpgradeLoading(true);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      await midtransService.loadSnapScript();
      const snapToken = await midtransService.initializeSubscriptionSnap(token, 30);
      const snap = (window as any).snap;
      if (!snap?.pay) {
        throw new Error('Midtrans Snap tidak tersedia.');
      }
      snap.pay(snapToken, {
        onSuccess: () => {
          setShowUpgradeModal(false);
          setProPending(false);
          refreshSubscriptionStatus();
        },
        onPending: () => {
          setShowUpgradeModal(false);
          setProPending(true);
          setProStatus('pending');
          refreshSubscriptionStatus();
        },
        onError: () => {
          setDashboardError('Pembayaran gagal. Silakan coba lagi.');
        }
      });
    } catch (error: any) {
      setDashboardError(error?.message || 'Gagal memulai pembayaran.');
    } finally {
      setUpgradeLoading(false);
    }
  };

  const handleTrialExpired = (payload: any) => {
    if (payload?.error === 'TRIAL_EXPIRED') {
      setShowUpgradeModal(true);
      return true;
    }
    return false;
  };


  const [state, setState] = useState<AppState>({
    productImage: null,
    productImage2: null,
    productImage3: null,
    productImage4: null,
    faceImage: null,
    backgroundImage: null,
    options: INITIAL_OPTIONS,
    isGenerating: false,
    isVideoGenerating: {},
    isKlingVideoGenerating: {},
    videoResults: {},
    klingVideoResults: {},
    klingSelectedImages: {},
    videoBatches: {},  // 3 videos per image: { imageIndex: [video1, video2, video3] }
    isVideoBatchGenerating: {},  // Loading state for batch video generation
    results: [],
    error: null
  });
  const [identityMode, setIdentityMode] = useState<IdentityMode>('none');

  const [coins, setCoins] = useState<number>(0);
  const [showCoinModal, setShowCoinModal] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [displayName, setDisplayName] = useState('User');
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [showDashboard] = useState(true);
  const [dashboardItems, setDashboardItems] = useState<AutopostDashboardItem[]>([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [dashboardErrorNeedsTopUp, setDashboardErrorNeedsTopUp] = useState(false);
  const [trialRemaining, setTrialRemaining] = useState<number | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscribedUntil, setSubscribedUntil] = useState<string | null>(null);
  const [proStatus, setProStatus] = useState<'active' | 'expired' | 'inactive' | 'pending'>('inactive');
  const [proPending, setProPending] = useState(false);
  const [renewWindow, setRenewWindow] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState<number | null>(null);
  const [dashboardRegeneratingId, setDashboardRegeneratingId] = useState<number | null>(null);
  const [variantName, setVariantName] = useState('');
  const [variants, setVariants] = useState<VariantPreset[]>([]);
  const [adminLogs, setAdminLogs] = useState<AdminAutopostLog[]>([]);
  const [adminLogsLoading, setAdminLogsLoading] = useState(false);
  const [adminLogsError, setAdminLogsError] = useState<string | null>(null);
  const [feedbackWeights, setFeedbackWeights] = useState<AutopostFeedbackWeights | null>(null);
  const [feedbackWeightsLoading, setFeedbackWeightsLoading] = useState(false);
  const [feedbackWeightsError, setFeedbackWeightsError] = useState<string | null>(null);
  const [feedbackWeightsQuery, setFeedbackWeightsQuery] = useState('');
  const [subscriptionQuery, setSubscriptionQuery] = useState('');
  const [subscriptionInfo, setSubscriptionInfo] = useState<AdminSubscriptionInfo | null>(null);
  const [subscriptionLoading, setSubscriptionLoading] = useState(false);
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState<string | null>(null);
  const [adminAuditLogs, setAdminAuditLogs] = useState<AdminAuditLog[]>([]);
  const [adminAuditLoading, setAdminAuditLoading] = useState(false);
  const [adminAuditError, setAdminAuditError] = useState<string | null>(null);
  const [adminAuditActor, setAdminAuditActor] = useState('');
  const [adminAuditTarget, setAdminAuditTarget] = useState('');
  const [adminAuditAction, setAdminAuditAction] = useState('ALL');
  const [adminLogsStatus, setAdminLogsStatus] = useState('ALL');
  const [adminLogsUserQuery, setAdminLogsUserQuery] = useState('');
  const [adminLogsDateFrom, setAdminLogsDateFrom] = useState('');
  const [adminLogsDateTo, setAdminLogsDateTo] = useState('');
  const [adminLogsLimit, setAdminLogsLimit] = useState(50);
  const [midtransStatus, setMidtransStatus] = useState<AdminMidtransStatus | null>(null);
  const [midtransStatusLoading, setMidtransStatusLoading] = useState(false);
  const [midtransStatusError, setMidtransStatusError] = useState<string | null>(null);
  const [trendsPreview, setTrendsPreview] = useState<TrendsPreview | null>(null);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [trendsMessage, setTrendsMessage] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [trendsSearch, setTrendsSearch] = useState('');
  const [trendsPage, setTrendsPage] = useState(1);
  const [trendsPageSize] = useState(20);
  const [trendsCategory, setTrendsCategory] = useState('');
  const [importStatus, setImportStatus] = useState<{ status: string; processed: number; total: number; valid: number; invalid: number } | null>(null);
  const [importErrors, setImportErrors] = useState<string[]>([]);
  const [categoryOptions, setCategoryOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [autoRetryImport, setAutoRetryImport] = useState(true);
  const importErrorRef = useRef<HTMLDivElement>(null);
  const [hashtagRegex, setHashtagRegex] = useState<string>('');
  const [templates, setTemplates] = useState<EngagementTemplates | null>(null);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [showOnlyErrors, setShowOnlyErrors] = useState(false);
  const [hideErrorHighlight, setHideErrorHighlight] = useState(false);
  const [insights, setInsights] = useState<AutopostInsights | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState<string | null>(null);
  const [competitors, setCompetitors] = useState<Array<{ id: number; title: string; url?: string; notes?: string }>>([]);
  const [metricsVideoId, setMetricsVideoId] = useState('');
  const [metricsUploadResult, setMetricsUploadResult] = useState<MetricsUploadResult>({
    status: 'idle',
    message: null
  });
  const [metricsUploading, setMetricsUploading] = useState(false);
  const metricsUploadRef = useRef<HTMLInputElement>(null);
  const errorRowSet = new Set(
    importErrors
      .map((err) => {
        const match = err.match(/Row\s+(\d+)/i);
        return match ? Number(match[1]) : null;
      })
      .filter((v): v is number => typeof v === 'number' && !Number.isNaN(v))
  );
  const errorRowsInPage = Array.from(errorRowSet).filter((rowNum) => {
    const start = (trendsPage - 1) * trendsPageSize + 1;
    const end = trendsPage * trendsPageSize;
    return rowNum >= start && rowNum <= end;
  });
  const errorPages = Array.from(errorRowSet)
    .map((rowNum) => Math.ceil(rowNum / trendsPageSize))
    .filter((value, index, self) => self.indexOf(value) === index)
    .sort((a, b) => a - b);

  const isAnimalModel = state.options.contentType === "Model" && state.options.modelType === "Hewan";
  const getFilteredInteractions = () => {
    let interactions = [...INTERACTION_OPTIONS];
    if (state.options.contentType === "Non Model" && state.options.category !== "Sandal/Sepatu") {
      interactions = interactions.filter(option => !option.toLowerCase().includes("kaki"));
    }
    return interactions;
  };
  const getFilteredPoses = () => {
    const isNonModel = state.options.contentType === "Non Model";
    const isTanpaInteraksi = state.options.interactionType === "Tanpa Interaksi";
    if (isAnimalModel) {
      return ["Close-Up Portrait"];
    }
    let poses = POSE_MAP[state.options.contentType]?.[state.options.category] || [];

    if (isNonModel && state.options.category === "Sandal/Sepatu") {
      const sandalPoseByInteraction: Record<string, string[]> = {
        "Pegang 1 Tangan Wanita": ["Tangan Memegang Sepasang Sandal/Sepatu"],
        "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan sepatu"],
        "Pegang 1 Tangan Pria": ["Tangan Memegang Sepasang Sandal/Sepatu"],
        "Pegang 2 Tangan Pria": ["Dua tangan menampilkan sepatu"],
        "Kaki Wanita": [
          "Kaki wanita berdiri natural mengenakan sepatu",
          "Kaki wanita melangkah",
          "Kaki wanita dengan tumit terangkat",
          "Kaki wanita naik tangga",
          "Kaki wanita berdiri simetris (dua kaki sejajar)"
        ],
        "Kaki Pria": [
          "Kaki pria berdiri tegap mengenakan sepatu",
          "Kaki pria melangkah santai",
          "Kaki pria satu kaki maju ke depan",
          "Kaki pria berada di jalan atau tangga"
        ]
      };
      const posesForInteraction = sandalPoseByInteraction[state.options.interactionType];
      if (posesForInteraction) {
        return posesForInteraction;
      }
    }

    if (isNonModel) {
      const nonModelPoseByInteraction: Record<string, Record<string, string[]>> = {
        "Fashion": {
          "Pegang 1 Tangan Wanita": ["Pegang produk dengan satu tangan"],
          "Pegang 2 Tangan Wanita": ["Pegang produk dengan dua tangan"],
          "Pegang 1 Tangan Pria": ["Pegang produk dengan satu tangan"],
          "Pegang 2 Tangan Pria": ["Pegang produk dengan dua tangan"],
          "Pegang Hanger dengan Produk": ["Pegang hanger dengan produk"],
          "Tanpa Interaksi": [
            "Produk digantung menggunakan hanger",
            "Hanger digantung di standing rack",
            "Hanger digantung di hook",
            "Produk dilipat dan diletakkan di meja",
            "Flatlay produk fashion"
          ]
        },
        "Beauty": {
          "Pegang 1 Tangan Wanita": ["Tangan memegang produk"],
          "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan produk"],
          "Pegang 1 Tangan Pria": ["Tangan memegang produk"],
          "Pegang 2 Tangan Pria": ["Dua tangan menampilkan produk"],
          "Tanpa Interaksi": [
            "Produk diletakkan di meja aesthetic",
            "Produk didekatkan ke area wajah tanpa menampilkan wajah",
            "Flatlay produk beauty"
          ]
        },
        "Tas": {
          "Pegang 1 Tangan Wanita": ["Tangan memegang tas"],
          "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan tas"],
          "Pegang 1 Tangan Pria": ["Tangan memegang tas"],
          "Pegang 2 Tangan Pria": ["Dua tangan menampilkan tas"],
          "Tanpa Interaksi": [
            "Tas digantung",
            "Tas diletakkan di meja aesthetic",
            "Tas disandarkan pada kursi atau properti"
          ]
        },
        "Aksesoris": {
          "Pegang 1 Tangan Wanita": ["Tangan memegang produk"],
          "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan produk"],
          "Pegang 1 Tangan Pria": ["Tangan memegang produk"],
          "Pegang 2 Tangan Pria": ["Dua tangan menampilkan produk"],
          "Tanpa Interaksi": [
            "Produk di meja aesthetic",
            "Detail tekstur close-up",
            "Flatlay aksesoris"
          ]
        },
        "Home Living": {
          "Pegang 1 Tangan Wanita": ["Tangan memegang produk"],
          "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan produk"],
          "Pegang 1 Tangan Pria": ["Tangan memegang produk"],
          "Pegang 2 Tangan Pria": ["Dua tangan menampilkan produk"],
          "Tanpa Interaksi": [
            "Produk diletakkan di meja",
            "Produk diletakkan di lantai",
            "Detail tekstur produk",
            "Flatlay produk home living"
          ]
        },
        "Food & Beverage": {
          "Pegang 1 Tangan Wanita": ["Tangan memegang produk"],
          "Pegang 2 Tangan Wanita": ["Dua tangan menampilkan produk"],
          "Pegang 1 Tangan Pria": ["Tangan memegang produk"],
          "Pegang 2 Tangan Pria": ["Dua tangan menampilkan produk"],
          "Tanpa Interaksi": [
            "Produk diletakkan di meja",
            "Close-up tekstur makanan atau minuman",
            "Flatlay food and beverage"
          ]
        }
      };
      const categoryMap = nonModelPoseByInteraction[state.options.category];
      const posesForInteraction = categoryMap?.[state.options.interactionType];
      if (posesForInteraction) {
        return posesForInteraction;
      }
    }
    
    if (isNonModel && isTanpaInteraksi) {
      const humanKeywords = ["tangan", "kaki", "pegang", "angkat", "hanger", "melangkah", "naik tangga", "mengenakan"];
      poses = poses.filter(p => {
        const pLower = p.toLowerCase();
        return !humanKeywords.some(keyword => pLower.includes(keyword));
      });
    }
    
    return poses;
  };

  const currentPoses = getFilteredPoses();
  const currentInteractions = getFilteredInteractions();

  useEffect(() => {
    if (!isAnimalModel) return;
    if (state.options.category !== "Aksesoris") {
      updateOption('category', "Aksesoris");
    }
    if (state.options.pose !== "Close-Up Portrait") {
      updateOption('pose', "Close-Up Portrait");
    }
  }, [isAnimalModel, state.options.category, state.options.pose]);
  
  // Check authentication on mount (non-blocking)
  const refreshCoins = React.useCallback(async () => {
    try {
      const profile = await supabaseService.getProfile();
      if (profile && typeof profile.coins_balance === 'number') {
        setCoins(profile.coins_balance);
      }
      if (profile?.trial_upload_remaining !== undefined && profile?.trial_upload_remaining !== null) {
        setTrialRemaining(profile.trial_upload_remaining);
      }
      if (profile?.subscribed !== undefined && profile?.subscribed !== null) {
        let active = Boolean(profile.subscribed);
        const expiresAt = profile.subscribed_until || profile.subscription_expires_at;
        if (active && expiresAt) {
          const dt = new Date(expiresAt);
          if (!Number.isNaN(dt.getTime())) {
            active = dt.getTime() > Date.now();
          }
        }
        setIsSubscribed(active);
        setSubscribedUntil(expiresAt || null);
        setProStatus(active ? 'active' : expiresAt ? 'expired' : 'inactive');
      }
      if (profile?.display_name) {
        setDisplayName(profile.display_name);
      }
      if (profile?.avatar_url !== undefined) {
        setAvatarUrl(profile.avatar_url || null);
      }
      if (!profile?.display_name || !profile?.avatar_url) {
        const user = await supabaseService.getCurrentUser();
        if (!profile?.display_name) {
          const fallbackName = user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email || 'User';
          setDisplayName(fallbackName);
        }
        if (!profile?.avatar_url) {
          const fallbackAvatar = user?.user_metadata?.avatar_url || user?.user_metadata?.picture;
          if (fallbackAvatar) {
            setAvatarUrl(fallbackAvatar);
            if (user?.id) {
              try {
                await supabaseService.supabase
                  .from('profiles')
                  .update({ avatar_url: fallbackAvatar })
                  .eq('user_id', user.id);
              } catch {
                // ignore avatar persistence errors
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error fetching coins balance:', error);
    }
  }, []);

  const fetchVariants = useCallback(async () => {
    if (!session) return;
    try {
      const { data, error } = await supabaseService.supabase
        .from('variant_presets')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) {
        console.error('Error fetching variants:', error);
        return;
      }
      const mapped = (data || []).map((row: any) => ({
        id: row.id,
        name: row.name,
        options: row.options,
        createdAt: row.created_at
      })) as VariantPreset[];
      setVariants(mapped);
    } catch (error) {
      console.error('Error fetching variants:', error);
    }
  }, [session]);

  const handleSaveVariant = useCallback(async () => {
    const name = variantName.trim();
    if (!name) {
      setState(prev => ({
        ...prev,
        error: "Nama varian tidak boleh kosong."
      }));
      return;
    }
    if (!session) {
      setState(prev => ({
        ...prev,
        error: "Sesi Anda telah berakhir. Silakan login ulang."
      }));
      return;
    }
    const snapshot = JSON.parse(JSON.stringify(state.options)) as GenerationOptions;
    try {
      const { data, error } = await supabaseService.supabase
        .from('variant_presets')
        .insert({
          user_id: session.user.id,
          name,
          options: snapshot
        })
        .select('*')
        .single();
      if (error) {
        console.error('Error saving variant:', error);
        setState(prev => ({
          ...prev,
          error: "Gagal menyimpan varian. Silakan coba lagi."
        }));
        return;
      }
      if (data) {
        setVariants(prev => [
          {
            id: data.id,
            name: data.name,
            options: data.options,
            createdAt: data.created_at
          },
          ...prev
        ]);
      }
      setVariantName('');
    } catch (error) {
      console.error('Error saving variant:', error);
      setState(prev => ({
        ...prev,
        error: "Gagal menyimpan varian. Silakan coba lagi."
      }));
    }
  }, [session, state.options, variantName]);

  const handleApplyVariant = useCallback((variant: VariantPreset) => {
    setState(prev => ({
      ...prev,
      options: {
        ...prev.options,
        ...variant.options
      }
    }));
  }, []);

  const handleDeleteVariant = useCallback(async (id: string) => {
    setVariants(prev => prev.filter(variant => variant.id !== id));
    try {
      await supabaseService.supabase
        .from('variant_presets')
        .delete()
        .eq('id', id);
    } catch (error) {
      console.error('Error deleting variant:', error);
    }
  }, []);

  useEffect(() => {
    let subscription: { unsubscribe: () => void } | null = null;
    let cancelled = false;

    const initSession = async () => {
      try {
        const { data } = await supabaseService.getSession();
        if (!cancelled) {
          setSession(data?.session ?? null);
        }
      } catch (error) {
        console.error('Error getting initial session:', error);
        if (!cancelled) {
          setSession(null);
        }
      }

      try {
        subscription = {
          unsubscribe: supabaseService.subscribeToAuthChanges((_event, session) => {
            setSession(session ?? null);
            if (!session) {
              setVariants([]);
            }
          })
        };
      } catch (error) {
        console.error('Error setting up auth listener:', error);
      }
    };

    initSession();
    return () => {
      cancelled = true;
      subscription?.unsubscribe?.();
    };
  }, []);

  useEffect(() => {
    if (!session) return;
    refreshCoins();
    fetchVariants();
  }, [session, refreshCoins, fetchVariants]);

  useEffect(() => {
    if (!showCoinModal) return;
    // Poll coins while modal is open
    refreshCoins();
    const intervalId = window.setInterval(() => {
      refreshCoins();
    }, 5000);
    return () => window.clearInterval(intervalId);
  }, [showCoinModal, refreshCoins]);

  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        refreshCoins();
      }
    };
    const handleFocus = () => {
      refreshCoins();
    };
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('focus', handleFocus);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('focus', handleFocus);
    };
  }, [refreshCoins]);

  useEffect(() => {
    if (!currentInteractions.includes(state.options.interactionType)) {
      const fallback = currentInteractions.find(option => option === "Tanpa Interaksi") || currentInteractions[0];
      if (fallback) {
        updateOption('interactionType', fallback);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.options.contentType, state.options.category]);

  useEffect(() => {
    if (currentPoses.length > 0 && !currentPoses.includes(state.options.pose)) {
      updateOption('pose', currentPoses[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.options.contentType, state.options.category, state.options.interactionType]);

  // Auto-switch to "Studio" if upload background is disabled (3 images already uploaded)
  useEffect(() => {
    const currentImageCount = countUploadedImages(state);
    const isBackgroundSlotFilled = !!state.backgroundImage;
    const canUploadBackground = isBackgroundSlotFilled || currentImageCount < 3;
    
    // If background upload is disabled (red state) and current selection is "Upload Background", auto-switch to "Studio"
    if (!canUploadBackground && state.options.background === 'Upload Background') {
      updateOption('background', 'Studio');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.productImage, state.productImage2, state.productImage3, state.productImage4, state.faceImage, state.backgroundImage]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInput2Ref = useRef<HTMLInputElement>(null);
  const fileInput3Ref = useRef<HTMLInputElement>(null);
  const fileInput4Ref = useRef<HTMLInputElement>(null);
  const faceInputRef = useRef<HTMLInputElement>(null);
  const bgInputRef = useRef<HTMLInputElement>(null);
  const dashboardUploadRef = useRef<HTMLInputElement>(null);
  const trendsUploadRef = useRef<HTMLInputElement>(null);

  // Helper function to count uploaded images
  const countUploadedImages = (currentState: AppState): number => {
    let count = 0;
    if (currentState.productImage) count++;
    if (currentState.productImage2) count++;
    if (currentState.productImage3) count++;
    if (currentState.productImage4) count++;
    if (currentState.faceImage) count++;
    if (currentState.backgroundImage) count++;
    return count;
  };

  // Helper function to check if a specific image slot is already filled
  const isImageSlotFilled = (type: 'product' | 'product2' | 'product3' | 'product4' | 'face' | 'background', currentState: AppState): boolean => {
    switch (type) {
      case 'product': return !!currentState.productImage;
      case 'product2': return !!currentState.productImage2;
      case 'product3': return !!currentState.productImage3;
      case 'product4': return !!currentState.productImage4;
      case 'face': return !!currentState.faceImage;
      case 'background': return !!currentState.backgroundImage;
      default: return false;
    }
  };

  const handleDeleteImage = (type: 'product' | 'product2' | 'product3' | 'product4' | 'face' | 'background') => {
    const stateKey = type === 'product' ? 'productImage' : 
                     type === 'product2' ? 'productImage2' : 
                     type === 'product3' ? 'productImage3' : 
                     type === 'product4' ? 'productImage4' : 
                     type === 'face' ? 'faceImage' : 'backgroundImage';
    
    setState(prev => ({
      ...prev,
      [stateKey]: null,
      error: null // Clear error on delete
    }));
    
    // Reset file input
    const inputRef = type === 'product' ? fileInputRef :
                     type === 'product2' ? fileInput2Ref :
                     type === 'product3' ? fileInput3Ref :
                     type === 'product4' ? fileInput4Ref :
                     type === 'face' ? faceInputRef : bgInputRef;
    
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'product' | 'product2' | 'product3' | 'product4' | 'face' | 'background') => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if this slot is already filled (replacing existing image is allowed)
    const isReplacing = isImageSlotFilled(type, state);
    
    // Count current uploaded images (excluding the one being replaced)
    const currentImageCount = countUploadedImages(state);
    const effectiveCount = isReplacing ? currentImageCount : currentImageCount + 1;

    // Validate: Maximum 3 images allowed
    if (effectiveCount > 3) {
      setState(prev => ({ 
        ...prev, 
        error: "Maksimal 3 upload gambar. Silakan hapus salah satu gambar terlebih dahulu." 
      }));
      // Reset file input
      e.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      const imageData: ImageData = {
        base64: (reader.result as string).split(',')[1],
        mimeType: file.type
      };
      const stateKey = type === 'product' ? 'productImage' : 
                       type === 'product2' ? 'productImage2' : 
                       type === 'product3' ? 'productImage3' : 
                       type === 'product4' ? 'productImage4' : 
                       type === 'face' ? 'faceImage' : 'backgroundImage';
      setState(prev => ({
        ...prev,
        [stateKey]: imageData,
        error: null // Clear error on successful upload
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    if (!state.productImage && !state.productImage2 && !state.productImage3 && !state.productImage4) {
      setState(prev => ({ ...prev, error: "Upload setidaknya satu produk untuk memulai." }));
      return;
    }
    if (coins < IMAGE_BATCH_COINS) {
      setState(prev => ({
        ...prev,
        error: getMissingCoinsMessage(IMAGE_BATCH_COINS, coins)
      }));
      return;
    }

    setState(prev => ({ ...prev, isGenerating: true, error: null }));
    
    try {
      // Collect all product images
      const productImages: string[] = [
        state.productImage ? `data:${state.productImage.mimeType};base64,${state.productImage.base64}` : null,
        state.productImage2 ? `data:${state.productImage2.mimeType};base64,${state.productImage2.base64}` : null,
        state.productImage3 ? `data:${state.productImage3.mimeType};base64,${state.productImage3.base64}` : null,
        state.productImage4 ? `data:${state.productImage4.mimeType};base64,${state.productImage4.base64}` : null,
      ].filter(Boolean) as string[];
      
      // Get face image if uploaded
      const faceImage = state.faceImage 
        ? `data:${state.faceImage.mimeType};base64,${state.faceImage.base64}`
        : undefined;
      
      // Get background image if uploaded
      const backgroundImage = state.backgroundImage
        ? `data:${state.backgroundImage.mimeType};base64,${state.backgroundImage.base64}`
        : undefined;
      
      // Generate 1 image using Fal.ai dengan semua images yang diupload
      // Prompt akan di-generate otomatis dari options di dalam generateImagesWithFal
      // Urutan gambar: [Produk1, Produk2, Wajah, Background]
      const imageUrls = await generateImagesWithFal(
        undefined, // Prompt akan di-generate dari options
        1, 
        productImages.length > 0 ? productImages : undefined,
        faceImage,
        backgroundImage,
        state.options, // Pass options untuk prompt generation
        undefined,
        identityMode
      );
      
      // Convert image URLs to GenerationResult format
      const newResults = imageUrls.map((url, i) => ({
        url: url,
        promptA: `GROK VIDEO PROMPT (6 SECONDS) — VERSION A\nA high-resolution video showing the product in this setting, with subtle natural movement and realistic lighting effects. Variation ${i + 1}.`,
        promptB: `GROK VIDEO PROMPT (6 SECONDS) — VERSION B\nA cinematic video of the product, with smooth camera movement and professional lighting. Variation ${i + 1}.`
      }));
      
      setState(prev => ({
        ...prev,
        results: [...newResults, ...prev.results],
        isGenerating: false,
        videoResults: {},
        klingVideoResults: {},
        klingSelectedImages: {},
        videoBatches: {},
        isVideoGenerating: {},
        isKlingVideoGenerating: {},
        isVideoBatchGenerating: {}
      }));
      await refreshCoins();
      
      // Auto-generate 3 videos for each generated image based on category
      if (state.options.category) {
        for (let i = 0; i < newResults.length; i++) {
          generateVideoBatch(i, newResults[i].url, state.options.category);
        }
      }
    } catch (err: any) {
      console.error('Error in handleGenerate:', err);
      const errorMessage = toSafeErrorMessage(err, "Gagal memproses gambar. Silakan coba lagi.");
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isGenerating: false
      }));
    }
  };

  const handleGenerateVideo = async (imageIndex: number, imageUrl: string) => {
    try {
      // Set loading state
      setState(prev => ({
        ...prev,
        isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: true }
      }));

      // Get auth token
      const { data: { session } } = await supabaseService.getSession();
      if (!session?.access_token) {
        throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
      }

      // Create video using new video service
      const result = await createVideoFromImage(
        imageUrl,
        "Check This Out!",
        "Shop Now",
        session.access_token
      );

      // Update state with video URL
      setState(prev => ({
        ...prev,
        videoResults: { ...prev.videoResults, [imageIndex]: result.video_url },
        isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: false }
      }));
    } catch (error: any) {
      console.error('Error creating video:', error);
      setState(prev => ({
        ...prev,
        isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: false },
        error: toSafeErrorMessage(error, "Gagal membuat video. Silakan coba lagi.")
      }));
    }
  };

  const handleSelectKlingImage = (imageIndex: number, file?: File) => {
    if (!file) {
      return;
    }
    if (!file.type.startsWith('image/')) {
      setState(prev => ({
        ...prev,
        error: 'File harus berupa gambar.'
      }));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      if (!result) {
        return;
      }
      setState(prev => ({
        ...prev,
        klingSelectedImages: { ...prev.klingSelectedImages, [imageIndex]: result }
      }));
    };
    reader.readAsDataURL(file);
  };

  const generateVideoBatch = async (imageIndex: number, imageUrl: string, category: string) => {
    try {
      // Set loading state
      setState(prev => ({
        ...prev,
        isVideoBatchGenerating: { ...prev.isVideoBatchGenerating, [imageIndex]: true }
      }));

      // Get auth token
      const { data: { session } } = await supabaseService.getSession();
      if (!session?.access_token) {
        throw new Error('Sesi kamu telah berakhir. Silakan login ulang.');
      }

      // Create 3 videos using batch service
      const result = await createVideoBatchFromImage(
        imageUrl,
        category,
        session.access_token
      );
      if (typeof result.remaining_coins === 'number') {
        setCoins(result.remaining_coins);
      }

      // Extract video URLs - ensure we get all videos
      console.log('📹 Video batch response:', result);
      console.log('📹 Total videos received:', result.videos?.length || 0);
      console.log('📹 Videos array:', result.videos);
      
      // Extract all video URLs from response
      const videoUrls = (result.videos || []).map((v: any) => v.video_url).filter((url: string) => url);
      console.log('📹 Extracted video URLs:', videoUrls);
      console.log('📹 Number of video URLs extracted:', videoUrls.length);
      
      if (videoUrls.length === 0) {
        console.error('⚠️ No video URLs extracted from response!');
        throw new Error('Tidak ada video yang dihasilkan. Silakan coba lagi.');
      }
      
      if (videoUrls.length < 3) {
        console.warn(`⚠️ Only ${videoUrls.length}/3 videos received from backend`);
      }

      // Update state with video batch
      setState(prev => {
        const newVideoBatches = { ...prev.videoBatches, [imageIndex]: videoUrls };
        console.log('📹 Updated videoBatches state:', newVideoBatches);
        console.log(`📹 videoBatches[${imageIndex}]:`, newVideoBatches[imageIndex]);
        console.log(`📹 videoBatches[${imageIndex}] length:`, newVideoBatches[imageIndex]?.length);
        return {
          ...prev,
          videoBatches: newVideoBatches,
          isVideoBatchGenerating: { ...prev.isVideoBatchGenerating, [imageIndex]: false }
        };
      });
    } catch (error: any) {
      console.error('Error creating video batch:', error);
      setState(prev => ({
        ...prev,
        isVideoBatchGenerating: { ...prev.isVideoBatchGenerating, [imageIndex]: false },
        error: toSafeErrorMessage(error, "Gagal membuat video. Silakan coba lagi.")
      }));
    }
  };

  const buildKlingPrompt = (options: GenerationOptions) => {
    const contentType = options.contentType || 'Non Model';
    const category = options.category || 'Produk';
    const pose = options.pose || 'Natural';
    const interaction = options.interactionType || 'Tanpa Interaksi';
    const camera = options.cameraAngle || 'Front';
    const background = options.background || 'Studio';
    const aspect = options.aspectRatio || '9:16';
    const categoryKey = category.toLowerCase();
    const poseKey = pose.toLowerCase();
    const isFootwear = /sepatu|sendal|shoe|footwear/.test(categoryKey);
    const isFashion = /fashion|apparel|outfit|dress|pakaian/.test(categoryKey);
    const isBeauty = /beauty|skincare|makeup|cosmetic/.test(categoryKey);
    const isAccessory = /aksesori|accessor|bag|tas|jam|watch/.test(categoryKey);
    const isFlatLay = /flat|top view|flatlay|flat lay/.test(poseKey);

    let phase1 = 'pan halus dari kiri ke kanan';
    let phase2 = 'zoom-in lembut ke produk';
    let transition = 'Transisi cepat namun smooth (tanpa patah)';

    if (isFootwear) {
      phase1 = 'tilt-down lembut fokus ke detail produk';
      phase2 = 'zoom-in mikro ke tekstur dan bentuk';
    } else if (isBeauty) {
      phase1 = 'push-in perlahan ke area label';
      phase2 = 'slow orbit kecil untuk menonjolkan kilau';
    } else if (isAccessory) {
      phase1 = 'pan mikro mengikuti kontur produk';
      phase2 = 'zoom-in halus pada detail utama';
    } else if (isFashion) {
      phase1 = 'push-in perlahan dari medium ke close-up';
      phase2 = 'pan vertikal halus mengikuti siluet';
    }

    if (isFlatLay) {
      phase1 = 'pan horizontal mikro di atas produk (flat lay)';
      phase2 = 'zoom-in lembut ke center';
    }

    if (interaction.toLowerCase().includes('tanpa')) {
      transition = 'Transisi cepat namun smooth, tanpa perubahan arah mendadak';
    }

    const isHandInteraction = /tangan/i.test(interaction.toLowerCase());
    const isTwoHandInteraction = /Pegang\s*2/i.test(interaction);
    const prompt = [
      `Pro Video prompt:`,
      `Tipe Konten: ${contentType}`,
      `Kategori Produk: ${category}`,
      `Pose Pilihan: ${pose}`,
      `Interaksi: ${interaction}`,
      `Kamera: ${camera}`,
      `Background: ${background}`,
      `Aspect Ratio: ${aspect}`,
      isFootwear
        ? isHandInteraction
          ? isTwoHandInteraction
            ? [
                `Professional e-commerce video, hands symmetrically reaching from bottom corners.`,
                `Gently cradling with both hands, subtle and slow upward lift, long sleeves covering both wrists.`,
                `0-2 detik: fokus pada impresi pertama (estetika tangan dan sweater yang hangat).`,
                `2-5 detik: fokus pada fungsionalitas produk (tekstur sandal dan kemewahan material saat digerakkan perlahan).`,
                `Balanced grip, both hands visible, no jitter, soft golden hour lighting, 5 seconds.`
              ].join(' ')
            : [
                `Professional e-commerce video, start with a single hand holding one sandal as per reference image.`,
                `The hand slowly rotates or tilts to reveal the second matching sandal tucked behind the first one.`,
                `Camera zooms out slightly, revealing a perfect matching pair, consistent product design.`,
                `Soft golden hour lighting, subtle hand movement, use "reveal" not "appear", 5 seconds.`
              ].join(' ')
          : [
              `Mode: The Action to Static Detail.`,
              `Detik 0-2 (The Action): kamera low angle, model melakukan gerakan kecil (melangkah pelan atau memutar pergelangan kaki).`,
              `Detik 2-5 (The Static Detail): gerakan berhenti, kamera slow panning mengelilingi sepatu yang diam, dari samping ke depan.`,
              `Tujuan: menonjolkan bentuk sepatu dari berbagai sudut tanpa mengganggu fokus produk.`,
              `Gerakan sangat stabil, no jitter, no scale shift, lighting natural, detail tajam, warna akurat.`
            ].join(' ')
        : [
            `Buat video sinematik 5 detik dengan 2 fase gerakan.`,
            `Fase 1 (0-2.5s): ${phase1}.`,
            `Fase 2 (2.5-5s): ${phase2}.`,
            `${transition}, produk tetap jelas, lighting natural, detail tekstur tajam, depth of field halus, warna akurat, no jitter.`,
            `Aesthetic lifestyle vibe, golden hour glow, clean soft look, gentle shadows, premium minimalist background.`
          ].join(' ')
    ].join(' | ');

    const negativePrompt = [
      'harsh shadows',
      'overexposed',
      'underexposed',
      'neon lighting',
      'hdr look',
      'oversaturated',
      'low quality',
      'blurry',
      'noisy',
      'grain',
      'text',
      'watermark',
      'logo',
      'glitch',
      'distorted',
      'warped',
      'jitter',
      'shaky camera',
      'cut-off product',
      'duplicate object',
      'extra limbs',
      'bad anatomy',
      'face morphing',
      'facial distortion',
      'blinking eyes',
      'eye asymmetry',
      'distorted mouth',
      'unstable facial features',
      'changing identity',
      'losing likeness',
      'melting face',
      'creepy smile',
      'double face',
      'extra eyes',
      'cartoon',
      'anime',
      '3d render',
      'cgi'
    ].join(', ');

    return { prompt, negativePrompt };
  };

  const handleGenerateKlingVideo = async (imageIndex: number, imageUrl: string) => {
    try {
      if (coins < PRO_VIDEO_COINS) {
        setState(prev => ({
          ...prev,
          error: getMissingCoinsMessage(PRO_VIDEO_COINS, coins)
        }));
        return;
      }
      setState(prev => ({
        ...prev,
        isKlingVideoGenerating: { ...prev.isKlingVideoGenerating, [imageIndex]: true }
      }));

      const { data: { session } } = await supabaseService.getSession();
      if (!session?.access_token) {
        throw new Error('Sesi Anda telah berakhir. Silakan login ulang.');
      }

      const klingPrompt = buildKlingPrompt(state.options);
      const result = await createKlingVideoFromImage(
        imageUrl,
        session.access_token,
        klingPrompt.prompt,
        klingPrompt.negativePrompt
      );

      setState(prev => ({
        ...prev,
        klingVideoResults: { ...prev.klingVideoResults, [imageIndex]: result.video_url },
        isKlingVideoGenerating: { ...prev.isKlingVideoGenerating, [imageIndex]: false }
      }));
      if (typeof result.remaining_coins === 'number') {
        setCoins(result.remaining_coins);
      } else {
        setCoins(prev => Math.max(0, prev - PRO_VIDEO_COINS));
      }
    } catch (error: any) {
      console.error('Error creating Pro video:', error);
      setState(prev => ({
        ...prev,
        isKlingVideoGenerating: { ...prev.isKlingVideoGenerating, [imageIndex]: false },
        error: toSafeErrorMessage(error, "Gagal membuat video. Silakan coba lagi.")
      }));
    }
  };

  // Legacy handleGenerateVideo for backward compatibility (if using window.aistudio)
  const handleGenerateVideoLegacy = async (imageIndex: number, base64Image: string) => {
    if (window.aistudio) {
      const hasKey = await window.aistudio.hasSelectedApiKey();
      if (!hasKey) {
        await window.aistudio.openSelectKey();
      }
    }

    setState(prev => ({
      ...prev,
      isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: true },
      error: null
    }));

    try {
      const videoUrl = await generateProductVideo(base64Image, state.options);
      setState(prev => ({
        ...prev,
        videoResults: { ...prev.videoResults, [imageIndex]: videoUrl },
        isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: false }
      }));
    } catch (err: any) {
      const rawMessage = typeof err?.message === 'string' ? err.message : '';
      let errorMsg = toSafeErrorMessage(err, "Gagal membuat video.");
      if (rawMessage.includes("Requested entity was not found") && window.aistudio) {
        await window.aistudio.openSelectKey();
      }
      setState(prev => ({
        ...prev,
        error: errorMsg,
        isVideoGenerating: { ...prev.isVideoGenerating, [imageIndex]: false }
      }));
    }
  };

  const updateOption = (key: keyof GenerationOptions, value: string) => {
    setState(prev => ({
      ...prev,
      options: { ...prev.options, [key]: value }
    }));
  };

  const handleLogout = async () => {
    try {
      localStorage.removeItem('auth_error');
    } catch {
      // ignore
    }
    await supabaseService.signOut();
    router.replace(ROUTES.login);
  };

  const handleTopUp = () => {
    // Navigate to top-up page
    router.replace(ROUTES.topup);
  };

  const getMissingCoinsMessage = (requiredCoins: number, currentCoins: number) => {
    const missing = Math.max(requiredCoins - currentCoins, 0);
    return `Coins kamu tidak cukup (kurang ${missing} coins). Top Up`;
  };

  const getDownloadTimestamp = () => {
    const now = new Date();
    const pad = (value: number) => value.toString().padStart(2, '0');
    const yyyy = now.getFullYear();
    const mm = pad(now.getMonth() + 1);
    const dd = pad(now.getDate());
    const hh = pad(now.getHours());
    const min = pad(now.getMinutes());
    const ss = pad(now.getSeconds());
    return `${yyyy}${mm}${dd}-${hh}${min}${ss}`;
  };

  const handleDashboard = () => {
    router.push('/app/dashboard');
  };

  const handleBackToStudio = () => {
    router.push('/app');
  };

  const fetchDashboard = useCallback(async () => {
    try {
      setDashboardLoading(true);
      setDashboardError(null);
      setDashboardErrorNeedsTopUp(false);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi Anda telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/autopost/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Gagal memuat dashboard (${response.status})`);
      }
      const data = await response.json();
      const items = Array.isArray(data?.items) ? data.items : [];
      const mapped: AutopostDashboardItem[] = items.map((item: any) => ({
        id: item.id,
        video_name: item.video_name || item.file_name || 'video',
        status: item.status || 'UNKNOWN',
        title: item.title || null,
        hook_text: item.hook_text || null,
        cta_text: item.cta_text || null,
        hashtags: item.hashtags || null,
        score: typeof item.score === 'number' ? item.score : null,
        score_reasons: Array.isArray(item.score_reasons) ? item.score_reasons : null,
        next_check_at: item.next_check_at || null,
        scheduled_at: item.scheduled_at || null,
        status_note: item.status_note || null,
        title_source: item.title_source || null,
        hook_source: item.hook_source || null,
        cta_source: item.cta_source || null,
        hashtags_source: item.hashtags_source || null,
        credit_used: typeof item.credit_used === 'number' ? item.credit_used : 0,
        score_details: item.score_details || null
      }));
      setDashboardItems(mapped);
    } catch (error: any) {
      setDashboardError('Gagal memuat dashboard. Silakan coba lagi.');
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  const fetchAdminLogs = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setAdminLogsLoading(true);
      setAdminLogsError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setAdminLogsError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/admin/autopost/logs?limit=50`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Gagal memuat log admin (${response.status})`);
      }
      const data = await response.json();
      const items = Array.isArray(data?.items) ? data.items : [];
      const mapped: AdminAutopostLog[] = items.map((item: any) => ({
        id: item.id,
        user_id: item.user_id,
        video_name: item.video_name || item.file_name || 'video',
        status: item.status || 'UNKNOWN',
        score: typeof item.score === 'number' ? item.score : null,
        created_at: item.created_at || null,
        views: typeof item.views === 'number' ? item.views : null,
        likes: typeof item.likes === 'number' ? item.likes : null,
        comments: typeof item.comments === 'number' ? item.comments : null,
        shares: typeof item.shares === 'number' ? item.shares : null
      }));
      setAdminLogs(mapped);
    } catch (error: any) {
      setAdminLogsError('Gagal memuat log admin. Silakan coba lagi.');
    } finally {
      setAdminLogsLoading(false);
    }
  }, [isAdmin]);

  const fetchFeedbackWeights = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setFeedbackWeightsLoading(true);
      setFeedbackWeightsError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setFeedbackWeightsError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const params = new URLSearchParams();
      if (feedbackWeightsQuery.trim()) {
        if (feedbackWeightsQuery.includes('@')) {
          params.set('email', feedbackWeightsQuery.trim());
        } else {
          params.set('user_id', feedbackWeightsQuery.trim());
        }
      }
      const response = await fetch(`${API_URL}/api/admin/autopost/feedback-weights?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Gagal memuat feedback weights (${response.status})`);
      }
      const data = await response.json();
      setFeedbackWeights(data);
    } catch (error: any) {
      setFeedbackWeightsError('Gagal memuat feedback weights.');
    } finally {
      setFeedbackWeightsLoading(false);
    }
  }, [isAdmin, feedbackWeightsQuery]);

  const fetchSubscriptionInfo = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setSubscriptionLoading(true);
      setSubscriptionError(null);
      setSubscriptionStatus(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setSubscriptionError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const params = new URLSearchParams();
      if (subscriptionQuery.trim()) {
        if (subscriptionQuery.includes('@')) {
          params.set('email', subscriptionQuery.trim());
        } else {
          params.set('user_id', subscriptionQuery.trim());
        }
      }
      const response = await fetch(`${API_URL}/api/admin/subscription/lookup?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Gagal memuat subscription (${response.status})`);
      }
      const data = await response.json();
      setSubscriptionInfo(data);
      setSubscriptionStatus('Status user berhasil dimuat.');
    } catch (error: any) {
      setSubscriptionError('Gagal memuat subscription user.');
    } finally {
      setSubscriptionLoading(false);
    }
  }, [isAdmin, subscriptionQuery]);

  const updateSubscription = useCallback(async (payload: Record<string, any>) => {
    if (!isAdmin) return;
    try {
      setSubscriptionLoading(true);
      setSubscriptionError(null);
      setSubscriptionStatus(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setSubscriptionError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/admin/subscription/update`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        throw new Error('Gagal update subscription.');
      }
      const data = await response.json();
      setSubscriptionInfo(data);
      setSubscriptionStatus('Perubahan berhasil disimpan.');
    } catch (error: any) {
      setSubscriptionError('Gagal update subscription.');
    } finally {
      setSubscriptionLoading(false);
    }
  }, [isAdmin]);

  const fetchAdminAuditLogs = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setAdminAuditLoading(true);
      setAdminAuditError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setAdminAuditError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const params = new URLSearchParams({ limit: '100' });
      if (adminAuditActor.trim()) params.set('actor', adminAuditActor.trim());
      if (adminAuditTarget.trim()) params.set('target', adminAuditTarget.trim());
      if (adminAuditAction !== 'ALL') params.set('action', adminAuditAction);
      const response = await fetch(`${API_URL}/api/admin/audit-logs?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Gagal memuat audit log.');
      }
      const data = await response.json();
      const items = Array.isArray(data?.items) ? data.items : [];
      const mapped: AdminAuditLog[] = items.map((item: any) => ({
        id: item.id,
        actor_user_id: item.actor_user_id,
        actor_email: item.actor_email,
        action: item.action,
        target_user_id: item.target_user_id,
        details: item.details || null,
        created_at: item.created_at || null
      }));
      setAdminAuditLogs(mapped);
    } catch (error: any) {
      setAdminAuditError('Gagal memuat audit log.');
    } finally {
      setAdminAuditLoading(false);
    }
  }, [isAdmin, adminAuditActor, adminAuditTarget, adminAuditAction]);

  const fetchMidtransStatus = useCallback(async () => {
    if (!isAdmin) return;
    try {
      setMidtransStatusLoading(true);
      setMidtransStatusError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setMidtransStatusError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/admin/midtrans/status`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Gagal memuat status Midtrans (${response.status})`);
      }
      const data = await response.json();
      setMidtransStatus(data);
    } catch (error: any) {
      setMidtransStatusError('Gagal memuat status Midtrans.');
    } finally {
      setMidtransStatusLoading(false);
    }
  }, [isAdmin]);

  const filteredAdminLogs = useMemo(() => {
    const statusFilter = adminLogsStatus.trim().toUpperCase();
    const userFilter = adminLogsUserQuery.trim().toLowerCase();
    const fromDate = adminLogsDateFrom ? new Date(adminLogsDateFrom) : null;
    const toDate = adminLogsDateTo ? new Date(`${adminLogsDateTo}T23:59:59`) : null;
    const filtered = adminLogs.filter((row) => {
      if (statusFilter !== 'ALL' && row.status !== statusFilter) {
        return false;
      }
      if (userFilter && !row.user_id.toLowerCase().includes(userFilter)) {
        return false;
      }
      if ((fromDate || toDate) && row.created_at) {
        const createdAt = new Date(row.created_at);
        if (fromDate && createdAt < fromDate) {
          return false;
        }
        if (toDate && createdAt > toDate) {
          return false;
        }
      }
      return true;
    });
    return filtered.slice(0, adminLogsLimit);
  }, [adminLogs, adminLogsStatus, adminLogsUserQuery, adminLogsDateFrom, adminLogsDateTo, adminLogsLimit]);

  const handleDashboardRecheck = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/autopost/recheck`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Gagal melakukan recheck.');
      }
      await fetchDashboard();
    } catch (error: any) {
      setDashboardError('Gagal melakukan recheck. Silakan coba lagi.');
    }
  }, [fetchDashboard, refreshCoins]);

  const handleDashboardRetry = useCallback(async (id: number) => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/autopost/tasks/${id}/retry`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Gagal retry video.');
      }
      await fetchDashboard();
    } catch (error: any) {
      setDashboardError('Gagal retry video. Silakan coba lagi.');
    }
  }, [fetchDashboard]);

  const handleDashboardRegenerate = useCallback(async (id: number) => {
    try {
      setDashboardRegeneratingId(id);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/autopost/${id}/generate`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (handleTrialExpired(errorData)) {
          return;
        }
        throw new Error('Gagal regenerate metadata.');
      }
      await fetchDashboard();
      refreshCoins();
    } catch (error: any) {
      setDashboardError('Gagal regenerate metadata. Silakan coba lagi.');
    } finally {
      setDashboardRegeneratingId(null);
    }
  }, [fetchDashboard]);

  const handleDashboardUploadClick = () => {
    dashboardUploadRef.current?.click();
  };

  const handleDashboardUploadChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setDashboardLoading(true);
      setDashboardError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setDashboardError('Sesi kamu telah berakhir. Silakan login ulang.');
        return;
      }

      const title = window.prompt('Judul video (opsional):') || '';
      const caption = window.prompt('Caption (opsional):') || '';
      const hookText = window.prompt('Hook (opsional):') || '';
      const ctaText = window.prompt('CTA (opsional):') || '';
      const hashtags = window.prompt('Hashtags (opsional, pisahkan spasi):') || '';

      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('caption', caption);
      formData.append('hook_text', hookText);
      formData.append('cta_text', ctaText);
      formData.append('hashtags', hashtags);
      formData.append('category', state.options.category);

      const response = await fetch(`${API_URL}/api/autopost/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (handleTrialExpired(errorData)) {
          return;
        }
        if (response.status === 403) {
          const detail = errorData.detail;
          const requiredCoins =
            detail && typeof detail === 'object' && typeof detail.required_coins === 'number'
              ? detail.required_coins
              : null;
          setDashboardError(
            requiredCoins !== null
              ? getMissingCoinsMessage(requiredCoins, coins)
              : 'Coins kamu tidak cukup. Top Up'
          );
          setDashboardErrorNeedsTopUp(true);
          return;
        }
        throw new Error(`Gagal upload video (${response.status})`);
      }

      const data = await response.json();
      if (typeof data?.remaining_coins === 'number') {
        setCoins(data.remaining_coins);
      }
      await fetchDashboard();
      refreshCoins();
    } catch (error: any) {
      setDashboardError('Gagal upload video. Silakan coba lagi.');
      setDashboardErrorNeedsTopUp(false);
    } finally {
      setDashboardLoading(false);
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const fetchTrendsPreview = useCallback(async () => {
    try {
      setTrendsLoading(true);
      setTrendsMessage(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setTrendsMessage('Sesi Anda telah berakhir. Silakan login ulang.');
        return;
      }
      const params = new URLSearchParams({
        search: trendsSearch,
        page: String(trendsPage),
        page_size: String(trendsPageSize),
        category: trendsCategory
      });
      const response = await fetch(`${API_URL}/api/admin/trends?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (response.status === 403) {
        setTrendsMessage('Admin only.');
        return;
      }
      if (!response.ok) {
        throw new Error('Gagal memuat trend.');
      }
      const data = await response.json();
      setTrendsPreview(data);
    } catch (error: any) {
      setTrendsMessage('Gagal memuat trend. Silakan coba lagi.');
    } finally {
      setTrendsLoading(false);
    }
  }, [trendsSearch, trendsPage, trendsPageSize, trendsCategory]);

  const fetchAdminStatus = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/admin/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const data = await response.json();
      setIsAdmin(!!data?.is_admin);
    } catch {
      setIsAdmin(false);
    }
  }, []);

  const fetchImportStatus = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/admin/trends/import-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const data = await response.json();
      setImportStatus({
        status: data?.status || 'idle',
        processed: data?.processed || 0,
        total: data?.total || 0,
        valid: data?.valid || 0,
        invalid: data?.invalid || 0
      });
      setImportErrors(Array.isArray(data?.errors) ? data.errors : []);
    } catch {
      // ignore
    }
  }, []);

  const fetchTrendCategories = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/admin/trends/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const data = await response.json();
      if (Array.isArray(data?.categories)) {
        setCategoryOptions(data.categories);
      }
      if (typeof data?.hashtag_regex === 'string') {
        setHashtagRegex(data.hashtag_regex);
      }
    } catch {
      setCategoryOptions([]);
    }
  }, []);

  const fetchTemplates = useCallback(async () => {
    try {
      setTemplatesLoading(true);
      setTemplatesError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const params = new URLSearchParams({ category: state.options.category });
      const response = await fetch(`${API_URL}/api/autopost/templates?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Gagal memuat template.');
      }
      const data = await response.json();
      setTemplates({
        hooks: Array.isArray(data?.hooks) ? data.hooks : [],
        ctas: Array.isArray(data?.ctas) ? data.ctas : [],
        captions: Array.isArray(data?.captions) ? data.captions : [],
        hashtags: Array.isArray(data?.hashtags) ? data.hashtags : []
      });
    } catch (error: any) {
      setTemplatesError('Gagal memuat template. Silakan coba lagi.');
    } finally {
      setTemplatesLoading(false);
    }
  }, [state.options.category]);

  const fetchInsights = useCallback(async () => {
    try {
      setInsightsLoading(true);
      setInsightsError(null);
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/autopost/insights`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Gagal memuat insights.');
      }
      const data = await response.json();
      setInsights(data);
    } catch (error: any) {
      setInsightsError('Gagal memuat insights. Silakan coba lagi.');
    } finally {
      setInsightsLoading(false);
    }
  }, []);

  const handleMetricsUploadClick = () => {
    metricsUploadRef.current?.click();
  };

  const handleMetricsUploadChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setMetricsUploadResult({ status: 'idle', message: null });
    setMetricsUploading(true);

    try {
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setMetricsUploadResult({
          status: 'error',
          message: 'Sesi Anda telah berakhir. Silakan login ulang.'
        });
        return;
      }

      const text = await file.text();
      const trimmed = text.trim();
      let payload: Record<string, any> = {};

      const looksJson = file.name.toLowerCase().endsWith('.json') || trimmed.startsWith('{') || trimmed.startsWith('[');
      if (looksJson) {
        try {
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed)) {
            throw new Error('JSON harus berupa object, bukan array.');
          }
          payload = parsed || {};
        } catch (error) {
          setMetricsUploadResult({
            status: 'error',
            message: 'Format JSON tidak valid.'
          });
          return;
        }
        if (!payload.video_id && metricsVideoId.trim()) {
          payload.video_id = metricsVideoId.trim();
        }
        if (!payload.video_id) {
          setMetricsUploadResult({
            status: 'error',
            message: 'video_id wajib diisi (di file JSON atau input Video ID).'
          });
          return;
        }
      } else {
        if (!/video[_ ]?id/i.test(text) && !metricsVideoId.trim()) {
          setMetricsUploadResult({
            status: 'error',
            message: 'TXT harus berisi video_id atau isi input Video ID.'
          });
          return;
        }
        const rawText = metricsVideoId.trim()
          ? `${text}\nvideo_id: ${metricsVideoId.trim()}`
          : text;
        payload = { raw_text: rawText };
      }

      const response = await fetch(`${API_URL}/api/autopost/metrics`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (handleTrialExpired(errorData)) {
          setMetricsUploadResult({
            status: 'error',
            message: 'Trial kamu sudah habis. Upgrade ke Pro untuk melanjutkan.'
          });
          return;
        }
        setMetricsUploadResult({
          status: 'error',
          message: 'Gagal mengupload data metrics. Periksa format file.'
        });
        return;
      }

      setMetricsUploadResult({
        status: 'success',
        message: 'Data metrics berhasil diupload dan dianalisis.'
      });
      fetchInsights();
    } catch {
      setMetricsUploadResult({
        status: 'error',
        message: 'Gagal memproses file metrics.'
      });
    } finally {
      setMetricsUploading(false);
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const fetchCompetitors = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/autopost/competitors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const data = await response.json();
      setCompetitors(Array.isArray(data?.items) ? data.items : []);
    } catch {
      setCompetitors([]);
    }
  }, []);

  const handleAddCompetitor = async () => {
    const title = window.prompt('Judul kompetitor (wajib):') || '';
    if (!title.trim()) return;
    const url = window.prompt('URL (opsional):') || '';
    const notes = window.prompt('Catatan (opsional):') || '';
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/autopost/competitors`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, url, notes })
      });
      if (!response.ok) return;
      await fetchCompetitors();
    } catch {
      // ignore
    }
  };

  const handleDownloadTemplate = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const response = await fetch(`${API_URL}/api/admin/trends/template`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) return;
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'trends_template.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // ignore
    }
  }, []);

  const handleDownloadAllTrends = useCallback(async () => {
    try {
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setTrendsMessage('Sesi Anda telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/admin/trends/export`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.status === 403) {
        setTrendsMessage('Admin only.');
        return;
      }
      if (!response.ok) {
        throw new Error('Gagal mengunduh data.');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'trends_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setTrendsMessage('Gagal mengunduh data.');
    }
  }, []);

  const handleCopyErrors = () => {
    if (importErrors.length === 0) return;
    navigator.clipboard.writeText(importErrors.join('\n'));
  };

  const handleExportErrorsCsv = () => {
    if (importErrors.length === 0) return;
    const rows = importErrors.map((err) => {
      const match = err.match(/Row\s+(\d+)/i);
      const row = match ? match[1] : '';
      const message = err.replace(/"/g, '""');
      return `"${row}","${message}"`;
    });
    const csv = ['row,error', ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'trend_import_errors.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleCopyTemplate = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleTrendsUploadClick = () => {
    trendsUploadRef.current?.click();
  };

  const handleTrendsUploadChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setTrendsLoading(true);
      setTrendsMessage(null);
      setImportStatus({ status: 'running', processed: 0, total: 0, valid: 0, invalid: 0 });
      setImportErrors([]);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setTrendsMessage('Sesi Anda telah berakhir. Silakan login ulang.');
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${API_URL}/api/admin/trends/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });
      if (response.status === 403) {
        setTrendsMessage('Admin only.');
        return;
      }
      if (!response.ok) {
        try {
          const errorData = await response.json();
          console.error('CSV upload error detail:', errorData);
        } catch {
          // ignore
        }
        throw new Error('Gagal upload CSV.');
      }
      await fetchTrendsPreview();
      setTrendsMessage('CSV trend berhasil diupload.');
      if (autoRetryImport && importStatus?.status === 'failed') {
        await fetchTrendsPreview();
      }
    } catch (error: any) {
      setTrendsMessage('Gagal upload CSV. Silakan coba lagi.');
      if (importErrorRef.current) {
        importErrorRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } finally {
      setTrendsLoading(false);
      if (event.target) {
        event.target.value = '';
      }
    }
  };

  const handleTrendsRefresh = useCallback(async () => {
    try {
      setTrendsLoading(true);
      setTrendsMessage(null);
      const token = await supabaseService.getAccessToken();
      if (!token) {
        setTrendsMessage('Sesi Anda telah berakhir. Silakan login ulang.');
        return;
      }
      const response = await fetch(`${API_URL}/api/admin/trends/refresh`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (response.status === 403) {
        setTrendsMessage('Admin only.');
        return;
      }
      if (!response.ok) {
        throw new Error('Gagal refresh trend.');
      }
      await fetchTrendsPreview();
      setTrendsMessage('Trend berhasil direfresh.');
    } catch (error: any) {
      setTrendsMessage('Gagal refresh trend. Silakan coba lagi.');
    } finally {
      setTrendsLoading(false);
    }
  }, [fetchTrendsPreview]);

  useEffect(() => {
    if (!showDashboard) return;
    fetchDashboard();
    fetchTrendsPreview();
    fetchAdminStatus();
    fetchImportStatus();
    fetchTrendCategories();
    fetchTemplates();
    fetchInsights();
    fetchCompetitors();
    const intervalId = window.setInterval(() => {
      fetchDashboard();
    }, 20000);
    return () => window.clearInterval(intervalId);
  }, [showDashboard, fetchDashboard, fetchTrendsPreview, fetchAdminStatus, fetchImportStatus, fetchTrendCategories, fetchTemplates, fetchInsights, fetchCompetitors]);

  useEffect(() => {
    if (!showDashboard) return;
    if (importStatus?.status !== 'running') return;
    const intervalId = window.setInterval(() => {
      fetchImportStatus();
    }, 1000);
    return () => window.clearInterval(intervalId);
  }, [showDashboard, importStatus?.status, fetchImportStatus]);

  useEffect(() => {
    if (!showDashboard) return;
    setTrendsPage(1);
    fetchTrendsPreview();
  }, [trendsSearch, trendsCategory, showDashboard, fetchTrendsPreview]);

  useEffect(() => {
    if (!showDashboard) return;
    let socket: WebSocket | null = null;
    let isClosed = false;
    const connect = async () => {
      const token = await supabaseService.getAccessToken();
      if (!token) return;
      const wsUrl = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');
      socket = new WebSocket(`${wsUrl}/ws/autopost?token=${encodeURIComponent(token)}`);
      socket.onmessage = () => {
        fetchDashboard();
      };
      socket.onclose = () => {
        if (!isClosed) {
          window.setTimeout(connect, 2000);
        }
      };
    };
    connect();
    return () => {
      isClosed = true;
      if (socket) {
        socket.close();
      }
    };
  }, [showDashboard, fetchDashboard]);

  useEffect(() => {
    if (!showDashboard || !isAdmin) return;
    fetchAdminLogs();
    fetchMidtransStatus();
    fetchAdminAuditLogs();
  }, [showDashboard, isAdmin, fetchAdminLogs, fetchMidtransStatus, fetchAdminAuditLogs]);

  useEffect(() => {
    if (!showDashboard) return;
    refreshSubscriptionStatus();
  }, [showDashboard, refreshSubscriptionStatus]);

  const handleCoinClick = () => {
    setShowCoinModal(!showCoinModal);
  };


  if (showDashboard) {
    return (
      <DashboardView
        items={dashboardItems}
        loading={dashboardLoading}
        error={dashboardError}
        displayName={displayName}
        avatarUrl={avatarUrl}
        onBack={handleBackToStudio}
        onLogout={handleLogout}
        onTopUp={handleTopUp}
        dashboardErrorNeedsTopUp={dashboardErrorNeedsTopUp}
        onRetry={handleDashboardRetry}
        onRecheck={handleDashboardRecheck}
        onRegenerate={handleDashboardRegenerate}
        regeneratingId={dashboardRegeneratingId}
        trialRemaining={trialRemaining}
        isSubscribed={isSubscribed}
        subscribedUntil={subscribedUntil}
        proStatus={proStatus}
        renewWindow={renewWindow}
        expiresInDays={expiresInDays}
        onUploadClick={handleDashboardUploadClick}
        onUploadChange={handleDashboardUploadChange}
        uploadInputRef={dashboardUploadRef}
        trendsPreview={trendsPreview}
        trendsLoading={trendsLoading}
        trendsMessage={trendsMessage}
        onTrendsUploadClick={handleTrendsUploadClick}
        onTrendsUploadChange={handleTrendsUploadChange}
        onTrendsRefresh={handleTrendsRefresh}
        trendsUploadRef={trendsUploadRef}
        isAdmin={isAdmin}
        trendsSearch={trendsSearch}
        onTrendsSearchChange={setTrendsSearch}
        trendsPage={trendsPage}
        trendsPageSize={trendsPageSize}
        onTrendsPageChange={setTrendsPage}
        trendsCategory={trendsCategory}
        onTrendsCategoryChange={setTrendsCategory}
        importStatus={importStatus}
        importErrors={importErrors}
        categoryOptions={categoryOptions}
        onDownloadTemplate={handleDownloadTemplate}
        onDownloadAllTrends={handleDownloadAllTrends}
        autoRetryImport={autoRetryImport}
        onToggleAutoRetry={setAutoRetryImport}
        templates={templates}
        templatesLoading={templatesLoading}
        templatesError={templatesError}
        onCopyTemplate={handleCopyTemplate}
        hashtagRegex={hashtagRegex}
        importErrorRef={importErrorRef}
        errorRowSet={errorRowSet}
        errorPages={errorPages}
        onCopyErrors={handleCopyErrors}
        onExportErrorsCsv={handleExportErrorsCsv}
        insights={insights}
        insightsLoading={insightsLoading}
        insightsError={insightsError}
        onAddCompetitor={handleAddCompetitor}
        competitors={competitors}
        showOnlyErrors={showOnlyErrors}
        onToggleShowOnlyErrors={setShowOnlyErrors}
        hideErrorHighlight={hideErrorHighlight}
        onToggleHideErrorHighlight={setHideErrorHighlight}
        errorRowsInPage={errorRowsInPage}
        adminLogs={adminLogs}
        adminLogsLoading={adminLogsLoading}
        adminLogsError={adminLogsError}
        onAdminLogsRefresh={fetchAdminLogs}
        adminLogsStatus={adminLogsStatus}
        onAdminLogsStatusChange={setAdminLogsStatus}
        adminLogsUserQuery={adminLogsUserQuery}
        onAdminLogsUserQueryChange={setAdminLogsUserQuery}
        adminLogsDateFrom={adminLogsDateFrom}
        onAdminLogsDateFromChange={setAdminLogsDateFrom}
        adminLogsDateTo={adminLogsDateTo}
        onAdminLogsDateToChange={setAdminLogsDateTo}
        adminLogsLimit={adminLogsLimit}
        onAdminLogsLimitChange={setAdminLogsLimit}
        filteredAdminLogs={filteredAdminLogs}
        midtransStatus={midtransStatus}
        midtransStatusLoading={midtransStatusLoading}
        midtransStatusError={midtransStatusError}
        onMidtransStatusRefresh={fetchMidtransStatus}
        metricsVideoId={metricsVideoId}
        onMetricsVideoIdChange={setMetricsVideoId}
        metricsUploadResult={metricsUploadResult}
        metricsUploading={metricsUploading}
        metricsUploadRef={metricsUploadRef}
        onMetricsUploadClick={handleMetricsUploadClick}
        onMetricsUploadChange={handleMetricsUploadChange}
        feedbackWeights={feedbackWeights}
        feedbackWeightsLoading={feedbackWeightsLoading}
        feedbackWeightsError={feedbackWeightsError}
        feedbackWeightsQuery={feedbackWeightsQuery}
        onFeedbackWeightsQueryChange={setFeedbackWeightsQuery}
        onFeedbackWeightsRefresh={fetchFeedbackWeights}
        subscriptionQuery={subscriptionQuery}
        subscriptionInfo={subscriptionInfo}
        subscriptionLoading={subscriptionLoading}
        subscriptionError={subscriptionError}
        subscriptionStatus={subscriptionStatus}
        onSubscriptionQueryChange={setSubscriptionQuery}
        onSubscriptionLookup={fetchSubscriptionInfo}
        onSubscriptionUpdate={updateSubscription}
        adminAuditLogs={adminAuditLogs}
        adminAuditLoading={adminAuditLoading}
        adminAuditError={adminAuditError}
        onAdminAuditRefresh={fetchAdminAuditLogs}
      />
    );
  }

  // Redirect if not authenticated (will be handled by useEffect)
  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-white selection:bg-purple-100">
      {/* Header Section */}
      <div className="luxury-gradient-bg py-16 sm:py-24 md:py-32 lg:py-40 px-4 sm:px-6 text-white text-center relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20 pointer-events-none">
          <Sparkles className="absolute top-10 left-10 w-20 h-20 animate-blink" />
          <Sparkles className="absolute bottom-10 right-10 w-32 h-32 animate-blink" style={{animationDelay: '1s'}} />
          <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-white/20 rounded-full blur-[100px] floating"></div>
        </div>

        <div className="relative z-10 flex flex-col items-center justify-center min-h-[45vh] sm:min-h-[55vh]">
          <div className="flex items-center gap-2 mb-6 bg-white/10 px-4 py-2 rounded-full backdrop-blur-md border border-white/20 shadow-xl badge-scan">
            <Sparkles size={12} className="text-purple-300 animate-blink" />
            <span className="text-[10px] sm:text-xs font-bold tracking-[0.35em] sm:tracking-[0.5em] uppercase text-white">PREMIUM AI STUDIO</span>
            <Sparkles size={12} className="text-pink-300 animate-blink" />
          </div>
          
          <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[9rem] font-sans font-semibold tracking-[0.02em] mb-4 uppercase text-white leading-[1.08]">
            PICTURE ON<br />FRAME
          </h1>
          
          <span className="scanline uppercase tracking-[0.28em] text-[11px] md:text-sm font-medium text-white/70 mt-4">
            STUDIO EXCLUSIVE AI RENDERING
          </span>
        </div>
      </div>

      {/* Dashboard, Coin, Top-Up, and Logout Buttons - Below Header */}
      <div className="relative z-20 px-4 sm:px-6 mt-6 mb-6">
        <div className="max-w-7xl mx-auto flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/app/dashboard"
            className="flex items-center gap-2 px-4 py-2 bg-white/90 backdrop-blur-md border border-purple-200 rounded-xl text-purple-600 hover:bg-white hover:border-purple-300 hover:shadow-lg transition-all duration-300 text-sm font-semibold shadow-sm"
          >
            <LayoutGrid size={16} />
            <span>Dashboard</span>
          </Link>
          <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleCoinClick}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-200 rounded-xl text-amber-600 hover:from-amber-100 hover:to-yellow-100 hover:border-amber-300 hover:shadow-lg transition-all duration-300 text-sm font-semibold shadow-sm relative"
            style={{
              textShadow: '0 0 8px rgba(217, 119, 6, 0.3)',
              filter: 'drop-shadow(0 1px 2px rgba(217, 119, 6, 0.2))'
            }}
          >
            <Coins size={16} className="text-amber-500" style={{ filter: 'drop-shadow(0 0 4px rgba(217, 119, 6, 0.4))' }} />
            <span className="font-bold" style={{ 
              background: 'linear-gradient(135deg, #d97706 0%, #f59e0b 50%, #fbbf24 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: '0 0 10px rgba(217, 119, 6, 0.5)'
            }}>{coins} Coins</span>
          </button>
          <button
            onClick={handleTopUp}
            className="flex items-center gap-2 px-4 py-2 bg-white/90 backdrop-blur-md border border-purple-200 rounded-xl text-purple-600 hover:bg-white hover:border-purple-300 hover:shadow-lg transition-all duration-300 text-sm font-semibold shadow-sm"
          >
            <Wallet size={16} />
            <span>Top-Up</span>
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl hover:bg-gray-50 transition-all duration-300 text-sm font-semibold shadow-md"
          >
            <LogOut size={16} className="text-purple-600" />
            <span className="text-gray-700">Logout</span>
          </button>
          </div>
        </div>
      </div>

      {/* Studio Mode Panel - Overlapping */}
      <div className="relative z-20 -mt-4 sm:-mt-6 px-4 sm:px-6 mb-10 mt-6 sm:mt-10">
        <div className="max-w-7xl mx-auto">
          <div className="glass-panel p-6 md:p-8 rounded-[3rem] shadow-2xl border border-white/40">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[8px] font-bold uppercase tracking-widest text-purple-400 mb-1">CURRENT STUDIO MODE</span>
                <span className="text-[11px] font-black uppercase text-purple-600">{state.options.contentType} • {state.options.category}</span>
              </div>
              <Monitor size={16} className="text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Variant Presets */}
      <div className="relative z-20 px-4 sm:px-6 mb-10">
        <div className="max-w-7xl mx-auto">
          <div className="glass-panel p-6 md:p-8 rounded-[2.5rem] shadow-2xl border border-white/40 bg-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Save size={16} className="text-purple-500" />
                <h3 className="text-sm font-semibold text-slate-700">Variant Input</h3>
              </div>
              <span className="text-[11px] text-slate-500">Simpan & pakai ulang kombinasi input</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr] gap-4">
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-600">Nama Variant</label>
                <input
                  value={variantName}
                  onChange={(e) => setVariantName(e.target.value)}
                  placeholder="Contoh: Fashion indoor soft"
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-200"
                />
                <div className="flex flex-wrap gap-2 text-[11px] text-slate-500">
                  <span className="px-2 py-1 rounded-full bg-slate-100">{state.options.contentType}</span>
                  <span className="px-2 py-1 rounded-full bg-slate-100">{state.options.category}</span>
                  <span className="px-2 py-1 rounded-full bg-slate-100">{state.options.style}</span>
                  <span className="px-2 py-1 rounded-full bg-slate-100">{state.options.lighting}</span>
                </div>
                <button
                  onClick={handleSaveVariant}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 text-white text-sm font-semibold hover:bg-purple-700 transition"
                >
                  <Save size={14} />
                  Simpan Variant
                </button>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
                  <List size={14} className="text-slate-400" />
                  Daftar Variant
                </div>
                {variants.length === 0 ? (
                  <div className="text-xs text-slate-400">Belum ada variant tersimpan.</div>
                ) : (
                  <div className="space-y-2">
                    {variants.map((variant) => (
                      <div key={variant.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 px-3 py-2">
                        <div>
                          <div className="text-sm font-semibold text-slate-700">{variant.name}</div>
                          <div className="text-[11px] text-slate-500">
                            {variant.options.contentType} • {variant.options.category} • {variant.options.style}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleApplyVariant(variant)}
                            className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"
                          >
                            Pakai
                          </button>
                          <button
                            onClick={() => handleDeleteVariant(variant.id)}
                            className="px-3 py-1.5 text-xs rounded-lg bg-red-50 text-red-600 hover:bg-red-100"
                          >
                            Hapus
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 text-left mt-6">
        <div className="grid grid-cols-1 lg:grid-cols-[450px_1fr] gap-12 items-start">
          
          {/* Controls Panel */}
          <aside className="glass-panel p-8 md:p-10 rounded-[3rem] shadow-2xl space-y-12 animate-in slide-in-from-left duration-700 bg-white">
            
            <div className="mb-8">
              <SectionHeader step="1" title="Koleksi Produk" icon={Package} />
              <div className="grid grid-cols-2 gap-4 mt-4">
                {[
                  { ref: fileInputRef, data: state.productImage, type: 'product', label: 'Main' },
                  { ref: fileInput2Ref, data: state.productImage2, type: 'product2', label: 'Opt 2' }
                ].map((slot, idx) => {
                  const currentImageCount = countUploadedImages(state);
                  const isSlotFilled = !!slot.data;
                  const canUpload = isSlotFilled || currentImageCount < 3;
                  
                  return (
                  <div key={idx} className="relative group">
                    <div 
                      onClick={() => {
                        if (!canUpload) {
                          setState(prev => ({ 
                            ...prev, 
                            error: "Maksimal 3 upload gambar. Silakan hapus salah satu gambar terlebih dahulu." 
                          }));
                          return;
                        }
                        slot.ref.current?.click();
                      }}
                      className={`aspect-square rounded-[2rem] border-2 border-dashed flex flex-col items-center justify-center transition-all duration-500 ${
                        !canUpload 
                          ? 'border-red-300 bg-red-50 cursor-not-allowed opacity-50' 
                          : slot.data 
                            ? 'border-purple-400 bg-purple-50 shadow-inner cursor-pointer' 
                            : 'border-gray-200 hover:border-purple-300 bg-white cursor-pointer'
                      }`}
                    >
                      {slot.data ? (
                        <div className="relative w-full h-full p-3 animate-in fade-in zoom-in duration-500">
                          <img src={`data:${slot.data.mimeType};base64,${slot.data.base64}`} className="w-full h-full object-contain" alt={`Product ${idx+1}`} />
                          <div className="absolute top-2 right-2 bg-purple-600 text-white rounded-full p-1">
                            <CheckCircle2 size={12} />
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation(); // Prevent triggering the parent onClick
                              handleDeleteImage(slot.type as any);
                            }}
                            className="absolute top-2 left-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 transition-all duration-200 shadow-lg hover:shadow-xl z-10 group"
                            title="Hapus gambar"
                          >
                            <X size={14} className="group-hover:scale-110 transition-transform" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center text-gray-300 gap-2">
                          <ImageIcon size={24} strokeWidth={1.5} />
                          <span className="text-[9px] font-bold tracking-widest uppercase">{slot.label}</span>
                        </div>
                      )}
                      <input type="file" hidden ref={slot.ref} onChange={(e) => handleFileUpload(e, slot.type as any)} accept="image/*" />
                    </div>
                  </div>
                  );
                })}
              </div>
            </div>

            <div className="mb-8">
              <SectionHeader step="2" title="Wajah Referensi" icon={Camera} />
              <div 
                onClick={() => {
                  const currentImageCount = countUploadedImages(state);
                  const isSlotFilled = !!state.faceImage;
                  const canUpload = isSlotFilled || currentImageCount < 3;
                  
                  if (!canUpload) {
                    setState(prev => ({ 
                      ...prev, 
                      error: "Maksimal 3 upload gambar. Silakan hapus salah satu gambar terlebih dahulu." 
                    }));
                    return;
                  }
                  faceInputRef.current?.click();
                }}
                className={`w-full aspect-[2/1] rounded-[2rem] border-2 border-dashed flex flex-col items-center justify-center transition-all duration-500 mt-4 ${
                  (() => {
                    const currentImageCount = countUploadedImages(state);
                    const isSlotFilled = !!state.faceImage;
                    const canUpload = isSlotFilled || currentImageCount < 3;
                    if (!canUpload) return 'border-red-300 bg-red-50 cursor-not-allowed opacity-50';
                    return state.faceImage ? 'border-purple-400 bg-purple-50 shadow-inner cursor-pointer' : 'border-gray-200 hover:border-purple-300 bg-white cursor-pointer';
                  })()
                }`}
              >
                {state.faceImage ? (
                  <div className="relative h-full p-3 animate-in fade-in duration-500">
                    <img src={`data:${state.faceImage.mimeType};base64,${state.faceImage.base64}`} className="h-full object-contain" alt="Face" />
                    <div className="absolute bottom-2 right-2 bg-purple-600 text-white px-2 py-0.5 rounded-full text-[8px] font-black tracking-widest uppercase">Verified</div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent triggering the parent onClick
                        handleDeleteImage('face');
                      }}
                      className="absolute top-2 left-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 transition-all duration-200 shadow-lg hover:shadow-xl z-10 group"
                      title="Hapus gambar"
                    >
                      <X size={14} className="group-hover:scale-110 transition-transform" />
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center text-gray-300 gap-2">
                    <Camera size={28} strokeWidth={1.5} />
                    <span className="text-[10px] font-bold tracking-[0.2em] uppercase">Upload High-Res Face</span>
                  </div>
                )}
                <input type="file" hidden ref={faceInputRef} onChange={(e) => handleFileUpload(e, 'face')} accept="image/*" />
              </div>
            </div>

            <div className="mb-8">
              <SectionHeader step="3" title="Tipe Konten" icon={LayoutGrid} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {CONTENT_TYPES.map(t => (
                  <OptionChip 
                    key={t} 
                    label={t} 
                    isSelected={state.options.contentType === t} 
                    onClick={() => updateOption('contentType', t)} 
                  />
                ))}
              </div>
            </div>

            {state.options.contentType === "Model" && (
              <div className="mb-8 animate-in slide-in-from-top duration-500">
                <SectionHeader step="3.1" title="Karakter Model" icon={User} />
                <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                  {MODEL_TYPES.map(m => (
                    <OptionChip 
                      key={m} 
                      label={m} 
                      isSelected={state.options.modelType === m} 
                      onClick={() => updateOption('modelType', m)} 
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="mb-8">
              <SectionHeader step="4" title="Kategori Produk" icon={Tag} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {(isAnimalModel ? ["Aksesoris"] : CATEGORY_OPTIONS).map(c => (
                  <OptionChip 
                    key={c} 
                    label={c} 
                    isSelected={state.options.category === c} 
                    onClick={() => updateOption('category', c)} 
                  />
                ))}
              </div>
              {isAnimalModel && (
                <div className="rounded-xl border border-purple-100 bg-purple-50 px-3 py-2 text-[10px] text-purple-700">
                  Khusus model Hewan: kategori dikunci ke Aksesoris agar hasil lebih seimbang.
                </div>
              )}
            </div>

            {state.options.contentType === "Non Model" && (
              <div className="mb-8 animate-in slide-in-from-top duration-500">
                <SectionHeader step="5" title="Interaksi Tangan & Kaki" icon={Hand} />
                <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                  {currentInteractions.map(i => (
                    <OptionChip 
                      key={i} 
                      label={i} 
                      isSelected={state.options.interactionType === i} 
                      onClick={() => updateOption('interactionType', i)} 
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="mb-8">
              <SectionHeader step="6" title="Pose Pilihan" icon={Sparkles} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {currentPoses.length > 0 ? currentPoses.map(p => (
                  <OptionChip 
                    key={p} 
                    label={p} 
                    isSelected={state.options.pose === p} 
                    onClick={() => updateOption('pose', p)}
                  />
                )) : (
                  <p className="text-[10px] text-gray-400 italic">No specific poses for this set. Use custom input.</p>
                )}
              </div>
              {isAnimalModel && (
                <div className="rounded-xl border border-purple-100 bg-purple-50 px-3 py-2 text-[10px] text-purple-700">
                  Khusus model Hewan: pose dikunci ke Close-Up Portrait.
                </div>
              )}
            </div>

            <div className="mb-8">
              <SectionHeader step="7" title="Background" icon={Layers} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {BACKGROUND_OPTIONS.map(opt => (
                  <OptionChip 
                    key={opt}
                    label={opt}
                    isSelected={state.options.background === opt}
                    onClick={() => updateOption('background', opt)}
                  />
                ))}
              </div>
              {state.options.background === 'Upload Background' && (
                <div 
                  onClick={() => {
                    const currentImageCount = countUploadedImages(state);
                    const isSlotFilled = !!state.backgroundImage;
                    const canUpload = isSlotFilled || currentImageCount < 3;
                    
                    if (!canUpload) {
                      setState(prev => ({ 
                        ...prev, 
                        error: "Maksimal 3 upload gambar. Silakan hapus salah satu gambar terlebih dahulu." 
                      }));
                      return;
                    }
                    bgInputRef.current?.click();
                  }} 
                  className={`p-5 border-2 border-dashed rounded-2xl text-center text-[10px] font-bold uppercase transition-colors mt-4 ${
                    (() => {
                      const currentImageCount = countUploadedImages(state);
                      const isSlotFilled = !!state.backgroundImage;
                      const canUpload = isSlotFilled || currentImageCount < 3;
                      if (!canUpload) {
                        return 'border-red-300 bg-red-50 text-red-400 cursor-not-allowed opacity-50';
                      }
                      return state.backgroundImage 
                        ? 'border-purple-400 bg-purple-50 text-purple-600 cursor-pointer' 
                        : 'border-purple-100 text-purple-400 cursor-pointer hover:bg-purple-50';
                    })()
                  }`}
                >
                  {state.backgroundImage ? (
                    <div className="relative w-full">
                      <div className="relative aspect-video rounded-xl overflow-hidden mb-2">
                        <img 
                          src={`data:${state.backgroundImage.mimeType};base64,${state.backgroundImage.base64}`} 
                          className="w-full h-full object-cover" 
                          alt="Background" 
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent triggering the parent onClick
                            handleDeleteImage('background');
                          }}
                          className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 transition-all duration-200 shadow-lg hover:shadow-xl z-10 group"
                          title="Hapus gambar"
                        >
                          <X size={14} className="group-hover:scale-110 transition-transform" />
                        </button>
                      </div>
                      <span className="text-[9px] font-bold text-purple-600 uppercase tracking-wider">Latar Kustom Terpilih</span>
                    </div>
                  ) : (
                    <span>Klik untuk Upload Background Referensi</span>
                  )}
                  <input type="file" hidden ref={bgInputRef} onChange={(e) => handleFileUpload(e, 'background')} accept="image/*" />
                </div>
              )}
            </div>

            <div className="mb-8">
              <SectionHeader step="8" title="Gaya Foto" icon={ImageIcon} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {STYLE_OPTIONS.map(opt => (
                  <OptionChip 
                    key={opt}
                    label={opt}
                    isSelected={state.options.style === opt}
                    onClick={() => updateOption('style', opt)}
                  />
                ))}
              </div>
            </div>

            <div className="mb-8">
              <SectionHeader step="9" title="Pencahayaan" icon={Sun} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {LIGHTING_OPTIONS.map(opt => (
                  <OptionChip 
                    key={opt}
                    label={opt}
                    isSelected={state.options.lighting === opt}
                    onClick={() => updateOption('lighting', opt)}
                  />
                ))}
              </div>
            </div>

            <div className="mb-8">
              <SectionHeader step="10" title="Rasio Aspek" icon={Maximize} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {ASPECT_RATIOS.map(r => (
                  <OptionChip key={r} label={r} isSelected={state.options.aspectRatio === r} onClick={() => updateOption('aspectRatio', r)} />
                ))}
              </div>
            </div>

            <div className="mb-8">
              <SectionHeader step="11" title="Sudut Pandang" icon={Camera} />
              <div className="flex flex-wrap gap-2 w-full mt-2 mb-6">
                {CAMERA_ANGLES.map(a => (
                  <OptionChip key={a} label={a} isSelected={state.options.cameraAngle === a} onClick={() => updateOption('cameraAngle', a)} />
                ))}
              </div>
            </div>


            <div className="mb-8">
              <SectionHeader step="12" title="Identitas" icon={User} />
              <IdentitySelector onChange={setIdentityMode} />
            </div>

            <div className="pt-6">
              <button
                onClick={handleGenerate}
                disabled={state.isGenerating || (!state.productImage && !state.productImage2 && !state.productImage3 && !state.productImage4)}
                data-identity-mode={identityMode}
                className={`w-full py-16 rounded-[3rem] font-black text-lg tracking-[0.5em] uppercase relative overflow-hidden group shadow-lg transition-all duration-300 ${
                  state.isGenerating 
                    ? 'text-white generating-button' 
                    : 'premium-button disabled:opacity-50 disabled:grayscale'
                }`}
              >
                {/* Animated background shimmer effect when generating */}
                {state.isGenerating && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                )}
                
                <span className={`relative z-10 flex items-center justify-center gap-4 ${
                  state.isGenerating ? 'animate-pulse text-white tracking-[0.2em]' : ''
                }`} style={state.isGenerating ? { color: '#ffffff' } : {}}>
                  {state.isGenerating ? (
                    <>
                      <Loader2 className="animate-spin" size={28} style={{ filter: 'drop-shadow(0 0 8px rgba(255, 255, 255, 0.8))', color: '#ffffff' }} />
                      <span className="text-white">Menciptakan Karya...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={28} />
                      Generate Batch
                    </>
                  )}
                </span>
              </button>
              {state.error && (
                <p className="mt-5 text-[10px] text-red-500 font-bold text-center uppercase tracking-widest">
                  {state.error.includes('Top Up') ? (
                    <span className="inline-flex flex-wrap items-center gap-2">
                      <span>{state.error.replace('Top Up', '').trim()}</span>
                      <button
                        onClick={handleTopUp}
                        className="text-indigo-600 hover:text-indigo-800 font-bold underline"
                      >
                        Top Up
                      </button>
                    </span>
                  ) : (
                    state.error
                  )}
                </p>
              )}
            </div>
          </aside>

          {/* Results Gallery */}
          <main className="space-y-12 animate-in fade-in duration-1000">
            <div className="flex items-center justify-between border-b border-gray-100 pb-10">
              <div className="space-y-1 text-left">
                <h2 className="text-4xl font-black tracking-tighter uppercase luxury-text italic">Studio Gallery</h2>
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.5em]">Exclusive AI Renderings</p>
              </div>
              <LayoutGrid size={28} className="text-gray-200" strokeWidth={1.5} />
            </div>

            {state.isGenerating ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                {[...Array(1)].map((_, i) => (
                  <div key={i} className="aspect-[3/4] bg-white rounded-[3rem] shadow-xl flex flex-col items-center justify-center gap-6 animate-pulse border border-gray-100">
                    <div className="w-16 h-16 border-4 border-purple-50 border-t-purple-600 rounded-full animate-spin"></div>
                    <p className="text-[11px] font-black text-gray-400 uppercase tracking-[0.3em]">Developing Piece {i+1}</p>
                  </div>
                ))}
              </div>
            ) : state.results.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                {state.results.slice(0, 1).map((result, i) => (
                  <React.Fragment key={`result-${i}`}>
                  <div className="flex flex-col gap-6 group">
                    <div className="relative bg-white p-5 rounded-[3.5rem] shadow-2xl transition-all duration-1000 hover:-translate-y-4">
                      <div className="relative aspect-[3/4] overflow-hidden rounded-[3rem] bg-gray-50 border border-gray-100">
                        
                        {state.videoResults[i] ? (
                          <video 
                            src={state.videoResults[i]} 
                            className="w-full h-full object-cover" 
                            autoPlay 
                            loop 
                            muted 
                            playsInline
                          />
                        ) : (
                          <img src={result.url} className="w-full h-full object-cover" alt={`Result ${i+1}`} />
                        )}

                        {state.isVideoGenerating[i] && (
                          <div className="absolute inset-0 bg-black/40 backdrop-blur-md flex flex-col items-center justify-center text-white p-8 text-center gap-4 z-20">
                            <Loader2 className="animate-spin text-purple-400" size={48} />
                            <div className="space-y-2">
                              <p className="text-xs font-black uppercase tracking-[0.2em]">Creating TikTok Video</p>
                              <p className="text-[10px] text-white/60">Adding smooth zoom and text overlays. This may take 30-60 seconds.</p>
                            </div>
                          </div>
                        )}
                        
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-700 backdrop-blur-[2px] flex flex-col items-center justify-center gap-4 z-10">
                          <div className="flex gap-4">
                            <button 
                              onClick={async () => {
                                try {
                                  const url = state.videoResults[i] || result.url;
                                  const response = await fetch(url);
                                  const blob = await response.blob();
                                  const blobUrl = window.URL.createObjectURL(blob);
                                  const link = document.createElement('a');
                                  link.href = blobUrl;
                                  link.download = `picture-on-frame-${getDownloadTimestamp()}-${i}.${state.videoResults[i] ? 'mp4' : 'png'}`;
                                  document.body.appendChild(link);
                                  link.click();
                                  document.body.removeChild(link);
                                  window.URL.revokeObjectURL(blobUrl);
                                } catch (error) {
                                  console.error('Error downloading file:', error);
                                  // Fallback to direct download if fetch fails
                                  const link = document.createElement('a');
                                  link.href = state.videoResults[i] || result.url;
                                  link.download = `picture-on-frame-${getDownloadTimestamp()}-${i}.${state.videoResults[i] ? 'mp4' : 'png'}`;
                                  link.target = '_self';
                                  link.click();
                                }
                              }}
                              className="w-16 h-16 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-all shadow-xl"
                              title="Download"
                            >
                              <Download size={24} className="text-black" />
                            </button>
                            
                            {!state.videoResults[i] && !state.isVideoGenerating[i] && (
                              <button 
                                onClick={() => handleGenerateVideo(i, result.url)}
                                className="w-16 h-16 rounded-full bg-purple-600 flex items-center justify-center hover:scale-110 transition-all shadow-xl text-white"
                                title="Create Free Video"
                                disabled={state.isVideoGenerating[i]}
                              >
                                <Video size={24} />
                              </button>
                            )}
                          </div>
                          <span className="text-white text-[9px] font-black uppercase tracking-[0.4em]">
                            {state.videoResults[i] ? 'Download Free Video' : state.isVideoGenerating[i] ? 'Creating Video...' : 'Create Free Video'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="mt-8 flex justify-between items-end px-4">
                        <div className="space-y-1 text-left">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${state.videoResults[i] ? 'bg-pink-500 animate-pulse' : 'bg-purple-600'}`}></div>
                            <p className="text-[10px] font-black text-purple-600 tracking-[0.3em] uppercase">
                              {state.videoResults[i] ? 'Cinematic Video' : `Render ${i+1}`}
                            </p>
                          </div>
                          <p className="text-2xl font-black tracking-tight text-gray-800 uppercase italic leading-none">Studio Pro</p>
                        </div>
                      </div>
                      
                      {/* Free Video Pilihan Section - 3 videos below image */}
                      <div className="mt-6 bg-white rounded-[2rem] p-6 border border-gray-100 shadow-lg">
                        <div className="mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-[11px] font-black text-gray-700 uppercase tracking-[0.3em]">Free Video Pilihan</h3>
                            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[9px] font-black uppercase tracking-[0.2em]">Free</span>
                          </div>
                          {state.isVideoBatchGenerating[i] && (
                            <div className="flex items-center gap-2 text-purple-600">
                              <Loader2 className="animate-spin" size={16} />
                              <p className="text-[10px] font-medium">Membuat 3 variasi video...</p>
                            </div>
                          )}
                        </div>
                        
                        {state.videoBatches[i] && state.videoBatches[i].length > 0 ? (
                          <div className="grid grid-cols-3 gap-4 w-full" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
                            {state.videoBatches[i].map((videoUrl: string, videoIndex: number) => {
                              return (
                                <div key={`video-${i}-${videoIndex}`} className="flex flex-col gap-2 group/video w-full">
                                  <div className="relative aspect-[9/16] rounded-xl overflow-hidden bg-gray-50 border border-gray-200 w-full min-h-[200px]">
                                    {/* Debug badge */}
                                    <div className="absolute top-1 left-1 bg-purple-600 text-white text-[8px] font-bold px-1.5 py-0.5 rounded z-20">
                                      #{videoIndex + 1}
                                    </div>
                                    <video 
                                      key={videoUrl} // Force re-render when URL changes
                                      src={videoUrl}
                                      className="w-full h-full object-cover"
                                      muted
                                      playsInline
                                      autoPlay
                                      loop
                                      onError={(e) => {
                                        console.error(`❌ Error loading video ${videoIndex + 1}:`, e);
                                        console.error(`Video URL:`, videoUrl);
                                      }}
                                      onLoadedData={() => {
                                        console.log(`✅ Video ${videoIndex + 1} loaded successfully`);
                                      }}
                                      onMouseEnter={(e) => {
                                        e.currentTarget.play().catch(err => {
                                          console.warn(`Could not play video ${videoIndex + 1}:`, err);
                                        });
                                      }}
                                      onMouseLeave={(e) => {
                                        e.currentTarget.pause();
                                        e.currentTarget.currentTime = 0;
                                      }}
                                    />
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/video:opacity-100 transition-opacity flex items-center justify-center">
                                      <button
                                        onClick={async () => {
                                          try {
                                            const response = await fetch(videoUrl);
                                            const blob = await response.blob();
                                            const blobUrl = window.URL.createObjectURL(blob);
                                            const link = document.createElement('a');
                                            link.href = blobUrl;
                                            link.download = `picture-on-frame-free-video-${i+1}-variasi-${videoIndex+1}-${getDownloadTimestamp()}.mp4`;
                                            document.body.appendChild(link);
                                            link.click();
                                            document.body.removeChild(link);
                                            window.URL.revokeObjectURL(blobUrl);
                                          } catch (error) {
                                            console.error('Error downloading video:', error);
                                            const link = document.createElement('a');
                                            link.href = videoUrl;
                                            link.download = `picture-on-frame-free-video-${i+1}-variasi-${videoIndex+1}.mp4`;
                                            link.click();
                                          }
                                        }}
                                        className="w-12 h-12 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-all shadow-xl"
                                        title="Download Video"
                                      >
                                        <Download size={20} className="text-black" />
                                      </button>
                                    </div>
                                  </div>
                                  <p className="text-[9px] font-medium text-gray-600 text-center">Variasi {videoIndex + 1}</p>
                                </div>
                              );
                            })}
                          </div>
                        ) : !state.isVideoBatchGenerating[i] ? (
                          <div className="text-center py-8 text-gray-400">
                            <Video size={32} className="mx-auto mb-2 opacity-50" />
                            <p className="text-[10px] font-medium">Video akan dibuat otomatis setelah gambar selesai</p>
                          </div>
                        ) : null}
                      </div>
                    </div>

                    {/* Grok Video Prompts Section */}
                    <div className="glass-panel rounded-[2rem] p-6 space-y-4 border border-purple-100/50 shadow-sm">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-purple-600">GROK VIDEO PROMPT (6 SECONDS) — VERSION A</h4>
                          <CopyButton text={result.promptA} />
                        </div>
                        <p className="text-[11px] text-gray-600 leading-relaxed font-medium bg-white/50 p-3 rounded-xl border border-gray-50 italic">
                          "{result.promptA}"
                        </p>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-600">GROK VIDEO PROMPT (6 SECONDS) — VERSION B</h4>
                          <CopyButton text={result.promptB} />
                        </div>
                        <p className="text-[11px] text-gray-600 leading-relaxed font-medium bg-white/50 p-3 rounded-xl border border-gray-50 italic">
                          "{result.promptB}"
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-6 group">
                    <div className="relative bg-white p-5 rounded-[3.5rem] shadow-2xl transition-all duration-1000 hover:-translate-y-4">
                      <div className="px-4 pt-2 pb-4">
                        <p className="text-xs font-semibold text-slate-600">Let's make your own PRO VIDEO here..</p>
                      </div>
                      <div className="relative aspect-[3/4] overflow-hidden rounded-[3rem] bg-gray-50 border border-gray-100">
                        {state.klingVideoResults[i] ? (
                          <video
                            src={state.klingVideoResults[i]}
                            className="w-full h-full object-cover"
                            autoPlay
                            loop
                            muted
                            playsInline
                          />
                        ) : (
                          <img
                            src={state.klingSelectedImages[i] || result.url}
                            className="w-full h-full object-cover"
                            alt={`Pro Video Preview ${i + 1}`}
                          />
                        )}

                        {state.isKlingVideoGenerating[i] && (
                          <div className="absolute inset-0 bg-black/40 backdrop-blur-md flex flex-col items-center justify-center text-white p-8 text-center gap-4 z-20">
                            <Loader2 className="animate-spin text-purple-400" size={48} />
                            <div className="space-y-2">
                              <p className="text-xs font-black uppercase tracking-[0.2em]">Creating Pro Video</p>
                              <p className="text-[10px] text-white/60">Rendering image-to-video. Please wait.</p>
                            </div>
                          </div>
                        )}

                        {state.klingVideoResults[i] && (
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-700 backdrop-blur-[2px] flex flex-col items-center justify-center gap-4 z-10">
                            <div className="flex gap-4">
                              <button
                                onClick={async () => {
                                  try {
                                    const url = state.klingVideoResults[i];
                                    const response = await fetch(url);
                                    const blob = await response.blob();
                                    const blobUrl = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = blobUrl;
                                    link.download = `picture-on-frame-pro-video-${getDownloadTimestamp()}-${i}.mp4`;
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                    window.URL.revokeObjectURL(blobUrl);
                                  } catch (error) {
                                    const link = document.createElement('a');
                                    link.href = state.klingVideoResults[i];
                                    link.download = `picture-on-frame-pro-video-${getDownloadTimestamp()}-${i}.mp4`;
                                    link.target = '_self';
                                    link.click();
                                  }
                                }}
                                className="w-16 h-16 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-all shadow-xl"
                                title="Download"
                              >
                                <Download size={24} className="text-black" />
                              </button>
                            </div>
                            <span className="text-white text-[9px] font-black uppercase tracking-[0.4em]">
                              Download Pro Video
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="mt-6 flex flex-col gap-4 px-4">
                        <div className="flex items-center gap-3">
                          <input
                            id={`kling-image-${i}`}
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={(event) => handleSelectKlingImage(i, event.target.files?.[0])}
                          />
                          <label
                            htmlFor={`kling-image-${i}`}
                            className="px-4 py-2 text-[10px] font-bold rounded-full bg-white border border-purple-200 text-purple-700 hover:bg-purple-50 transition-all cursor-pointer"
                          >
                            Pilih gambar
                          </label>
                          <button
                            onClick={() => handleGenerateKlingVideo(i, state.klingSelectedImages[i] || result.url)}
                            className="px-4 py-2 text-[10px] font-bold rounded-full bg-purple-600 text-white hover:bg-purple-700 transition-all disabled:opacity-60"
                            disabled={state.isKlingVideoGenerating[i]}
                          >
                            Create Pro Video
                          </button>
                        </div>
                      </div>

                      <div className="mt-4 flex justify-between items-end px-4">
                        <div className="space-y-1 text-left">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${state.klingVideoResults[i] ? 'bg-pink-500 animate-pulse' : 'bg-purple-600'}`}></div>
                            <p className="text-[10px] font-black text-purple-600 tracking-[0.3em] uppercase">
                              {state.klingVideoResults[i] ? 'Pro Video' : `Pro Render ${i + 1}`}
                            </p>
                          </div>
                          <p className="text-2xl font-black tracking-tight text-gray-800 uppercase italic leading-none">Pro Video</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  </React.Fragment>
                ))}
              </div>
            ) : (
              <div className="py-52 bg-white rounded-[4rem] shadow-inner border-2 border-dashed border-gray-50 flex flex-col items-center justify-center text-center px-12 animate-in fade-in zoom-in duration-1000">
                <h3 className="text-2xl font-black text-gray-800 uppercase tracking-[0.3em] mb-4 text-center">Mulai Penciptaan</h3>
                <p className="text-sm text-gray-400 italic text-center">Unggah produk Anda dan biarkan AI kami mengolahnya menjadi visual yang tak terlupakan.</p>
              </div>
            )}
          </main>
        </div>
      </div>

      <footer className="mt-52 text-center space-y-12 flex flex-col items-center">
        <div className="w-48 h-px bg-gradient-to-r from-transparent via-purple-100 to-transparent"></div>
        <p className="text-[11px] font-black tracking-[1.5em] text-gray-300 uppercase">PREMIUM AI STUDIO</p>
        <p className="text-3xl font-black tracking-tighter luxury-text italic uppercase">Picture on Frame AI Generate Image Video and Auto-Post</p>
      </footer>

      {/* Coin Balance Modal */}
      {showCoinModal && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={() => setShowCoinModal(false)}
        >
          <div 
            className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-purple-100"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center border border-amber-200">
                  <Coins size={20} className="text-amber-500" />
                </div>
                <h2 className="text-xl font-bold text-gray-800">Saldo Coins</h2>
              </div>
              <button
                onClick={() => setShowCoinModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-6 border border-amber-200">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Total Coins</p>
                  <p className="text-4xl font-black text-amber-600 mb-1">{coins}</p>
                  <p className="text-xs text-gray-500">Tersedia untuk digunakan</p>
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Penggunaan Coins</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <ImageIcon size={16} className="text-amber-500" />
                      <span className="text-sm text-gray-700">Generate Image</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">75 Coins</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Video size={16} className="text-amber-500" />
                      <span className="text-sm text-gray-700">Generate Pro Video</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">185 Coins</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Upload size={16} className="text-amber-500" />
                      <span className="text-sm text-gray-700">AI Auto-Post</span>
                    </div>
                    <span className="text-sm font-semibold text-amber-600">90 Coins</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowCoinModal(false);
                    handleTopUp();
                  }}
                  className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-amber-700 transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-amber-200"
                >
                  <Wallet size={18} />
                  <span>Top Up Coins</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={() => setShowUpgradeModal(false)}
        >
          <div
            className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-purple-100"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center border border-purple-200">
                <Lock size={20} className="text-purple-500" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800">🔒 Trial Kamu Sudah Habis</h3>
                <p className="text-xs text-slate-500">Upgrade ke Pro untuk lanjut.</p>
              </div>
            </div>
            <div className="text-sm text-slate-600 space-y-3">
              <p>Kamu sudah menggunakan 3x upload gratis.</p>
              <div className="space-y-1 text-xs text-slate-600">
                <div>• AI generate hook, CTA, hashtag otomatis</div>
                <div>• FYP Score + penjelasan skor</div>
                <div>• Auto schedule posting</div>
                <div>• AI belajar dari performa akun</div>
                <div>• Regenerate metadata tanpa batas</div>
              </div>
              <div className="mt-3 text-sm font-semibold text-slate-800">
                💳 Rp49.000 / bulan
                <span className="block text-xs text-slate-500 font-normal">Bisa dibatalkan kapan saja</span>
              </div>
            </div>
            <div className="mt-6 flex flex-col gap-2">
              <button
                onClick={() => {
                  handleUpgradeClick();
                }}
                className="w-full px-4 py-2 rounded-xl bg-purple-600 text-white font-semibold hover:bg-purple-700 transition disabled:opacity-60"
                disabled={upgradeLoading}
              >
                {upgradeLoading ? 'Memproses...' : 'Bayar via Midtrans'}
              </button>
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
              >
                Nanti dulu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

