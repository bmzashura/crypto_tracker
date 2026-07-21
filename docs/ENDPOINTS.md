# API Endpoints — CryptoTracker BMZ

## Public Endpoints

### `GET /`
**Fungsi:** Landing page dengan ringkasan pasar global.
**Akses:** Semua pengunjung (publik).
**Request:** Tidak ada parameter.
**Response:** HTML page dengan global stats (total market cap, 24h volume, active cryptos, BTC dominance).
**Kemungkinan Error:** 200 OK selalu (fallback: empty stats).

---

### `GET /market`
**Fungsi:** Halaman data cryptocurrency dari CoinGecko.
**Akses:** Publik.
**Query Parameters:**
| Parameter | Tipe | Default | Deskripsi |
|---|---|---|---|
| `page` | int | 1 | Nomor halaman (min 1) |
| `per_page` | int | 20 | Items per halaman (10/20/50) |
| `order` | string | market_cap_desc | Sorting order |
| `search` | string | "" | Kata kunci pencarian |

**Response:** HTML table dengan minimal 20 koin (nama, simbol, harga, market cap, 24h change, volume, rank).
**Kemungkinan Error:** 200 OK (API error → fallback empty list).

---

### `GET /coin/<coin_id>`
**Fungsi:** Halaman detail cryptocurrency.
**Akses:** Publik.
**Path Parameters:**
| Parameter | Tipe | Deskripsi |
|---|---|---|
| `coin_id` | string | CoinGecko coin ID (cth: bitcoin, ethereum) |

**Query Parameters:**
| Parameter | Tipe | Default | Deskripsi |
|---|---|---|---|
| `days` | int | 7 | Rentang chart (7/30/90) |

**Response:** HTML page dengan info koin, chart harga, ML prediction, RSI, SMA, Bollinger Bands.
**Kemungkinan Error:** 404 (coin tidak ditemukan), 500 (API error).

---

### `GET /about`
**Fungsi:** Halaman informasi tentang aplikasi.
**Akses:** Publik.
**Response:** HTML page dengan deskripsi aplikasi dan fitur.

---

## Authentication Endpoints

### `GET/POST /register`
**Fungsi:** Form registrasi user baru.
**Akses:** Publik (guest only).
**POST Body (form-data):**
| Field | Required | Deskripsi |
|---|---|---|
| `username` | Ya | 3-30 chars, alphanumeric + `_.-` |
| `email` | Ya | Format email valid, unique |
| `password` | Ya | Minimal 8 karakter |
| `confirm_password` | Ya | Harus sama dengan password |
| `csrf_token` | Ya | CSRF token dari Flask-WTF |

**Redirect:** `GET /register` → form; `POST` sukses → `/login` dengan flash message.
**Kemungkinan Error:**
- 400 — CSRF token invalid
- 422 — Validasi gagal (username/email/password)

**Catatan:** User baru dibuat dengan `is_approved=False` — perlu approval admin sebelum login.

---

### `GET/POST /login`
**Fungsi:** Form login user.
**Akses:** Publik (guest only).
**POST Body (form-data):**
| Field | Required | Deskripsi |
|---|---|---|
| `username` | Ya | Username user |
| `password` | Ya | Password |
| `csrf_token` | Ya | CSRF token |

**Query Parameter:** `next` — redirect URL setelah login (validasi same-origin).
**Redirect:** Sukses → `/dashboard` atau `next`; Gagal → `/login` dengan flash error.
**Kemungkinan Error:**
- 400 — CSRF invalid
- 401 — Username/password salah
- 403 — Akun belum di-approve

---

### `POST /logout`
**Fungsi:** Logout user.
**Akses:** User yang sudah login.
**Request:** POST dengan CSRF token (form atau header).
**Response:** Redirect ke `/` dengan flash "Anda sudah logout."
**Kemungkinan Error:** 401 — belum login.

---

## Authenticated User Endpoints

### `GET /dashboard`
**Fungsi:** Dashboard user — watchlist + global stats + trending.
**Akses:** User yang sudah login.
**Response:** HTML dengan watchlist coins (harga + prediction 7 hari), global market summary, 7 trending coins.
**Kemungkinan Error:** 401 — belum login.

---

### `POST /watchlist/add/<coin_id>`
**Fungsi:** Tambahkan koin ke watchlist user.
**Akses:** User yang sudah login.
**Path Parameters:** `coin_id` — CoinGecko coin ID.
**Request:** POST dengan CSRF token.
**Response:** Redirect kembali ke halaman sebelumnya.
**Kemungkinan Error:** 401 — belum login; 409 — sudah ada di watchlist.

---

### `POST /watchlist/remove/<coin_id>`
**Fungsi:** Hapus koin dari watchlist user.
**Akses:** User yang sudah login.
**Path Parameters:** `coin_id` — CoinGecko coin ID.
**Request:** POST dengan CSRF token.
**Response:** Redirect kembali ke halaman sebelumnya.
**Kemungkinan Error:** 401 — belum login.

---

### `GET/POST /profile`
**Fungsi:** Lihat dan edit profil user.
**Akses:** User yang sudah login.
**POST Body (form-data):**
| Field | Required | Deskripsi |
|---|---|---|
| `username` | Ya | Username baru |
| `email` | Ya | Email baru |
| `csrf_token` | Ya | CSRF token |

**Response:** Form edit profil. Setelah update → flash success.
**Kemungkinan Error:** 400 — duplicate username/email atau validasi gagal.

---

### `GET/POST /change-password`
**Fungsi:** Ubah password user.
**Akses:** User yang sudah login.
**POST Body (form-data):**
| Field | Required | Deskripsi |
|---|---|---|
| `current_password` | Ya | Password lama |
| `new_password` | Ya | Password baru (min 8 chars) |
| `confirm_password` | Ya | Konfirmasi password baru |
| `csrf_token` | Ya | CSRF token |

**Response:** Setelah sukses → logout + redirect ke login.
**Kemungkinan Error:** 400 — password lama salah atau validasi gagal.

---

## Admin Endpoints

### `GET /admin`
**Fungsi:** Panel admin — manajemen user.
**Akses:** User dengan `is_admin=True` dan `is_approved=True`.
**Response:** HTML dengan daftar user pending approval + daftar user approved.
**Kemungkinan Error:** 403 — bukan admin.

---

### `POST /admin/create-user`
**Fungsi:** Buat user baru langsung oleh admin (langsung approved).
**Akses:** Admin only.
**POST Body (form-data):**
| Field | Required | Deskripsi |
|---|---|---|
| `username` | Ya | Username |
| `email` | Ya | Email valid |
| `password` | Ya | Min 8 karakter |
| `make_admin` | No | Checkbox untuk admin privilege |
| `csrf_token` | Ya | CSRF token |

**Response:** Redirect ke `/admin` dengan flash success.
**Kemungkinan Error:** 400 — duplicate atau validasi gagal; 403 — bukan admin.

---

### `GET/POST /admin/edit-user/<user_id>`
**Fungsi:** Edit data user oleh admin.
**Akses:** Admin only.
**Path Parameters:** `user_id` — ID user yang akan diedit.
**POST Body:** Sama seperti `/admin/create-user` + `csrf_token`.
**Proteksi:** Tidak bisa edit admin terakhir; tidak bisa demote diri sendiri.
**Kemungkinan Error:** 403 — bukan admin; 404 — user tidak ditemukan.

---

### `POST /admin/approve/<user_id>`
**Fungsi:** Setujui user pending.
**Akses:** Admin only.
**Path Parameters:** `user_id` — ID user.
**Request:** POST dengan CSRF token.
**Response:** Redirect ke `/admin` dengan flash success.
**Kemungkinan Error:** 404 — user tidak ditemukan.

---

### `POST /admin/reject/<user_id>`
**Fungsi:** Tolak dan hapus user pending.
**Akses:** Admin only.
**Proteksi:** Tidak bisa reject admin; tidak bisa reject diri sendiri.
**Kemungkinan Error:** 403 — tidak diizinkan; 404 — user tidak ditemukan.

---

### `POST /admin/toggle-admin/<user_id>`
**Fungsi:** Promosi user ke admin atau demote admin ke user.
**Akses:** Admin only.
**Proteksi:** Admin terakhir tidak bisa di-demote; tidak bisa demote diri sendiri.
**Kemungkinan Error:** 403 — tidak diizinkan; 404 — user tidak ditemukan.

---

### `POST /admin/delete-user/<user_id>`
**Fungsi:** Hapus user dan seluruh watchlist-nya.
**Akses:** Admin only.
**Proteksi:** Admin terakhir tidak bisa dihapus; tidak bisa hapus diri sendiri.
**Kemungkinan Error:** 403 — tidak diizinkan; 404 — user tidak ditemukan.

---

## Error Responses

Semua error handler mengembalikan HTML page dengan struktur:

| Code | Title | Icon |
|---|---|---|
| 403 | Akses Ditolak | shield-off |
| 404 | Halaman Tidak Ditemukan | file-x |
| 405 | Metode Tidak Diizinkan | x-circle |
| 500 | Kesalahan Server | server-off |

---

## CLI Commands

### `flask create-admin`
**Fungsi:** Buat admin user via terminal interaktif.
**Usage:**
```bash
flask create-admin
```
Prompt untuk username, email, password (dengan getpass — tidak echo).
