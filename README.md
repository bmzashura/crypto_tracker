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

## Cara Menjalankan Aplikasi

### Tahapan Lengkap

#### 1. Persiapan Lingkungan

```bash
# Pastikan Python 3.9+ terinstall
python3 --version
```

#### 2. Clone Repository

```bash
git clone https://github.com/bmzashura/crypto_tracker.git
cd crypto_tracker
```

#### 3. Buat Virtual Environment (Opsional tapi Disarankan)

```bash
# Membuat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows (CMD)
# venv\Scripts\Activate.ps1    # Windows (PowerShell)

# Jika menggunakan zsh/bash di macOS, aktifkan dengan:
# source venv/bin/activate
```

#### 4. Install Dependencies

```bash
# Upgrade pip terlebih dahulu (opsional)
pip3 install --upgrade pip

# Install semua dependencies dari requirements.txt
pip3 install -r requirements.txt
```

**Daftar dependencies** (`requirements.txt`):
| Package | Fungsi |
|---|---|
| `flask` | Web framework |
| `flask-sqlalchemy` | ORM database |
| `flask-login` | Session-based authentication |
| `werkzeug` | Password hashing |
| `requests` | HTTP client untuk CoinGecko API |
| `numpy` | Komputasi numerik untuk ML |
| `scikit-learn` | Machine Learning (LinearRegression, RSI, SMA, Bollinger) |

#### 5. Jalankan Aplikasi

```bash
# Jalankan Flask app
python3 app.py
```

**Output yang diharapkan:**
```
Starting CryptoTracker Flask App...
API Key: CG-aop5s5...
Database initialized.
 * Running on http://127.0.0.1:5050/
```

#### 6. Akses Aplikasi

Buka browser dan navigasi ke:
```
http://127.0.0.1:5050
```

**Halaman yang tersedia:**
| URL | Deskripsi |
|---|---|
| `/` | Homepage — daftar harga koin |
| `/login` | Halaman login |
| `/register` | Halaman registrasi |
| `/dashboard` | Dashboard user (login required) |
| `/profile` | Edit profil (login required) |
| `/change-password` | Ganti password (login required) |
| `/admin` | Panel admin (admin only) |
| `/about` | About + dokumentasi ML |
| `/coin/<coin_id>` | Detail koin + chart + ML |

#### 7. Login dengan Akun Default

Buka `http://127.0.0.1:5050/login` dan gunakan kredensial berikut:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin1234` |
| User | `reporter_test` | `ReportTest123` |

> **Catatan Penting:** Akun baru yang register memerlukan approval dari admin sebelum bisa login. Login sebagai admin dulu, lalu approve user baru di `/admin`.

#### 8. Menghentikan Aplikasi

```bash
# Tekan Ctrl+C di terminal yang menjalankan Flask

# Atau jika di background:
pkill -f "python3 app.py"
```

#### 9. Troubleshooting

**Port 5050 sudah digunakan?**
```bash
# Cari proses yang menggunakan port 5050
lsof -ti:5050

# Kill proses tersebut
kill -9 <PID>

# Atau ganti port di app.py baris terakhir:
# app.run(debug=True, port=5051)
```

**Error "No module named flask"?**
```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Install ulang dependencies
pip3 install -r requirements.txt
```

**CoinGecko API rate limit?**
- App menggunakan in-memory cache (TTL 5 menit) untuk menghindari rate limit
- Demo tier CoinGecko: ~10-30 request/menit
- Jika limit tercapai, tunggu beberapa menit dan refresh halaman

**Database error?**
```bash
# Hapus database lama dan biarkan app membuat yang baru
rm instance/users.db
python3 app.py
```

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
| Admin | `admin` | `Admin1234` | Approved — Full access (dashboard + admin panel) |
| User | `reporter_test` | `ReportTest123` | Approved — Dashboard + watchlist |

> **Catatan:** Akun `admin` dibuat langsung via SQL insert (tanpa registrasi) sehingga `created_at = NULL`. Error page fix sudah diterapkan untuk menangani case ini.

### Alur Registrasi Normal
1. User register di `/register` → akun berstatus `is_approved=False`
2. User belum bisa login sampai admin approve di `/admin`
3. Admin login → ke `/admin` → klik **Approve** pada user yang pending
4. User sekarang bisa login dengan kredensial yang sudah didaftarkan

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
