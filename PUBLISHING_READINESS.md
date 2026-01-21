## Publishing Readiness Notes

This project is ready for production payments only after the items below are set.

### Coin Packages (Production)
- Rp 10.000 = 300 coins
- Rp 50.000 = 1.500 coins
- Rp 100.000 = 3.200 coins
- Rp 150.000 = 5.000 coins
- Rp 200.000 = 6.800 coins
- Rp 250.000 = 8.850 coins

Backend uses a fixed package map for Midtrans (`MIDTRANS_COIN_PACKAGES`). Webhook credits coins by matching `gross_amount` to this map.

### Midtrans Environment
- `MIDTRANS_SERVER_KEY` must be set on the backend.
- `MIDTRANS_CLIENT_KEY` must be set on the backend.
- `MIDTRANS_IS_PRODUCTION=true` to call Midtrans production API.
- Frontend must set `NEXT_PUBLIC_MIDTRANS_CLIENT_KEY`.
- Frontend must set `NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION=true` to load production Snap JS.

### Webhook Security
- Webhook now verifies Midtrans `signature_key`.
- If the signature is missing or invalid, coins are not added.
- Ensure the Midtrans webhook URL points to `/api/webhook/midtrans`.

### Admin Config Check
- Admin endpoint: `GET /api/admin/midtrans/status`
- Returns environment readiness + package mapping.

### Supabase Transaction Logs
- Webhook inserts a record into `midtrans_transactions`.
- Expected columns:
  - `user_id` (text)
  - `order_id` (text)
  - `package_id` (text, nullable)
  - `gross_amount` (int)
  - `coins_added` (int)
  - `transaction_status` (text)
  - `payment_type` (text, nullable)
  - `fraud_status` (text, nullable)
  - `midtrans_signature` (text, nullable)
  - `raw_payload` (jsonb)
  - `created_at` (timestamp, default now)

### Coins Deduction Rules
- Image batch generation costs 75 coins.
- Pro Video generation costs 185 coins.
- Auto-post video upload costs 90 coins.
- Coins are deducted only after a successful generation.

### Quick Checklist Before Publish
- Midtrans keys are production keys.
- `NEXT_PUBLIC_MIDTRANS_IS_PRODUCTION=true`.
- Webhook URL configured in Midtrans dashboard.
- Coins match the package mapping in backend.
