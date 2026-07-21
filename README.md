# CryptoTracker BMZ

Aplikasi pelacak harga cryptocurrency berbasis Flask dengan fitur Machine Learning untuk prediksi harga dan sistem autentikasi pengguna.

> **Nama:** Bemis Huntala | **NIM:** 1002240018 | **ITTS 2026**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## About

CryptoTracker BMZ adalah aplikasi web untuk melacak harga cryptocurrency secara real-time menggunakan data dari [CoinGecko API](https://www.coingecko.com/en/api). Aplikasi ini dilengkapi dengan fitur Machine Learning untuk prediksi harga jangka pendek dan sistem autentikasi pengguna dengan role (admin/user).

### Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Flask 3.0+ |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | Flask-Login (session-based) + PBKDF2-SHA256 |
| ML | scikit-learn (LinearRegression, RSI, SMA, Bollinger Bands) |
| API | CoinGecko (free tier + multi-key fallback) |
| Visualisasi | Chart.js 4.4 |
| Frontend | Jinja2 Templates + Vanilla JS |
| Icons | Lucide Icons |

---

## Features

### Core Features
- **Harga Real-Time** — Data harga dari CoinGecko API dengan cache 2 menit
- **Market Overview** — Statistik pasar global (total market cap, volume, BTC dominance)
- **Visualisasi Chart** — Grafik interaktif 7/30/90 hari menggunakan Chart.js
- **Prediksi Machine Learning** — Prediksi 7 hari ke depan:
  - Linear Regression + R² confidence score
  - RSI (Relative Strength Index)
  - SMA Crossover (SMA-7 vs SMA-30)
  - Bollinger Bands (upper/middle/lower)
  - Overall Signal (STRONG BUY / BUY / HOLD / SELL / STRONG SELL)
- **Watchlist Personal** — Simpan koin favorit (login required)
- **Dark/Light Mode** — Toggle tema, persist di session
- **Trending Coins** — 7 koin trending dari CoinGecko

### Authentication & Authorization
- Register dengan approval admin (pending user system)
- Login/Logout dengan password hashing PBKDF2-SHA256
- Role-based access: Admin vs Regular User
- Password change & profile edit

### Admin Panel
- **User Management** — Create, Read, Update, Delete user
- **Pending Approval** — Approve/reject user registrations
- **Toggle Admin** — Promote/demote user jadi admin
- **API Key Management** — Konfigurasi API key via file `.env`

### Multi-Key Fallback System
- Mendukung multiple API key CoinGecko
- Otomatis switch ke key berikutnya saat rate-limited
- Konfigurasi API key via file `.env`
- Fallback message jika semua key rate-limited

---

## Installation & Setup

### Prerequisites

- Python 3.9+
- Internet connection (untuk CoinGecko API)
- macOS/Linux/Windows

### Steps

```bash
# 1. Clone repository
git clone https://github.com/bmzashura/crypto_tracker.git
cd crypto_tracker

# 2. Buat virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 4. Setup environment variable (API key)
# Buat file .env di root folder:
cp .env.example .env
# Edit .env dan isi SECRET_KEY dan COINGECKO_API_KEY

# 5. Buat folder instance (untuk SQLite database)
mkdir -p instance

# 6. Jalankan aplikasi
python3 app.py
# Atau dengan dotenv:
source .env && python3 app.py
```

**File `.env` yang diperlukan:**

```env
SECRET_KEY=ubah_dengan_secret_key_random_kamu
COINGECKO_API_KEY=CG-your_api_key_di_sini
COINGECKO_API_KEY_2=                # opsional, key kedua untuk fallback
MARKET_CACHE_TTL=120
API_TIMEOUT=10
```

> **Catatan:** Dapatkan API key gratis di [coingecko.com](https://www.coingecko.com). Free tier: 30 requests/menit.

**Output yang diharapkan:**

```
Starting CryptoTracker Flask App...
API Key loaded: CG-aop...
Database initialized.
 * Running on http://127.0.0.1:5050/
```

### Default Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin1234` |
| User | `reporter_test` | `ReportTest123` |

> Akun baru yang register memerlukan approval dari admin sebelum bisa login.

### Access URLs

| URL | Deskripsi |
|---|---|
| `/` | Landing page — global stats + CTA |
| `/market` | Daftar lengkap semua koin (paginated) |
| `/coin/<id>` | Detail koin + chart + ML prediction |
| `/dashboard` | Watchlist + trending + market overview |
| `/about` | About + dokumentasi ML |
| `/login` | Login |
| `/register` | Registrasi |
| `/admin` | Admin panel (admin only) |


---

## Project Structure

```
crypto_tracker/
├── app.py                      # Flask app — routes, auth, API calls
├── config.py                   # Flask config + COINGECKO_API_KEYS list
├── ml_model.py                 # ML: LinearRegression, RSI, SMA, Bollinger Bands
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (gitignored)
├── docs/                       # Dokumentasi tambahan
│   ├── ML_PREDICTION.md
│   └── API_DOCUMENTATION.md
├── instance/
│   └── users.db               # SQLite database (auto-created)
├── services/
│   ├── __init__.py
│   ├── cache_service.py       # In-memory cache dengan TTL
│   └── coingecko_service.py   # CoinGecko API wrapper + multi-key fallback
├── static/
│   └── css/
│       └── style.css          # Design system (light + dark theme)
└── templates/
    ├── base.html               # Base template (navbar, footer, flash messages)
    ├── index.html              # Landing page — global stats + CTA
    ├── market.html             # Full coin list dengan search & sort
    ├── detail.html             # Coin detail + chart + ML indicators
    ├── dashboard.html          # Watchlist + trending + market overview
    ├── profile.html            # Edit profil user
    ├── change_password.html    # Ganti password
    ├── admin.html              # Admin panel — user management
    ├── admin_edit.html         # Form edit user
    ├── login.html              # Login page
    ├── register.html           # Registrasi page
    ├── about.html              # About + ML documentation
    └── error.html              # Custom error pages (404, 403, 405, 500)
```

### Services Architecture

```
services/
├── cache_service.py
│   └── In-memory cache dengan TTL per endpoint.
│       Mengurangi CoinGecko API calls dan rate limit.
│
└── coingecko_service.py
    ├── fetch_coins()          # /coins/markets
    ├── fetch_coin_detail()    # /coins/{id}
    ├── fetch_price_history()  # /coins/{id}/market_chart
    ├── fetch_market_by_ids()  # /coins/markets (by ids)
    ├── fetch_search()          # /search
    ├── fetch_trending()        # /search/trending
    ├── fetch_global_stats()    # /global
    │
    └── _get_with_fallback()   # Internal: coba semua keys sampai success
```

---

## ML Prediction Documentation

### Algorithm: Linear Regression

1. Ambil 30 hari data harga historis
2. Train LinearRegression model (X = day index, y = price)
3. Predict 7 hari ke depan
4. Calculate R² score untuk confidence

### Signal Classification

| Signal | Condition |
|---|---|
| **STRONG BUY** | predicted_change > 10% AND R² > 0.7 |
| **BUY** | predicted_change > 5% AND R² > 0.5 |
| **HOLD** | -5% <= predicted_change <= 5% |
| **SELL** | predicted_change < -5% AND R² > 0.5 |
| **STRONG SELL** | predicted_change < -10% AND R² > 0.7 |

### Technical Indicators

| Indicator | Description |
|---|---|
| **RSI** | 0-100, overbought > 70, oversold < 30 |
| **SMA Crossover** | SMA-7 vs SMA-30, bullish/bearish crossover |
| **Bollinger Bands** | Upper/middle/lower band berdasarkan 20-day std dev |

---

## Troubleshooting

**Port 5050 sudah digunakan?**
```bash
lsof -ti:5050
kill -9 <PID>
```

**CoinGecko rate limit?**
- Cache TTL 120 detik — tunggu sebentar lalu refresh
- Semua key rate-limited → tunggu 1 menit

**Database error?**
```bash
rm instance/users.db
python3 app.py
```

**Import error "No module named"?**
```bash
source venv/bin/activate
pip3 install -r requirements.txt
```

---

## License

MIT License — Bemis Huntala, NIM 1002240018, ITTS 2026
