'use client';

import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { enrollIdentity } from '../../../../lib/identityApi';
import { supabaseService } from '../../../../services/supabaseService';

export default function AvatarEnrollPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [consent, setConsent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFilesChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files ? Array.from(event.target.files) : [];
    setFiles(selected);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (files.length < 5 || files.length > 10) {
      setError('Upload 5–10 selfie untuk hasil terbaik.');
      return;
    }
    if (!consent) {
      setError('Kamu harus menyetujui consent terlebih dahulu.');
      return;
    }

    try {
      setIsSubmitting(true);
      const token = await supabaseService.getAccessToken();
      const formData = new FormData();
      files.forEach((file) => formData.append('images[]', file));
      await enrollIdentity(formData, token || undefined);
      router.push('/app');
    } catch (err: any) {
      setError(typeof err?.message === 'string' ? err.message : 'Gagal enroll avatar.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-12">
      <h1 className="text-2xl font-bold text-gray-900">Buat Avatar</h1>
      <p className="mt-2 text-sm text-gray-600">
        Upload 5–10 selfie dengan pencahayaan yang jelas dan wajah menghadap kamera.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-5">
          <label className="block text-sm font-semibold text-gray-800">
            Upload selfie
          </label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleFilesChange}
            className="mt-3 block w-full text-sm text-gray-700"
          />
          <p className="mt-2 text-xs text-gray-500">
            File terpilih: {files.length}
          </p>
        </div>

        <label className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-1"
          />
          <span>
            Saya setuju menggunakan foto wajah untuk pembuatan avatar konsisten.
          </span>
        </label>

        {error && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-xs text-red-600">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!consent || isSubmitting}
          className="w-full rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:bg-gray-400"
        >
          {isSubmitting ? 'Memproses…' : 'Submit Enrollment'}
        </button>
      </form>
    </div>
  );
}
