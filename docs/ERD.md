# Entity Relationship Diagram — CryptoTracker BMZ

## Database Schema

**Database:** SQLite
**ORM:** Flask-SQLAlchemy

---

## ERD

```mermaid
erDiagram
    USER ||--o{ WATCHLIST : "has (1 to many)"
    USER {
        int id PK "Primary Key, Auto Increment"
        string username UK "Unique, 3-30 chars, NOT NULL"
        string email UK "Unique, lowercase, NOT NULL"
        string password_hash "NOT NULL, Werkzeug pbkdf2:sha256"
        boolean is_admin "DEFAULT FALSE"
        boolean is_approved "DEFAULT FALSE"
        datetime created_at "Auto UTC timestamp"
    }
    WATCHLIST {
        int id PK "Primary Key, Auto Increment"
        int user_id FK "NOT NULL, → USER.id ON DELETE CASCADE"
        string coin_id "NOT NULL, CoinGecko coin ID string"
    }
    WATCHLIST {
        unique_constraint "uq_watchlist_user_coin (user_id, coin_id)"
    }
```

---

## Relasi

### USER → WATCHLIST (One-to-Many)

```
USER (1) ──────< (many) WATCHLIST
```

- Setiap USER dapat memiliki nol atau banyak WATCHLIST entries.
- Setiap WATCHLIST entry milik tepat satu USER.
- Relasi diimplementasikan via SQLAlchemy `relationship()` dengan `cascade="all, delete-orphan"`.

---

## Atribut USER

| Atribut | Tipe | Constraints | Deskripsi |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Primary key |
| `username` | String(30) | UNIQUE, NOT NULL, INDEX | Username login |
| `email` | String(120) | UNIQUE, NOT NULL, INDEX | Email untuk kontak |
| `password_hash` | String(256) | NOT NULL | Werkzeug hash |
| `is_admin` | Boolean | DEFAULT False | Role flag |
| `is_approved` | Boolean | DEFAULT False | Approval flag |
| `created_at` | DateTime | Auto UTC | Timestamp registrasi |

**Indexes:**
- `idx_username` on `username`
- `idx_email` on `email`

---

## Atribut WATCHLIST

| Atribut | Tipe | Constraints | Deskripsi |
|---|---|---|---|
| `id` | Integer | PK, Auto Increment | Primary key |
| `user_id` | Integer | FK → USER.id, NOT NULL | Owner |
| `coin_id` | String(50) | NOT NULL | CoinGecko coin ID |

**Unique Constraint:** `(user_id, coin_id)` — mencegah duplikat watchlist untuk koin yang sama oleh user yang sama.

**Cascade:** `ON DELETE CASCADE` — jika user dihapus, semua watchlist entries-nya ikut terhapus.

---

## SQL DDL (Reference)

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    is_admin BOOLEAN DEFAULT 0 NOT NULL,
    is_approved BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_username ON user(username);
CREATE INDEX idx_email ON user(email);

CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    coin_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    UNIQUE (user_id, coin_id)
);
```

---

## Aturan Bisnis

1. **Registration:** User baru dibuat dengan `is_approved=False`. Tidak dapat login sampai admin approve.
2. **Admin Auto-create:** Admin default (`admin`/`Admin1234`) dibuat otomatis pada startup pertama jika `AUTO_CREATE_DEFAULT_ADMIN=true`.
3. **Watchlist Unique:** Satu user tidak dapat menambahkan koin yang sama dua kali ke watchlist.
4. **Admin Protection:** Admin terakhir tidak dapat dihapus atau di-demote untuk mencegah lockout.
5. **Self-Delete Protection:** User tidak dapat menghapus atau me-demote akunnya sendiri.
6. **Cascade Delete:** Menghapus user akan menghapus seluruh watchlist terkait.
