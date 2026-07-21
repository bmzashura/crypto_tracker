# UAS Documentation — CryptoTracker BMZ

## 1. Identitas Kelompok

| Field | Isi |
|---|---|
| **Nama Aplikasi** | CryptoTracker BMZ |
| **Kategori** | Web Application — Backend Programming |
| **Anggota 1** | [Nama Lengkap] / [NIM] |
| **Anggota 2** | [Nama Lengkap] / [NIM] |
| **Dosen** | [Nama Dosen] |
| **Mata Kuliah** | Pemrograman Backend |
| **Institusi** | Institut Teknologi-Telunikasi Sains (ITTS) |

---

## 2. Latar Belakang

Pasar cryptocurrency merupakan salah satu aset digital yang paling volatile dan menarik untuk dianalisis. Tingginya frekuensi perubahan harga membuat investor dan pengamat memerlukan alat bantu untuk memantau pergerakan harga secara real-time.

CryptoTracker BMZ hadir sebagai aplikasi web yang memberikan informasi pasar cryptocurrency secara langsung melalui integrasi dengan CoinGecko Public API. Aplikasi ini dirancang untuk memenuhi kebutuhan UAS mata kuliah Pemrograman Backend dengan mengimplementasikan seluruh konsep dasar development web modern: routing, templating, autentikasi, otorisasi, validasi input, error handling, caching, serta dokumentasi API.

---

## 3. Tujuan

1. Mengimplementasikan aplikasi web full-stack dengan Flask sebagai backend framework.
2. Mengintegrasikan public API CoinGecko untuk mengambil data cryptocurrency secara real-time.
3. Menerapkan sistem autentikasi dan otorisasi dengan Flask-Login.
4. Menggunakan SQLite sebagai database relasional dengan SQLAlchemy ORM.
5. Membuat struktur proyek yang modular dan mudah dipelihara.
6. Menampilkan hasil analisis teknikal (RSI, SMA, Bollinger Bands) dan proyeksi tren menggunakan Machine Learning (Linear Regression).
7. Mendemonstrasikan kemampuan deployment dan dokumentasi proyek perangkat lunak.

---

## 4. Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.9+, Flask 3.0+ |
| **ORM** | Flask-SQLAlchemy |
| **Auth** | Flask-Login, Flask-WTF (CSRF) |
| **Database** | SQLite |
| **API** | CoinGecko Public API v3 |
| **ML** | NumPy, scikit-learn (Linear Regression) |
| **Template** | Jinja2 |
| **CSS/JS** | IBM Plex Sans, Lucide Icons, Chart.js |
| **Cache** | In-memory TTL cache (custom) |
| **Testing** | pytest |

---

## 5. CoinGecko API

### 5.1 Tentang CoinGecko

CoinGecko menyediakan API publik gratis untuk mengakses data cryptocurrency. API ini tidak memerlukan kunci untuk endpoint dasar, namun API key meningkatkan rate limit.

**Base URL:** `https://api.coingecko.com/api/v3`

### 5.2 Rate Limit (Tanpa API Key)

| Endpoint | Limit |
|---|---|
| `/coins/markets` | 10–30 request/menit |
| `/coins/{id}` | 10–50 request/menit |
| `/search` | 10–50 request/menit |
| `/global` | 10–30 request/menit |

### 5.3 Alur Request API

```
Browser → Flask Route → services/coingecko_service.py
                                    ↓
                              [Cache Check]
                                    ↓
                          CoinGecko API (HTTP GET)
                                    ↓
                              [Parse JSON]
                                    ↓
                              [Store Cache]
                                    ↓
                            Flask Template (Jinja2)
                                    ↓
                               Browser Render
```

### 5.4 Error Handling API

Semua error dari CoinGecko ditangani secara terstruktur dengan custom exception:

- `CoinGeckoTimeout` — request timeout
- `CoinGeckoRateLimit` — HTTP 429
- `CoinGeckoAPIError` — HTTP 4xx/5xx
- `CoinGeckoDataError` — response tidak sesuai schema

---

## 6. Struktur Aplikasi

```
crypto_tracker/
├── app.py                  # Flask app factory + semua route
├── config.py               # Konfigurasi environment-based
├── extensions.py           # Ekstensi Flask (db, login_manager, csrf)
├── models.py               # Model SQLAlchemy (User, Watchlist)
├── decorators.py           # Custom decorators (admin_required)
├── validators.py           # Input validation functions
├── ml_model.py             # ML: Linear Regression, RSI, SMA, Bollinger
├── requirements.txt        # Dependency Python
├── .env.example            # Template environment variable
├── .env                    # Environment variable (tidak di-commit)
├── services/
│   ├── cache_service.py    # In-memory TTL cache singleton
│   └── coingecko_service.py # Semua request ke CoinGecko
├── templates/
│   ├── base.html           # Layout utama
│   ├── index.html          # Landing + /market
│   ├── detail.html         # Detail koin + chart
│   ├── dashboard.html      # Dashboard user
│   ├── login.html          # Login form
│   ├── register.html       # Registrasi
│   ├── profile.html        # Edit profil
│   ├── change_password.html# Ubah password
│   ├── admin.html          # Panel admin
│   ├── admin_edit.html     # Edit user oleh admin
│   ├── about.html          # Tentang aplikasi
│   └── error.html          # Custom error pages
├── static/css/style.css    # Stylesheet utama
└── instance/users.db       # Database SQLite
```

---

## 7. Struktur Database

### 7.1 ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    USER ||--o{ WATCHLIST : has
    USER {
        int id PK "Primary Key, Auto Increment"
        string username UK "Unique, 3-30 chars"
        string email UK "Unique, lowercase"
        string password_hash "Werkzeug pbkdf2:sha256"
        boolean is_admin "Default: False"
        boolean is_approved "Default: False, perlu approval admin"
        datetime created_at "Auto set pada create"
    }
    WATCHLIST {
        int id PK "Primary Key, Auto Increment"
        int user_id FK "Foreign Key → USER.id"
        string coin_id "CoinGecko coin ID"
    }
    WATCHLIST {
        unique_constraint "(user_id, coin_id)" 
    }
```

### 7.2 Penjelasan Relasi

- **USER → WATCHLIST (one-to-many):** Satu user dapat memiliki banyak koin dalam watchlist.
- **WATCHLIST:** Tabel penghubung many-to-many antara User dan Koin. Menggunakan `UniqueConstraint` pada `(user_id, coin_id)` untuk mencegah duplikat.
- **Cascade Delete:** Ketika user dihapus, seluruh watchlist terkait ikut dihapus.

---

## 8. Daftar Endpoint

| Method | Endpoint | Akses | Fungsi |
|---|---|---|---|
| GET | `/` | Publik | Landing page dengan ringkasan pasar |
| GET | `/market` | Publik | Halaman data API (min 20 koin) |
| GET | `/coin/<coin_id>` | Publik | Detail koin dengan chart dan ML indicators |
| GET/POST | `/register` | Publik | Form registrasi user baru |
| GET/POST | `/login` | Publik | Form login |
| POST | `/logout` | Login | Logout user (POST only) |
| GET | `/dashboard` | Login | Dashboard dengan watchlist + trending |
| POST | `/watchlist/add/<coin_id>` | Login | Tambah koin ke watchlist |
| POST | `/watchlist/remove/<coin_id>` | Login | Hapus koin dari watchlist |
| GET/POST | `/profile` | Login | Edit profil user |
| GET/POST | `/change-password` | Login | Ubah password |
| POST | `/theme` | Semua | Toggle light/dark theme |
| GET | `/admin` | Admin | Panel admin — approve/reject user |
| POST | `/admin/create-user` | Admin | Buat user baru (langsung approved) |
| GET/POST | `/admin/edit-user/<id>` | Admin | Edit data user |
| POST | `/admin/approve/<id>` | Admin | Approve user pending |
| POST | `/admin/reject/<id>` | Admin | Tolak dan hapus user pending |
| POST | `/admin/toggle-admin/<id>` | Admin | Promosi/demote role admin |
| POST | `/admin/delete-user/<id>` | Admin | Hapus user |
| GET | `/about` | Publik | Tentang aplikasi |

---

## 9. Authentication & Authorization

### 9.1 Authentication

- **Register:** User baru dibuat dengan `is_approved=False`. Password di-hash dengan `pbkdf2:sha256`.
- **Login:** Hanya user dengan `is_approved=True` dapat login.
- **Session:** Menggunakan Flask-Login dengan session cookie `HttpOnly`, `SameSite=Lax`.
- **Logout:** Hanya via POST request (CSRF protected).

### 9.2 Authorization

- **`@login_required`:** Memastikan user sudah login.
- **`@admin_required`:** Memastikan user login DAN memiliki role `is_admin=True`.
- **Middleware-level:** Proteksi di level decorator, bukan inline check.

### 9.3 Proteksi Admin Terakhir

Fungsi `count_active_admins()` menghitung admin yang:
- `is_admin == True`
- `is_approved == True`

Pencegahan:
- Admin terakhir tidak dapat dihapus.
- Admin terakhir tidak dapat demote.
- User tidak dapat menghapus dirinya sendiri sebagai admin.

---

## 10. Validation

| Field | Aturan |
|---|---|
| **Username** | 3–30 karakter, alphanumeric + `_.-` saja |
| **Email** | Format valid (email-validator), lowercase, unique |
| **Password** | Minimal 8 karakter |
| **Pagination** | `page` minimal 1; `per_page` hanya 10/20/50 |
| **Sort order** | Allowlist: `market_cap_desc`, `market_cap_asc`, `volume_desc`, `id_asc`, `id_desc` |
| **Chart days** | Hanya boleh `7`, `30`, atau `90` |

---

## 11. Error Handling

### 11.1 HTTP Error Handler

| Code | Halaman | Fungsi |
|---|---|---|
| 403 | Custom | Akses ditolak — unauthorized |
| 404 | Custom | Halaman tidak ditemukan |
| 405 | Custom | Method not allowed |
| 500 | Custom | Server error (DB rollback otomatis) |
| CSRF | Custom | Token CSRF tidak valid |

### 11.2 API Error Handling

- **Timeout:** Log warning + tampilkan flash message + halaman fallback dengan data kosong.
- **Rate Limit (429):** Gunakan cached data jika tersedia + flash warning.
- **HTTP 5xx:** Log + flash + halaman fallback.
- **HTTP 4xx:** Log + flash + halaman fallback.

### 11.3 Database Transaction

Semua operasi write menggunakan pola:
```python
try:
    db.session.commit()
except Exception:
    db.session.rollback()
    flash("Error message", "error")
```

---

## 12. Cache

Implementasi: **In-memory TTL cache singleton** (tidak memerlukan Redis).

### 12.1 Cache Key Strategy

```
coins:usd:market_cap_desc:page=1:per_page=20
history:bitcoin:30
detail:bitcoin
global
trending
```

### 12.2 TTL (Time-To-Live)

| Data | TTL |
|---|---|
| Market list | 300 detik (5 menit) |
| Coin detail | 300 detik |
| Global stats | 300 detik |
| Trending | 300 detik |
| Price history | 600 detik (10 menit) |

---

## 13. Fitur Utama

1. **Market Data** — 20+ koin dari CoinGecko dengan harga, market cap, volume, perubahan 24 jam.
2. **Pencarian** — Cari koin berdasarkan nama atau simbol.
3. **Sorting** — Urutkan berdasarkan market cap atau volume.
4. **Pagination** — Navigasi halaman untuk hasil banyak.
5. **Detail Koin** — Halaman detail dengan chart interaktif (Chart.js).
6. **Autentikasi** — Register, login, logout dengan proteksi CSRF.
7. **Watchlist** — Simpan koin favorit per user.
8. **Dashboard** — Ringkasan watchlist + trending + global stats.
9. **ML Prediction** — Proyeksi tren 7 hari menggunakan Linear Regression.
10. **RSI Indicator** — Relative Strength Index (overbought/oversold).
11. **SMA Crossover** — Simple Moving Average 7 vs 30 hari.
12. **Bollinger Bands** — Volatility envelope.
13. **Admin Panel** — CRUD user, approve/reject registrasi.
14. **Theme Toggle** — Mode light/dark.
15. **Error Pages** — Custom 403/404/405/500/CSRF.
16. **API Rate Limit Handling** — Graceful fallback.

---

## 14. Cara Menjalankan

### 14.1 Install Dependency

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# atau .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 14.2 Konfigurasi

```bash
cp .env.example .env
# Edit .env jika perlu (SECRET_KEY sudah dibuat otomatis)
```

### 14.3 Jalankan

```bash
python app.py
```

Aplikasi berjalan di `http://127.0.0.1:5050`.

### 14.4 Buat Admin via CLI

```bash
flask create-admin
```

---

## 15. Pembagian Tugas

| Anggota | Tugas |
|---|---|
| [Nama 1] | Backend route, autentikasi, database model |
| [Nama 2] | Template, CSS, API integration, dokumentasi |

*Sesuaikan dengan pembagian aktual*

---

## 16. Manfaat

1. **Edukatif:** Mendemonstrasikan konsep full-stack web development.
2. **Analitis:** Memberikan insight pergerakan harga cryptocurrency.
3. **Modular:** Struktur proyek dapat digunakan sebagai template proyek lain.
4. **Real-time:** Data selalu fresh dari CoinGecko API.
5. **Aman:** Implementasi CSRF, validasi input, proteksi admin.

---

## 17. Insight Implementasi

### 17.1 Modularitas

Pemisahan `services/coingecko_service.py` memungkinkan perubahan endpoint API tanpa menyentuh route. Cache service singleton mencegah duplicate code.

### 17.2 Keamanan

- CSRF protection pada semua form POST.
- Safe redirect untuk mencegah open redirect.
- Password tidak pernah di-log atau di-display.
- Admin last-admin protection mencegah lockout.

### 17.3 Error Handling Terstruktur

Custom exception hierarchy memungkinkan granular error handling tanpa `except Exception: pass`.

### 17.4 ML Prediction

Linear Regression dipilih karena sederhana, interpretable, dan cocok untuk data time series pendek. Hasil bukan rekomendasi investasi — hanya proyeksi tren eksperimental.

---

## 18. Keterbatasan

1. **Rate Limit:** Tanpa API key, CoinGecko membatasi request.
2. **Offline:** Tidak ada mekanisme sync offline.
3. **ML Sederhana:** Linear Regression tidak menangkap seasonality atau non-linearitas.
4. **Single Database:** SQLite tidak cocok untuk multi-user konkuren tinggi.
5. **No WebSocket:** Harga tidak real-time — perlu refresh atau polling.

---

## 19. Kesimpulan

CryptoTracker BMZ berhasil mengimplementasikan seluruh requirement UAS Pemrograman Backend: integrasi public API, autentikasi & otorisasi, validasi, error handling, struktur modular, ORM, CRUD, templating, dan dokumentasi. Aplikasi dapat dijalankan dari instalasi baru tanpa langkah tersembunyi dan memiliki error handling yang robust terhadap kegagalan API CoinGecko.

---

## 20. Disclaimer ML

> ⚠️ **Analisis ini merupakan proyeksi tren eksperimental berdasarkan data historis dan indikator teknikal. Hasilnya BUKAN rekomendasi investasi dan tidak menjamin pergerakan harga di masa depan. Selalu lakukan riset sendiri sebelum membuat keputusan finansial.**
