/**
 * Midtrans payment service
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const MIDTRANS_CLIENT_KEY = process.env.NEXT_PUBLIC_MIDTRANS_CLIENT_KEY || '';
const MIDTRANS_IS_PRODUCTION = (process.env.NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION || 'false').toLowerCase() === 'true';

export interface CoinPackage {
  id: string;
  name: string;
  coins: number;
  price: number;
  description: string;
}

export const COIN_PACKAGES: CoinPackage[] = [
  {
    id: 'package-10k',
    name: 'Rp 10.000',
    coins: 300,
    price: 10000,
    description: 'Paket hemat pemula dan tester'
  },
  {
    id: 'package-50k',
    name: 'Rp 50.000',
    coins: 1500,
    price: 50000,
    description: 'Buat kaum rebahan yang mau dapat cuan'
  },
  {
    id: 'package-100k',
    name: 'Rp 100.000',
    coins: 3200,
    price: 100000,
    description: 'Buat yang gak mau ribet'
  },
  {
    id: 'package-150k',
    name: 'Rp 150.000',
    coins: 5000,
    price: 150000,
    description: 'Level up orang sat-set'
  },
  {
    id: 'package-200k',
    name: 'Rp 200.000',
    coins: 6800,
    price: 200000,
    description: 'Bukan kaum mendang-mending '
  },
  {
    id: 'package-250k',
    name: 'Rp 250.000',
    coins: 8850,
    price: 250000,
    description: 'Sultan nih bos, senggol dong'
  }
];

export const midtransService = {
  /**
   * Initialize Midtrans Snap
   */
  async initializeSnap(packageId: string, userId: string, token: string): Promise<string> {
    const packageData = COIN_PACKAGES.find(p => p.id === packageId);
    if (!packageData) {
      throw new Error('Package not found');
    }

    // Create order ID
    const orderId = `coins-${userId}-${Date.now()}`;

    // Call backend to create Midtrans transaction
    // Note: In production, this should be done server-side for security
    const response = await fetch(`${API_URL}/api/midtrans/create-transaction`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        package_id: packageId,
        order_id: orderId,
        gross_amount: packageData.price,
        user_id: userId
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create transaction' }));
      throw new Error(error.detail || 'Failed to create transaction');
    }

    const { snap_token } = await response.json();
    return snap_token;
  },

  /**
   * Load Midtrans Snap script
   */
  loadSnapScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (document.getElementById('midtrans-snap-script')) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.id = 'midtrans-snap-script';
      script.src = MIDTRANS_IS_PRODUCTION
        ? 'https://app.midtrans.com/snap/snap.js'
        : 'https://app.sandbox.midtrans.com/snap/snap.js';
      script.setAttribute('data-client-key', MIDTRANS_CLIENT_KEY);
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Midtrans Snap script'));
      document.body.appendChild(script);
    });
  }
  ,
  async initializeSubscriptionSnap(token: string, days: number = 30): Promise<string> {
    const response = await fetch(`${API_URL}/api/billing/checkout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        plan_id: 'pro_monthly',
        days
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create subscription' }));
      throw new Error(error.detail || 'Failed to create subscription');
    }

    const { snap_token } = await response.json();
    return snap_token;
  }
};

