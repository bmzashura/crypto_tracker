# Screenshot Checklist — CryptoTracker BMZ UAS

Dokumen ini berisi daftar screenshot yang perlu diambil untuk demonstrasi UAS.
Setiap screenshot harus menunjukkan data nyata, bukan data dummy.

---

## Kategori A — Authentication

### A1. Halaman Login
**Route:** `GET /login`
**Langkah:**
1. Buka browser, navigasi ke `http://127.0.0.1:5050/login`
2. Screenshot halaman login

**Expected:** Form login dengan fields username, password, tombol Login, link ke Register.

---

### A2. Form Registrasi
**Route:** `GET /register`
**Langkah:**
1. Klik link "Register here" di halaman login
2. Screenshot halaman registrasi

**Expected:** Form registrasi dengan fields username, email, password, confirm password.

---

### A3. Registrasi Validasi — Username Kosong
**Route:** `POST /register`
**Langkah:**
1. Submit form registrasi dengan username kosong
2. Screenshot flash error

**Expected:** Pesan error validasi username.

---

### A4. Registrasi Validasi — Email Tidak Valid
**Route:** `POST /register`
**Langkah:**
1. Submit form dengan email tidak valid (cth: `bukan-email`)
2. Screenshot flash error

**Expected:** Pesan error format email tidak valid.

---

### A5. Registrasi Validasi — Password Pendek
**Route:** `POST /register`
**Langkah:**
1. Submit form dengan password kurang dari 8 karakter
2. Screenshot flash error

**Expected:** Pesan error password minimal 8 karakter.

---

### A6. Registrasi Sukses — User Pending
**Route:** `POST /register` → redirect ke login
**Langkah:**
1. Submit form dengan data valid
2. Screenshot flash success + redirect ke login

**Expected:** "Registrasi berhasil! Akun Anda menunggu approval dari admin."

---

### A7. Login Gagal — User Pending
**Route:** `POST /login`
**Langkah:**
1. Login dengan akun yang baruregister (belum di-approve)
2. Screenshot flash error

**Expected:** "Akun Anda belum disetujui admin."

---

## Kategori B — Admin & Authorization

### B1. Admin Panel — Daftar User
**Route:** `GET /admin`
**Langkah:**
1. Login sebagai admin (admin / Admin1234)
2. Navigasi ke `/admin`
3. Screenshot panel admin

**Expected:** Tabel user pending + tabel user approved.

---

### B2. Admin Membuat User Baru
**Route:** `POST /admin/create-user`
**Langkah:**
1. Klik tombol "+ Create User" di admin panel
2. Isi form: username, email, password, centang "Grant Admin Privileges"
3. Submit dan screenshot

**Expected:** User langsung terbuat (approved), muncul di tabel approved.

---

### B3. Admin Approve User
**Route:** `POST /admin/approve/<user_id>`
**Langkah:**
1. Di panel admin, cari user pending
2. Klik tombol "Approve"
3. Screenshot flash success

**Expected:** User berpindah dari tabel pending ke approved.

---

### B4. User Login Setelah Approval
**Route:** `POST /login`
**Langkah:**
1. Login dengan user yang sudah di-approve
2. Screenshot redirect ke dashboard

**Expected:** Berhasil login, redirect ke dashboard.

---

### B5. Authorization — User Biasa Akses Admin
**Route:** `GET /admin`
**Langkah:**
1. Login sebagai user biasa (bukan admin)
2. Navigasi ke `/admin`
3. Screenshot error 403

**Expected:** Halaman 403 Custom Error — "Akses Ditolak".

---

### B6. Admin Edit User
**Route:** `GET/POST /admin/edit-user/<user_id>`
**Langkah:**
1. Di admin panel, klik "Edit" pada user tertentu
2. Ubah username atau email
3. Submit dan screenshot

**Expected:** User diperbarui, flash success.

---

### B7. Admin Toggle Admin Role
**Route:** `POST /admin/toggle-admin/<user_id>`
**Langkah:**
1. Di admin panel, klik "Make Admin" atau "Remove Admin"
2. Screenshot flash success + perubahan role badge

**Expected:** Role berubah antara Admin/User.

---

### B8. Admin Delete User
**Route:** `POST /admin/delete-user/<user_id>`
**Langkah:**
1. Di admin panel, klik "Delete" pada user non-admin
2. Konfirmasi delete
3. Screenshot flash success

**Expected:** User dihapus dari tabel.

---

## Kategori C — Market Data & API

### C1. Landing Page
**Route:** `GET /`
**Langkah:**
1. Buka `http://127.0.0.1:5050/`
2. Screenshot landing page

**Expected:** Ringkasan market global + CTA ke /market.

---

### C2. Market Page — Minimal 10 Koin
**Route:** `GET /market`
**Langkah:**
1. Navigasi ke `/market`
2. Screenshot tabel market dengan minimal 10 koin

**Expected:** Tabel dengan nama, harga, 24h change, market cap, volume, rank. Semua data dari CoinGecko API.

---

### C3. Market Page — Pencarian
**Route:** `GET /market?search=bitcoin`
**Langkah:**
1. Ketik "bitcoin" di search box
2. Submit
3. Screenshot hasil pencarian

**Expected:** Hasil pencarian untuk Bitcoin.

---

### C4. Market Page — Sorting
**Route:** `GET /market?order=volume_desc`
**Langkah:**
1. Ubah sorting ke volume descending
2. Screenshot perubahan urutan

**Expected:** Koin dengan volume tertinggi di atas.

---

### C5. Detail Koin — Bitcoin
**Route:** `GET /coin/bitcoin`
**Langkah:**
1. Klik "Details" pada Bitcoin di market page
2. Screenshot halaman detail

**Expected:** Info Bitcoin, chart harga 7 hari, ML prediction signal.

---

### C6. Detail Koin — Chart 30 Hari
**Route:** `GET /coin/bitcoin?days=30`
**Langkah:**
1. Di halaman detail Bitcoin, klik tombol "30D"
2. Screenshot chart berubah rentang waktu

**Expected:** Chart menampilkan 30 hari data.

---

### C7. Global Market Stats
**Route:** `GET /` (bagian atas)
**Langkah:**
1. Scroll ke atas landing page
2. Screenshot statistik global

**Expected:** Total market cap, 24h volume, BTC dominance.

---

## Kategori D — Watchlist & Dashboard

### D1. Tambah ke Watchlist
**Route:** `POST /watchlist/add/<coin_id>`
**Langkah:**
1. Login sebagai user
2. Di market page, klik heart icon pada koin
3. Screenshot flash success

**Expected:** "bitcoin ditambahkan ke watchlist."

---

### D2. Dashboard — Watchlist
**Route:** `GET /dashboard`
**Langkah:**
1. Navigasi ke `/dashboard`
2. Screenshot dashboard dengan watchlist

**Expected:** Watchlist coins dengan harga, prediction, dan trending.

---

### D3. Hapus dari Watchlist
**Route:** `POST /watchlist/remove/<coin_id>`
**Langkah:**
1. Di dashboard, klik heart icon pada koin di watchlist
2. Screenshot flash success

**Expected:** Koin dihapus dari watchlist.

---

## Kategori E — User Profile

### E1. Edit Profil
**Route:** `GET/POST /profile`
**Langkah:**
1. Login sebagai user
2. Navigasi ke `/profile`
3. Ubah username atau email
4. Submit dan screenshot

**Expected:** Flash success + perubahan terlihat.

---

### E2. Ubah Password
**Route:** `GET/POST /change-password`
**Langkah:**
1. Navigasi ke `/change-password`
2. Isi form: password lama, password baru, konfirmasi
3. Submit dan screenshot

**Expected:** Redirect ke login setelah sukses.

---

## Kategori F — Error Handling

### F1. Error 403 — Akses Ditolak
**Route:** `GET /admin` (sebagai user non-admin)
**Langkah:**
1. Login sebagai user biasa
2. Akses `/admin`
3. Screenshot halaman error 403

**Expected:** Custom error page dengan icon shield-off, judul "Akses Ditolak".

---

### F2. Error 404 — Halaman Tidak Ditemukan
**Route:** `GET /halaman-yang-tidak-ada`
**Langkah:**
1. Navigasi ke URL yang tidak ada
2. Screenshot halaman error 404

**Expected:** Custom error page dengan icon file-x, judul "Halaman Tidak Ditemukan".

---

### F3. Error 405 — Method Not Allowed
**Route:** `GET /logout` (seharusnya POST)
**Langkah:**
1. Langsung akses `GET /logout`
2. Screenshot error 405

**Expected:** Custom error page dengan icon x-circle.

---

### F4. Error CSRF
**Route:** `POST /login` (dengan CSRF token invalid)
**Langkah:**
1. Submit form login dengan CSRF token salah
2. Screenshot CSRF error

**Expected:** "The CSRF token is invalid or missing."

---

## Kategori G — UI/UX

### G1. Theme Toggle — Light Mode
**Langkah:**
1. Screenshot aplikasi dalam light mode

**Expected:** Background putih, teks gelap.

---

### G2. Theme Toggle — Dark Mode
**Langkah:**
1. Klik tombol theme toggle (bulan/matahari)
2. Screenshot dalam dark mode

**Expected:** Background gelap, teks terang.

---

## Catatan Penting

1. Semua screenshot harus menunjukkan **data nyata** dari CoinGecko API.
2. Jangan edit atau crop screenshot secara misleading.
3. Username/password yang ditunjukkan adalah akun demo.
4. Urutan screenshot mengikuti alur demontrasi UAS.
