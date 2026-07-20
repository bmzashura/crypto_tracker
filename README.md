# CryptoTracker BMZ

Aplikasi pelacak harga cryptocurrency berbasis Flask dengan fitur Machine Learning untuk prediksi harga dan sistem autentikasi pengguna.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Fitur

### Fitur Utama
- **Harga Real-Time** — Data harga cryptocurrency dari [CoinGecko API](https://www.coingecko.com/en/api) (demo tier, tanpa API key)
- **Visualisasi Chart** — Grafik interaktif 7/30/90 hari menggunakan Chart.js
- **Prediksi Machine Learning** — Prediksi harga 7 hari ke depan menggunakan Linear Regression + RSI + SMA + Bollinger Bands
- **Watchlist Personal** — Simpan koin favorit untuk dilacak per user
- **Dark/Light Mode** — Tema otomatis mengikuti preferensi session
- **Autentikasi** — Register, Login, Logout dengan password hashing PBKDF2-SHA256
- **Admin Panel** — CRUD lengkap untuk manajemen user (Create, Read, Update, Delete)
- **Halaman Error Kustom** — Error page untuk 404, 403, 405, 500 dengan desain konsisten

### Screenshots
Lihat folder `docs/` untuk dokumentasi lengkap.

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Flask 3.0+ |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | Flask-Login (session-based) |
| ML | scikit-learn (LinearRegression, RSI, SMA, Bollinger Bands) |
| Visualisasi | Chart.js 4.4 |
| Frontend | Jinja2 Templates + Vanilla JS |
| Icons | Lucide Icons |
| Font | IBM Plex Sans |
| API | CoinGecko (demo tier) |

---

## Cara Instalasi

### Prasyarat
- Python 3.9+
- pip3

### Langkah

```bash
# 1. Clone repository
git clone https://github.com/bmzashura/crypto_tracker.git
cd crypto_tracker

# 2. Buat virtual environment (opsional tapi disarankan)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate     # Windows

# 3. Install dependencies
pip3 install -r requirements.txt

# 4. Jalankan aplikasi
python3 app.py
```

Aplikasi akan berjalan di `http://127.0.0.1:5050`

> **Catatan:** Port 5050 digunakan karena port default Flask (5000) sering dipakai macOS AirPlay Receiver.

---

## Struktur Direktori

```
crypto_tracker/
├── app.py              # Flask app — routes, auth, API calls
├── ml_model.py         # ML: LinearRegression, RSI, SMA, Bollinger Bands
├── requirements.txt    # Python dependencies
├── instance/
│   └── users.db        # SQLite database (auto-created)
├── static/
│   └── css/
│       └── style.css   # Design system (light + dark theme)
└── templates/
    ├── base.html       # Base template (navbar, footer, theme toggle)
    ├── index.html      # Homepage — daftar koin
    ├── detail.html     # Detail koin + chart + ML indicators
    ├── dashboard.html  # Dashboard — watchlist, market overview
    ├── profile.html    # Edit profil user
    ├── admin.html      # Admin panel — manajemen user
    ├── admin_edit.html # Form edit user
    ├── login.html      # Halaman login
    ├── register.html   # Halaman registrasi
    ├── about.html       # About + dokumentasi ML
    └── error.html      # Custom error pages
```

---

## Kredensial Default

| Role | Username | Password | Status |
|---|---|---|---|
| Admin | `admin` | `Admin1234` | Approved |
| User | `reporter_test` | `ReportTest123` | Approved |

> **Catatan:** Akun `admin` dibuat langsung via SQL insert (tanpa registrasi) sehingga `created_at = NULL`. Error page fix sudah diterapkan untuk menangani case ini.

---

## Dokumentasi ML

Dokumentasi lengkap algoritma Machine Learning tersedia di:
- `docs/ML_PREDICTION.md` — Mekanisme prediksi Linear Regression
- `docs/API_DOCUMENTATION.md` — Dokumentasi API internal dan CoinGecko endpoints
- `docs/SOP_CryptoTracker_BMZ_API_Usage.md` — Panduan penggunaan API

### Indikator ML

1. **Linear Regression** — Prediksi harga 7 hari ke depan berdasarkan data 30 hari terakhir. Signal: STRONG BUY / BUY / HOLD / SELL / STRONG SELL.
2. **RSI (Relative Strength Index)** — Momentum oscillator (0-100). RSI > 70 = Overbought, RSI < 30 = Oversold.
3. **SMA Crossover** — SMA-7 vs SMA-30. SMA-7 > SMA-30 + 1% = BULLISH, SMA-7 < SMA-30 - 1% = BEARISH.
4. **Bollinger Bands** — Upper/Lower band berdasarkan volatilitas. Price > upper = strong buy signal.
5. **Overall Signal** — Kombinasi semua indikator di atas.

---

## API Endpoints CoinGecko

| Endpoint | Fungsi |
|---|---|
| `GET /coins/markets` | Daftar koin dengan market data |
| `GET /coins/{id}` | Detail satu koin |
| `GET /coins/{id}/market_chart` | Data harga historical |
| `GET /search` | Pencarian koin |
| `GET /search/trending` | Koin trending |
| `GET /global` | Statistik pasar global |

---

## Lisensi

MIT License — Bemis Huntala, NIM 1002240018, ITTS 2026
