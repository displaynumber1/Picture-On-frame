'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Book, Lightbulb, Users, Info, HelpCircle, X, Monitor, AlertTriangle, Send, Facebook, Share2, Instagram } from 'lucide-react';

declare global {
  interface Window {
    google?: any;
  }
}

const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<{ title: string; content: React.ReactNode } | null>(null);
  const [shareUrl, setShareUrl] = useState('');
  const [isShareOpen, setIsShareOpen] = useState(false);

  const API_URL =
    (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

  // WhatsApp number - format: country code + number (without + or spaces)
  // Example: 6282115434299 (for Indonesia +62 821-1543-4299)
  const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '6285190049996';

  const handleContactUs = () => {
    const message = encodeURIComponent('Halo kak, saya tertarik dengan tools Picture on Frame.');
    const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${message}`;
    window.open(whatsappUrl, '_blank');
  };

  // Menu items configuration
  const menuItems = [
    {
      id: 'panduan',
      label: 'Panduan',
      icon: Book,
      content: (
        <div className="space-y-4 text-sm text-gray-700">
          <ul className="space-y-2 list-disc list-inside">
            <li>Upload produk yang ingin kamu promosikan</li>
            <li>Upload beberapa produk dalam sekali upload untuk mendapatkan kombinasi produk</li>
            <li>Upload Wajah kamu untuk mendapatkan hasil yang lebih personal</li>
            <li>Pilih kategori produk yang ingin kamu promosikan untuk mendapatkan hasil yang lebih sesuai</li>
            <li>Untuk Pose dan Background, pilih yang sesuai dengan produk yang ingin kamu promosikan</li>
            <li>untuk gaya foto pilih dan sesuaikan dari background yang kamu upload</li>
            <li>untuk pencahyaan sesuaikan dengan konsep produk dan background yang kamu upload</li>
            <li>Klik Generate untuk membuat gambar produk profesional</li>
            <li>Download hasil gambar atau buat variasi lainnya</li>
          </ul>
        </div>
      )
    },
    {
      id: 'tips',
      label: 'Tips & Trick',
      icon: Lightbulb,
      content: (
        <div className="space-y-4 text-sm text-gray-700">
          <ul className="space-y-2 list-disc list-inside">
            <li>📸 Gunakan foto produk dengan resolusi tinggi untuk hasil terbaik</li>
            <li>🎨 Eksperimen dengan berbagai kombinasi style dan lighting</li>
            <li>✨ Coba berbagai pose untuk menemukan yang paling menarik</li>
            <li>🎯 Pilih background yang kontras dengan warna produk</li>
            <li>💡 Gunakan custom prompt untuk hasil yang lebih spesifik</li>
            <li>🔄 Buat beberapa variasi untuk membandingkan hasil</li>
          </ul>
        </div>
      )
    },
    {
      id: 'komunitas',
      label: 'Komunitas',
      icon: Users,
      content: (
        <div className="space-y-4 text-sm text-gray-700">
          <p>Bergabunglah dengan 250+ member Picture on Frame untuk:</p>
          <ul className="space-y-2 list-disc list-inside">
            <li>Berbagi hasil karya dan inspirasi</li>
            <li>Mendapatkan feedback dari sesama pengguna</li>
            <li>Feel Free to Share your result</li>
            <li>Saling Support dan Berbagi pengalaman Affiliate</li>
          </ul>
          <p className="text-xs text-gray-500 mt-4">Hubungi kami melalui WhatsApp untuk info lebih lanjut.</p>
        </div>
      )
    },
    {
      id: 'about',
      label: 'About Me',
      icon: Info,
      content: (
        <div className="space-y-4 text-sm text-gray-700">
          <p className="font-semibold">Picture on Frame</p>
          <p>Platform AI-powered untuk membuat foto produk profesional dengan mudah.</p>
          <p className="text-xs text-gray-500 mt-4">
            Follow tiktok: Sassywiff, IG: slstari<br />
            © 2026 Picture on Frame. All rights reserved.
          </p>
        </div>
      )
    }
  ];

  const handleMenuClick = (item: typeof menuItems[0]) => {
    setModalContent({ title: item.label, content: item.content });
    setIsModalOpen(true);
    setIsMenuOpen(false);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalContent(null);
  };

  useEffect(() => {
    try {
      setShareUrl(window.location.origin);
    } catch {
      // ignore
    }
  }, []);

  const isUnregisteredError = error.toLowerCase().includes('belum terdaftar');

  // === SUPABASE AUTH FLOW ===
  const handleGoogleLogin = async () => {
    setError('');
    setIsLoading(true);

    try {
      // Use Supabase for Google OAuth
      const { supabaseService } = await import('../services/supabaseService');
      const { error } = await supabaseService.signInWithGoogle();
      
      if (error) {
        throw new Error('Login gagal. Silakan coba lagi.');
      }
      
      // Redirect will be handled by the global auth listener
    } catch (err: any) {
      console.error('Login error:', err);
      setError('Login gagal. Silakan coba lagi.');
      setIsLoading(false);
    }
  };

  const WhatsAppIcon = ({ size = 14 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#25D366"
        d="M12.02 2C6.49 2 2 6.48 2 12c0 1.94.55 3.82 1.6 5.44L2 22l4.74-1.55A9.97 9.97 0 0 0 12.02 22C17.53 22 22 17.52 22 12S17.53 2 12.02 2zm0 18.2c-1.67 0-3.3-.44-4.73-1.27l-.34-.2-2.81.92.92-2.73-.22-.36A8.12 8.12 0 0 1 3.8 12c0-4.52 3.68-8.2 8.22-8.2 4.53 0 8.2 3.68 8.2 8.2 0 4.53-3.67 8.2-8.2 8.2zm4.64-6.19c-.25-.12-1.5-.74-1.73-.82-.23-.09-.4-.12-.57.12-.17.24-.66.82-.81.99-.15.17-.3.2-.55.07-.25-.12-1.05-.39-2-1.24-.74-.66-1.25-1.48-1.4-1.73-.15-.25-.02-.38.11-.5.12-.12.25-.3.38-.45.13-.15.17-.25.25-.42.08-.17.04-.32-.02-.45-.06-.12-.57-1.38-.78-1.9-.2-.48-.4-.41-.57-.42h-.49c-.17 0-.45.06-.69.32-.24.25-.9.88-.9 2.15 0 1.27.92 2.49 1.04 2.66.12.17 1.81 2.76 4.39 3.87.61.26 1.09.41 1.46.52.62.2 1.18.17 1.63.1.5-.08 1.5-.61 1.71-1.2.21-.59.21-1.1.15-1.2-.06-.1-.23-.16-.48-.28z"
      />
    </svg>
  );

  const TikTokIcon = ({ size = 14 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#25F4EE" d="M14.2 4.2c.6 1.7 2 3 3.7 3.6v2.3c-1.6-.1-3.1-.7-4.3-1.7v6.3c0 2.7-2.2 4.9-4.9 4.9-2.7 0-4.9-2.2-4.9-4.9 0-2.7 2.2-4.9 4.9-4.9.3 0 .7 0 1 .1v2.4c-.3-.1-.6-.2-1-.2-1.4 0-2.5 1.1-2.5 2.5 0 1.4 1.1 2.5 2.5 2.5 1.4 0 2.5-1.1 2.5-2.5V2h2.9c0 .7.1 1.5.1 2.2z" />
      <path fill="#FE2C55" d="M13.6 3.6c.6 1.7 2 3 3.7 3.6v2.3c-1.6-.1-3.1-.7-4.3-1.7v6.3c0 2.7-2.2 4.9-4.9 4.9-2.4 0-4.4-1.8-4.8-4.1.4 1.2 1.6 2 3 2 1.8 0 3.2-1.4 3.2-3.2V3.4h4.1z" />
      <path fill="#FFFFFF" d="M12.7 2h1.9c0 .7.1 1.5.3 2.2-1.2-.1-1.9-.5-2.2-.7V2z" />
    </svg>
  );

  const ThreadsIcon = ({ size = 14 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#FFFFFF"
        d="M12 2.2c-4.3 0-7.8 3.5-7.8 7.8 0 4.6 3.7 8.3 8.3 8.3 2.9 0 5.3-1.4 6.7-3.6-.2-1.6-.8-2.8-1.7-3.7-.8-.8-2-1.2-3.3-1.2-1.6 0-2.8.6-3.5 1.7-.5.8-.7 1.7-.7 2.7h-2c0-1.4.3-2.7 1-3.8 1-1.6 2.8-2.6 5.2-2.6 1.9 0 3.5.7 4.7 1.8.1-2.6-1.9-4.9-4.7-5.5-.4-.1-.9-.1-1.3-.1zm2.3 10.1c.7.3 1.2.8 1.5 1.4-.8 1.2-2.2 2-3.8 2-2.4 0-4.3-1.9-4.3-4.3 0-2.4 1.9-4.3 4.3-4.3 1.2 0 2.3.5 3.1 1.2-.4 0-.8.1-1.1.2-1.2.4-2 .9-2.6 1.7-.4.6-.6 1.2-.6 1.8h2c0-.4.1-.8.3-1.1.3-.5.9-.8 1.8-1 .2 0 .4-.1.6-.1.2.1.4.2.8.5z"
      />
    </svg>
  );

  const XIcon = ({ size = 14 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#FFFFFF" d="M3 3h3.7l4.5 6.5L16.2 3H21l-7 9.2L21 21h-3.7l-4.9-7L7.7 21H3l7.6-9.9L3 3z" />
    </svg>
  );

  const shareText = 'Coba Picture on Frame untuk hasil foto produk yang lebih profesional!';
  const shareTargets = [
    {
      label: 'WhatsApp',
      icon: WhatsAppIcon,
      href: shareUrl
        ? `https://wa.me/?text=${encodeURIComponent(`${shareText} ${shareUrl}`)}`
        : null
    },
    {
      label: 'Telegram',
      icon: Send,
      href: shareUrl
        ? `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`
        : null
    },
    {
      label: 'Instagram',
      icon: Instagram,
      href: shareUrl
        ? `https://www.instagram.com/?url=${encodeURIComponent(shareUrl)}`
        : null
    },
    {
      label: 'Threads',
      icon: ThreadsIcon,
      href: shareUrl
        ? `https://www.threads.net/intent/post?text=${encodeURIComponent(`${shareText} ${shareUrl}`)}`
        : null
    },
    {
      label: 'Facebook',
      icon: Facebook,
      href: shareUrl
        ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`
        : null
    },
    {
      label: 'X',
      icon: XIcon,
      href: shareUrl
        ? `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`
        : null
    }
  ];

  const handleShare = () => {
    if (!shareUrl) return;
    setIsShareOpen(true);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center luxury-gradient-bg relative overflow-hidden">
      {/* Animated background elements - same as header */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20 pointer-events-none">
        <Sparkles className="absolute top-10 left-10 w-20 h-20 animate-blink" />
        <Sparkles className="absolute bottom-10 right-10 w-32 h-32 animate-blink" style={{animationDelay: '1s'}} />
        <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-white/20 rounded-full blur-[100px] floating"></div>
      </div>

      {/* Login Card - positioned above background */}
      <div className="relative z-10 w-full max-w-md px-5 py-10 sm:px-8">
        <div
          className="bg-white/20 backdrop-blur-xl rounded-3xl border border-white/30 shadow-2xl p-6 sm:p-8 md:p-10"
        >
          {/* Header */}
          <div className="flex items-center justify-center gap-2 mb-5">
            <Sparkles size={10} className="text-purple-300 animate-blink" />
            <span className="text-[8px] sm:text-[9px] font-bold tracking-[0.35em] sm:tracking-[0.5em] uppercase text-white">
              PREMIUM AI STUDIO
            </span>
            <Sparkles size={10} className="text-pink-300 animate-blink" />
          </div>

          {/* Main Title */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-2 text-center title-serif drop-shadow-2xl">
            <span className="text-white">Picture</span>{' '}
            <span className="text-[#ec4899] italic">on</span>{' '}
            <span className="text-white">Frame</span>
          </h1>

          {/* Subtitle */}
          <div className="text-[8px] sm:text-[9px] uppercase tracking-[0.45em] sm:tracking-[0.7em] font-medium text-white/70 mb-6 sm:mb-8 text-center">
            <span className="text-white">Exclusive AI Renderings</span>
          </div>

          {/* Error Message */}
          {error && (
            <div
              className={`mb-5 p-4 rounded-xl text-sm text-center border ${
                isUnregisteredError
                  ? 'bg-amber-500/20 text-amber-100 border-amber-400/60'
                  : 'bg-red-500/20 text-red-200 border-red-500/50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                {isUnregisteredError ? (
                  <AlertTriangle size={16} className="text-amber-200" />
                ) : (
                  <X size={16} className="text-red-200" />
                )}
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Google Login Button */}
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading || !process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}
            className="w-full py-3.5 sm:py-4 bg-white text-gray-700 rounded-2xl flex justify-center items-center gap-3 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-medium border border-white text-sm sm:text-base"
          >
            {/* Google Logo SVG */}
            <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            <span>{isLoading ? 'Loading...' : 'Continue with Google'}</span>
          </button>

          {/* Hubungi Kami Button */}
          <button
            onClick={handleContactUs}
            className="w-full py-3.5 sm:py-4 bg-white/10 border-2 border-white text-white hover:text-white rounded-2xl flex justify-center items-center gap-3 shadow-lg hover:bg-white/20 hover:shadow-xl hover:shadow-white/20 transition-all duration-300 font-medium mt-3 cursor-pointer text-sm sm:text-base"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            <span>Hubungi Kami</span>
          </button>

          <div className="mt-5 sm:mt-6 flex flex-col items-center">
            <button
              onClick={handleShare}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/25 border border-white/30 text-white font-semibold text-xs sm:text-sm hover:bg-white/35 transition-all duration-300"
            >
              <Share2 size={16} />
              Share
            </button>
          </div>
        </div>
      </div>

      {isShareOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-white/20 border border-white/30 backdrop-blur-xl shadow-2xl p-5 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 font-semibold">
                <Share2 size={16} />
                Share
              </div>
              <button
                onClick={() => setIsShareOpen(false)}
                className="p-1 rounded-lg hover:bg-white/20 transition-all"
                aria-label="Tutup"
              >
                <X size={16} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {shareTargets.map((target) => {
                const Icon = target.icon;
                return (
                  <button
                    key={target.label}
                    onClick={() => target.href && window.open(target.href, '_blank')}
                    disabled={!target.href}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/25 border border-white/30 text-white hover:bg-white/35 transition-all duration-300 text-xs font-semibold disabled:opacity-50"
                  >
                    <Icon size={14} />
                    {target.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Floating Corner Menu */}
      <div className="fixed top-1/2 right-8 -translate-y-1/2 z-50">
        {/* Desktop: Full Menu */}
        <div className="hidden md:flex flex-col gap-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleMenuClick(item)}
                className="group bg-white/10 backdrop-blur-md border border-white/30 rounded-xl px-4 py-3 text-xs text-white/70 hover:text-white/70 hover:bg-white/20 hover:shadow-lg hover:shadow-white/20 hover:border-white/50 hover:ring-1 hover:ring-white/10 transition-all duration-300 flex items-center gap-2 min-w-[140px]"
              >
                <Icon size={16} className="group-hover:scale-110 transition-transform text-white/70 group-hover:text-white/70" />
                <span className="text-white/70 group-hover:text-white/70">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Mobile: Help Icon with Popover */}
        <div className="md:hidden">
          {!isMenuOpen ? (
            <button
              onClick={() => setIsMenuOpen(true)}
              className="bg-white/10 backdrop-blur-md border border-white/30 rounded-full p-4 text-white/70 hover:bg-white/20 hover:shadow-lg hover:shadow-white/20 hover:border-white/50 hover:ring-1 hover:ring-white/10 transition-all duration-300"
            >
              <HelpCircle size={24} />
            </button>
          ) : (
            <div className="flex flex-col gap-2 bg-white/10 backdrop-blur-md border border-white/30 rounded-xl p-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleMenuClick(item)}
                    className="group bg-white/10 backdrop-blur-md border border-white/30 rounded-lg px-4 py-3 text-xs text-white/70 hover:text-white/70 hover:bg-white/20 hover:shadow-lg hover:shadow-white/20 hover:border-white/50 hover:ring-1 hover:ring-white/10 transition-all duration-300 flex items-center gap-2 min-w-[140px]"
                  >
                    <Icon size={16} className="group-hover:scale-110 transition-transform text-white/70 group-hover:text-white/70" />
                    <span className="text-white/70 group-hover:text-white/70">{item.label}</span>
                  </button>
                );
              })}
              <button
                onClick={() => setIsMenuOpen(false)}
                className="mt-2 bg-white/10 backdrop-blur-md border border-white/30 rounded-lg px-4 py-2 text-xs text-white/70 hover:bg-white/20 hover:border-white/50 hover:ring-1 hover:ring-white/10 transition-all duration-300"
              >
                Tutup
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && modalContent && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={closeModal}
        >
          <div 
            className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">{modalContent.title}</h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="text-gray-700">
              {modalContent.content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
