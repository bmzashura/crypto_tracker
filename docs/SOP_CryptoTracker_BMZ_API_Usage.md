# CryptoTracker BMZ — REST API Usage Guide

> Detailed API usage dengan curl dan Postman.
> Base URL: `http://127.0.0.1:5050`
> Content-Type: `application/x-www-form-urlencoded` untuk semua POST request.
> Authentication: Session-based (Flask-Login) — cookie `session` diperlukan untuk protected endpoints.

---

## Overview

CryptoTracker BMZ adalah Flask web app, **bukan** REST API tradisional. Semua endpoint mengembalikan HTML templates, bukan JSON. Namun karena Flask routes bisa di-hit dengan curl/Postman, panduan ini mendokumentasikan semua workflow yang mungkin.

**Tipe Authentication:** Session-based (Flask-Login)
- Login → server set cookie `session`
- Semua request authenticated → sertakan cookie dari login
- Cookie expire: browser close atau `logout`

**User Roles:**
- `user` — approve required, bisa akses dashboard, watchlist, profile
- `admin` — full access, bisa approve/reject user, toggle admin, delete user

**Admin Default:** Buat manual di DB atau via Python script.

---

## 1. CoinGecko API (External — No Auth)

App ini menggunakan CoinGecko API (free demo tier) untuk semua data cryptocurrency market.

### Base URL
```
https://api.coingecko.com/api/v3
```

### API Key
Demo key: `CG-your_api_key_here`

### Endpoints yang Digunakan

#### GET /coins/markets
Fetch market data untuk multiple coins.

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `vs_currency` | string | `usd` | Currency |
| `order` | string | `market_cap_desc` | Sort order |
| `per_page` | int | 20 | Results per page (max 250) |
| `page` | int | 1 | Page number |
| `ids` | string | — | Comma-separated coin IDs |
| `sparkline` | bool | `false` | Include sparkline |
| `price_change_percentage` | string | `24h` | Include 24h change |

**Response:** Array of coin objects dengan: `id`, `symbol`, `name`, `image`, `current_price`, `market_cap`, `market_cap_rank`, `total_volume`, `high_24h`, `low_24h`, `price_change_24h`, `price_change_percentage_24h`, `circulating_supply`, `total_supply`, `max_supply`, `ath`, `ath_date`, `atl`, `atl_date`.

---

#### GET /coins/{id}
Fetch detailed info untuk specific coin.

**Parameters:**
| Param | Type | Description |
|---|---|---|
| `localization` | bool | Include localized languages (default: false) |
| `tickers` | bool | Include tickers (default: false) |
| `community_data` | bool | Include community stats (default: false) |
| `developer_data` | bool | Include developer stats (default: false) |

**Response:** Full coin object dengan: `id`, `symbol`, `name`, `image`, `description`, `market_data` (prices, ATH, ATL, market cap, volume, supply), etc.

---

#### GET /coins/{id}/market_chart
Fetch price history untuk chart dan ML prediction.

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `vs_currency` | string | `usd` | Currency |
| `days` | int | 7 | Days of history (1, 7, 14, 30, 90, 180, 365, max) |

**Response:**
```json
{
  "prices": [[timestamp_ms, price], ...],
  "market_caps": [[timestamp_ms, market_cap], ...],
  "total_volumes": [[timestamp_ms, volume], ...]
}
```

---

#### GET /search
Search coins by name atau symbol.

**Parameters:**
| Param | Type | Description |
|---|---|---|
| `query` | string | Search term |

**Response:** `{coins: [{id, name, symbol, thumb, market_cap_rank}, ...]}`

---

#### GET /search/trending
Fetch top 7 trending coins.

**Response:**
```json
{
  "coins": [
    {"item": {"id": "...", "name": "...", "symbol": "...", "thumb": "...", "market_cap_rank": 1, "price_btc": "..."}}
  ]
}
```

---

#### GET /global
Fetch global market statistics.

**Response:**
```json
{
  "data": {
    "total_market_cap": {"usd": 1234567890},
    "total_volume": {"usd": 987654321},
    "active_cryptocurrencies": 12345,
    "market_cap_percentage": {"btc": 52.3}
  }
}
```

---

## 2. Authentication

> ⚠️ **Note:** App ini pakai session-based auth (Flask-Login), bukan JWT. Cookie `session` di-set setelah login dan harus disisipkan di semua request authenticated.

---

### 2.1 Register Akun Baru

```bash
curl -X POST http://127.0.0.1:5050/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=bemis_huntala&email=bemis@email.com&password=L1nux3r&confirm_password=L1nux3r'
```

**Validations:**
- Username: min 3 chars, unique
- Email: valid format, unique
- Password: min 6 chars, must match `confirm_password`

**Behavior:**
- Registrasi berhasil → redirect ke `/login` dengan flash message "Account registered! Awaiting admin approval..."
- Account butuh **admin approval** sebelum bisa login (`is_approved = false` default)
- Error → render register.html dengan flash errors

**Error (400 — duplicate):**
```
Username already taken.
Email already registered.
```

---

### 2.2 Login

```bash
curl -X POST http://127.0.0.1:5050/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d 'username=bemis_huntala&password=L1nux3r'
```

> `-c cookies.txt` → menyimpan session cookie ke file.
> Cookie ini **wajib** untuk semua request authenticated.

**Behavior:**
- Login berhasil + `is_approved = true` → redirect ke `/dashboard`
- Login berhasil + `is_approved = false` → "Account is pending admin approval."
- Error → "Invalid username or password."

**Response (302 redirect — success):**
```
Redirecting to http://127.0.0.1:5050/dashboard
```

**Error (401):**
```
Invalid username or password.
```

---

### 2.3 Logout

```bash
curl -X POST http://127.0.0.1:5050/logout \
  -b cookies.txt
```

**Behavior:**
- Clears Flask-Login session
- Redirects to `/` (index)
- Cookie jadi invalid

---

## 3. Public Endpoints (No Auth Required)

---

### 3.1 Homepage — Coin List

```bash
# Default: page 1, 20 coins
curl -X GET "http://127.0.0.1:5050/"

# Page 2
curl -X GET "http://127.0.0.1:5050/?page=2"

# Search coins
curl -X GET "http://127.0.0.1:5050/?search=bitcoin"
```

**Query Params:**
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `search` | string | — | Search query (triggers search mode, max 20 results) |
| `signal` | string | `ALL` | Filter by ML signal: `ALL`, `STRONG BUY`, `BUY`, `HOLD`, `SELL`, `STRONG SELL` |

**Response:** HTML page dengan coin table.

**Signal Filter (authenticated user, requires computation):**
- Computes `get_price_prediction()` untuk setiap coin
- Coins di-sort by `predicted_change_pct` descending + `r2` descending
- Cache TTL: 1 hour per coin_id

---

### 3.2 Coin Detail Page

```bash
# Default: 7 days chart
curl -X GET "http://127.0.0.1:5050/coin/bitcoin"

# 30 days chart
curl -X GET "http://127.0.0.1:5050/coin/ethereum?days=30"

# 90 days chart
curl -X GET "http://127.0.0.1:5050/coin/solana?days=90"
```

**Path Params:**
| Param | Type | Description |
|---|---|---|
| `coin_id` | string | CoinGecko coin ID (e.g., `bitcoin`, `ethereum`, `solana`) |

**Query Params:**
| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | 7 | Chart range: 7, 30, 90 |

**Response:** HTML page dengan:
- Price chart (Chart.js, 7D/30D/90D range)
- Market stats: current price, 24h change, market cap, volume, ATH, ATL
- **Login required:** 4 ML indicator cards (RSI, SMA, Bollinger, Overall Signal)

---

### 3.3 About Page

```bash
curl -X GET "http://127.0.0.1:5050/about"
```

**Response:** Static HTML page dengan feature list, ML documentation, student info.

---

### 3.4 Theme Toggle

```bash
# Toggle theme
curl -X GET "http://127.0.0.1:5050/theme" \
  -b cookies.txt
```

**Behavior:**
- Toggles session `theme`: `light` ↔ `dark`
- Redirects back to `referer` or `/`

---

## 4. User Endpoints (Login Required)

> Semua endpoint ini memerlukan cookie session dari login.

---

### 4.1 Dashboard

```bash
curl -X GET "http://127.0.0.1:5050/dashboard" \
  -b cookies.txt
```

**Response:** HTML page dengan:
- **Market Overview:** Total market cap, 24h volume, active cryptos, BTC dominance (dari CoinGecko `/global`)
- **Trending Coins:** Top 7 trending (dari CoinGecko `/search/trending`)
- **Watchlist:** Coins yang di-track user + ML prediction per coin (via `get_advanced_prediction()`)

**Watchlist Coin Object (with prediction attached):**
```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "image": "https://...",
  "current_price": 67000.0,
  "price_change_percentage_24h": 2.5,
  "prediction": {
    "overall_signal": "BUY",
    "overall_icon": "trending-up",
    "lr": {
      "signal": "BUY",
      "confidence": "High",
      "predicted_change_pct": 5.2,
      "predicted_price": 70484.0,
      "r2": 0.82,
      "forecast_points": [67100, 67200, ...]
    },
    "rsi": 55.3,
    "sma_7": 66800.0,
    "sma_30": 65500.0,
    "bollinger": {"upper": 68500, "middle": 67000, "lower": 65500}
  }
}
```

---

### 4.2 Add to Watchlist

```bash
curl -X POST "http://127.0.0.1:5050/watchlist/add/bitcoin" \
  -b cookies.txt
```

**Path Params:**
| Param | Description |
|---|---|
| `coin_id` | CoinGecko coin ID |

**Behavior:**
- Jika coin belum ada di watchlist → add → flash success
- Jika sudah ada → no-op
- Redirects to `referer` (previous page) or `/dashboard`

---

### 4.3 Remove from Watchlist

```bash
curl -X POST "http://127.0.0.1:5050/watchlist/remove/bitcoin" \
  -b cookies.txt
```

**Behavior:**
- Jika coin ada di watchlist → delete → flash info
- Jika tidak ada → no-op
- Redirects to `referer` or `/dashboard`

---

### 4.4 View Profile

```bash
curl -X GET "http://127.0.0.1:5050/profile" \
  -b cookies.txt
```

**Response:** HTML form dengan current user data (username, email).

---

### 4.5 Update Profile

```bash
curl -X POST "http://127.0.0.1:5050/profile" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -b cookies.txt \
  -d 'username=bemis_updated&email=bemis_new@email.com'
```

**Validations:**
- Username: min 3 chars, unique
- Email: valid format, unique

**Behavior:**
- Success → flash success → stay on profile page
- Error → render profile.html dengan flash errors

---

### 4.6 View Change Password

```bash
curl -X GET "http://127.0.0.1:5050/change-password" \
  -b cookies.txt
```

**Response:** HTML form dengan fields: current password, new password, confirm password.

---

### 4.7 Change Password

```bash
curl -X POST "http://127.0.0.1:5050/change-password" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -b cookies.txt \
  -d 'current_password=L1nux3r&new_password=L1nux3r_new&confirm_password=L1nux3r_new'
```

**Validations:**
- Current password: must match
- New password: min 6 chars, different from current
- Confirm: must match new password

**Behavior:**
- Success → flash success → redirect to `/dashboard`
- Error → render form dengan flash errors

---

## 5. Admin Endpoints (Admin Role Required)

> Semua endpoint admin memerlukan `is_admin = True` di user record.

---

### 5.1 Admin Dashboard

```bash
curl -X GET "http://127.0.0.1:5050/admin" \
  -b cookies.txt
```

**Response (200):**
```html
<!-- HTML page with: -->
<!-- - pending_users: list of unapproved accounts -->
<!-- - approved_users: list of approved accounts (limit 50, ordered by created_at desc) -->
```

**Error (non-admin — 302):**
```
Access denied. Admin only.
```

---

### 5.2 Approve User

```bash
curl -X POST "http://127.0.0.1:5050/admin/approve/5" \
  -b cookies.txt
```

**Path Params:**
| Param | Description |
|---|---|
| `user_id` | ID of user to approve |

**Behavior:**
- Sets `is_approved = True` for the user
- User bisa login setelah diapprove
- Redirects to `/admin`

---

### 5.3 Reject User

```bash
curl -X POST "http://127.0.0.1:5050/admin/reject/5" \
  -b cookies.txt
```

**Behavior:**
- Deletes the user record from DB
- Watchlist entries untuk user juga di-delete (cascade)
- Redirects to `/admin`

---

### 5.4 Toggle Admin Status

```bash
curl -X POST "http://127.0.0.1:5050/admin/toggle-admin/5" \
  -b cookies.txt
```

**Behavior:**
- Toggle `is_admin` True ↔ False
- Cannot change own admin status → flash error
- Redirects to `/admin`

---

### 5.5 Delete User

```bash
curl -X POST "http://127.0.0.1:5050/admin/delete-user/5" \
  -b cookies.txt
```

**Behavior:**
- Deletes user + their watchlist entries
- Cannot delete yourself → flash error
- Redirects to `/admin`

---

## 6. ML Prediction Reference

### 6.1 Linear Regression — `get_price_prediction()`

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `coin_id` | string | — | CoinGecko coin ID |
| `fetch_func` | function | — | `fetch_price_history` |
| `days_history` | int | 30 | Training window |
| `days_ahead` | int | 7 | Forecast horizon |

**Returns:**
```python
{
    'signal': 'BUY',           # STRONG BUY | BUY | HOLD | SELL | STRONG SELL
    'signal_icon': 'trending-up',
    'confidence': 'High',       # High (R²>0.7) | Medium (R²>0.4) | Low
    'predicted_change_pct': 5.2,
    'current_price': 67000.0,
    'predicted_price': 70484.0,
    'slope': 0.32,             # slope ratio (% per day)
    'r2': 0.82,                # R² score
    'forecast_points': [67100, 67200, ...],  # for chart overlay
    'forecast_labels': ['+1d', '+2d', ...]
}
```

**Signal Logic:**
| Slope Ratio | Signal |
|---|---|
| `> 0.5` | STRONG BUY |
| `0.1 - 0.5` | BUY |
| `-0.1 - 0.1` | HOLD |
| `-0.5 - -0.1` | SELL |
| `< -0.5` | STRONG SELL |

---

### 6.2 RSI — `calculate_rsi()`

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `prices` | list[float] | — | List of price values |
| `period` | int | 14 | RSI period |

**Returns:** float 0-100

| Value | Status |
|---|---|
| `> 70` | Overbought (sell signal) |
| `< 30` | Oversold (buy signal) |
| `30-70` | Neutral |

---

### 6.3 SMA — `calculate_sma()`

**Parameters:**
| Param | Type | Description |
|---|---|---|
| `prices` | list[float] | Price values |
| `period` | int | SMA period (e.g., 7, 30) |

**SMA Crossover Signal:**
| Condition | Signal |
|---|---|
| SMA-7 > SMA-30 + 1% | BULLISH |
| SMA-7 < SMA-30 - 1% | BEARISH |
| Within ±1% | NEUTRAL |

---

### 6.4 Bollinger Bands — `calculate_bollinger()`

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `prices` | list[float] | — | Price values |
| `period` | int | 20 | Moving average period |
| `num_std` | int | 2 | Standard deviation multiplier |

**Returns:**
```python
{
    'upper': 68500.0,
    'middle': 67000.0,
    'lower': 65500.0,
    'bandwidth': 4.48,  # % bandwidth
    'position': 'Above Middle (mild buy signal)'
}
```

**Position Analysis:**
| Price Position | Interpretation |
|---|---|
| Above Upper Band | Strong Buy (overbought breakout) |
| Above Middle | Mild Buy |
| Below Middle | Mild Sell |
| Below Lower Band | Strong Sell (oversold breakdown) |

---

### 6.5 Advanced Prediction — `get_advanced_prediction()`

Combines: Linear Regression + RSI + SMA + Bollinger Bands.

**Returns:**
```python
{
    'lr': { /* Linear Regression result */ },
    'rsi': 55.3,                   # float or None
    'rsi_status': 'Neutral',
    'sma_7': 66800.0,
    'sma_30': 65500.0,
    'sma_diff_pct': 1.98,
    'sma_signal': 'BULLISH',
    'bollinger': { /* Bollinger result */ },
    'overall_signal': 'BUY',       # Combined BUY/SELL/HOLD
    'overall_icon': 'trending-up',
    'prices': [...],               # last 30 prices
    'timestamps': [...]           # last 30 timestamps
}
```

**Overall Signal Logic (7-day forecast):**
| Predicted Change | R² | Signal |
|---|---|---|
| `> +10%` | `> 0.3` | STRONG BUY |
| `+5% to +10%` | `> 0.3` | BUY |
| `-5% to +5%` | any | HOLD |
| `-10% to -5%` | `> 0.3` | SELL |
| `< -10%` | `> 0.3` | STRONG SELL |
| any | `< 0.3` | HOLD (low confidence) |

---

## 7. Database Models

### User
| Field | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(256) | NOT NULL (pbkdf2:sha256) |
| `is_admin` | BOOLEAN | DEFAULT FALSE |
| `is_approved` | BOOLEAN | DEFAULT FALSE |
| `created_at` | DATETIME | DEFAULT `func.now()` |

### Watchlist
| Field | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | FOREIGN KEY → `user.id` |
| `coin_id` | VARCHAR(100) | NOT NULL |

---

## 8. Error Codes

| HTTP Code | Arti | Contoh |
|---|---|---|
| `200` | OK | Page rendered |
| `302` | Found | Redirect (login success, form submission) |
| `400` | Bad Request | Validation error (registrasi gagal) |
| `401` | Unauthorized | Session expired / not logged in |
| `403` | Forbidden | Non-admin mencoba akses admin route |
| `404` | Not Found | Coin ID tidak ditemukan |
| `500` | Server Error | CoinGecko API timeout, DB error |

---

## 9. Postman Setup

### 9.1 Environment Variables

Buat environment baru di Postman:

| Variable | Initial Value |
|---|---|
| `base_url` | `http://127.0.0.1:5050` |
| `session_cookie` | (kosong, akan di-set dari login) |

### 9.2 Collection: Authentication

**Request 1 — Register (POST {{base_url}}/register)**
- Body (x-www-form-urlencoded):
  ```
  username=bemis_huntala&email=bemis@email.com&password=L1nux3r&confirm_password=L1nux3r
  ```
- Tests tab: (kosongkan, redirect only)

**Request 2 — Login (POST {{base_url}}/login)**
- Body (x-www-form-urlencoded):
  ```
  username=bemis_huntala&password=L1nux3r
  ```
- Tests tab:
  ```javascript
  var cookie = pm.response.headers.get('Set-Cookie');
  if (cookie) {
      var sessionCookie = cookie.split(';')[0];
      pm.environment.set('session_cookie', sessionCookie);
  }
  ```

**Request 3 — Dashboard (GET {{base_url}}/dashboard)**
- Headers: `Cookie: {{session_cookie}}`

**Request 4 — Logout (POST {{base_url}}/logout)**
- Headers: `Cookie: {{session_cookie}}`

### 9.3 Collection: User Flow

1. Register → POST `/register`
2. **Admin approval** → (manual via DB atau admin dashboard)
3. Login → POST `/login` (simpan cookie)
4. Dashboard → GET `/dashboard`
5. Add to Watchlist → POST `/watchlist/add/bitcoin`
6. View Coin Detail → GET `/coin/bitcoin?days=30`
7. Profile → GET `/profile`
8. Change Password → POST `/change-password`
9. Logout → POST `/logout`

### 9.4 Collection: Admin Flow

1. Login dengan admin account
2. Admin Dashboard → GET `/admin`
3. Approve User → POST `/admin/approve/{user_id}`
4. Reject User → POST `/admin/reject/{user_id}`
5. Toggle Admin → POST `/admin/toggle-admin/{user_id}`
6. Delete User → POST `/admin/delete-user/{user_id}`

### 9.5 Collection: Public Flow

1. Homepage → GET `/`
2. Search → GET `/?search=solana`
3. Coin Detail → GET `/coin/ethereum?days=90`
4. About → GET `/about`
5. Theme Toggle → GET `/theme`

---

## 10. Session-Based Auth vs JWT

> ⚠️ **Perbedaan penting** dengan Koneksaun Saudavel API:

| Aspek | CryptoTracker BMZ | Koneksaun Saudavel |
|---|---|---|
| Auth Type | Session-based (Flask-Login) | JWT Token-based |
| Cookie | `session` (HTTP-only) | `Authorization: Bearer <token>` |
| Login Persists | Until logout / browser close | Until token expire |
| Storage | Server-side (Flask signed cookie) | Client-side (localStorage) |
| CSRF | SESSION_COOKIE_SAMESITE='Lax' | JWT di body/header |

Untuk programmatic access (script/curl), session cookie cara paling reliable:
```bash
# Step 1: Login + save cookie
curl -X POST http://127.0.0.1:5050/login \
  -d 'username=admin&password=YourPass' -c cookies.txt

# Step 2: Use cookie for authenticated requests
curl -X GET http://127.0.0.1:5050/dashboard -b cookies.txt
curl -X POST http://127.0.0.1:5050/watchlist/add/bitcoin -b cookies.txt
```

---

## 11. Security Notes

- Password hashing: `pbkdf2:sha256` (LibreSSL compatible)
- Session cookie: `HTTPOnly`, `SameSite=Lax`
- New user: `is_approved = false` (must be approved by admin before login)
- Admin check: `is_admin = True` required for admin routes
- SESSION_COOKIE_SAMESITE='Lax' — works for most cases, occasional 403 on cross-site POST
- No rate limiting pada app ini — CoinGecko free tier sendiri yang rate-limited (~10-30 req/min)

---

## 12. Run & Deploy

```bash
# Local run
cd /Users/ashura/projects/crypto_tracker
python3 app.py

# App runs on http://127.0.0.1:5050
# (port 5000 occupied by macOS AirPlay Receiver)

# Production considerations:
# - Set SECRET_KEY environment variable
# - Set COINGECKO_API_KEY for higher rate limits
# - Use gunicorn/uwsgi instead of Flask debug server
# - Add rate limiting (Flask-Limiter)
# - Use HTTPS in production
```

---

## Tags

#crypto-tracker #flask #api #curl #postman #rest-api #coingecko #ml #prediction #rsi #sma #bollinger
