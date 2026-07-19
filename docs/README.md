# CryptoTracker BMZ

Cryptocurrency price tracker with user authentication, watchlist, ML price prediction, and admin approval system.

## Features

### Core Features
- **Live Prices** — Real-time data from CoinGecko API
- **Market Overview** — Total market cap, 24h volume, BTC dominance
- **Trending Coins** — Top 7 trending coins
- **Search** — Find any cryptocurrency by name
- **Price Chart** — Interactive chart (7D / 30D / 90D) with Chart.js

### User Features
- **Authentication** — Register, login, logout (Flask-Login + pbkdf2:sha256)
- **Watchlist** — Save favorite coins with heart icon
- **Price Prediction** — Linear Regression model predicts price 7 days ahead
- **Signal Filter** — Filter coins by BUY/SELL/HOLD/STRONG BUY/STRONG SELL on market page
- **Profile Management** — Edit username, email, change password

### Admin Features
- **Admin Dashboard** (`/admin`) — Manage user registrations
- **Approval System** — New users require admin approval before login
- **User Management** — Promote to admin, delete users

### UI/UX
- **Dark / Light Mode** — Toggle in navbar (session-persisted)
- **Toast Notifications** — Floating alerts with auto-dismiss
- **Lucide Icons** — Consistent SVG icon system
- **Responsive Design** — Works on desktop and mobile

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0+ |
| Database | SQLite (Flask-SQLAlchemy) |
| Auth | Flask-Login |
| Password | Werkzeug (pbkdf2:sha256) |
| ML | scikit-learn (LinearRegression), NumPy |
| API | CoinGecko (free demo tier) |
| Charts | Chart.js 4 (CDN) |
| Icons | Lucide (CDN) |
| Frontend | Jinja2, Vanilla JS, CSS |

## Installation

```bash
cd /Users/ashura/projects/crypto_tracker
pip3 install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5050 in your browser.

## Project Structure

```
crypto_tracker/
├── app.py                  # Flask app, routes, ML prediction
├── ml_model.py             # ML functions (Linear Regression)
├── requirements.txt        # Python dependencies
├── .gitignore             # Excludes: __pycache__, *.db, .env
├── instance/
│   └── users.db            # SQLite database (auto-created)
├── docs/
│   ├── README.md          # This file
│   ├── ML_PREDICTION.md   # ML mechanism documentation
│   └── API_DOCUMENTATION.md # Full API documentation
├── templates/
│   ├── base.html          # Base layout + navbar + theme toggle
│   ├── index.html         # Homepage (coin list + search + signal filter)
│   ├── detail.html        # Coin detail + chart + ML signal (logged-in)
│   ├── dashboard.html     # User dashboard (watchlist + prediction)
│   ├── login.html         # Login form
│   ├── register.html      # Registration form
│   ├── profile.html       # Edit profile
│   ├── change_password.html # Change password
│   ├── admin.html         # Admin dashboard (user approvals)
│   ├── about.html         # About page
│   └── error.html         # Error page
└── static/
    └── css/
        └── style.css      # All styles (light + dark theme)
```

## Routes

| Route | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | Public | Homepage — coin list + signal filter (logged-in) |
| `/coin/<id>` | GET | Public | Coin detail + chart |
| `/about` | GET | Public | About page |
| `/register` | GET/POST | Public | User registration (pending approval) |
| `/login` | GET/POST | Public | User login (requires approval) |
| `/logout` | GET | Required | Clear session |
| `/dashboard` | GET | **Required** | Watchlist + prediction |
| `/profile` | GET/POST | **Required** | Edit profile |
| `/change-password` | GET/POST | **Required** | Change password |
| `/watchlist/add/<id>` | POST | **Required** | Add to watchlist |
| `/watchlist/remove/<id>` | POST | **Required** | Remove from watchlist |
| `/theme` | GET | Public | Toggle dark/light mode |
| `/admin` | GET | **Admin** | Admin dashboard |
| `/admin/approve/<id>` | POST | **Admin** | Approve pending user |
| `/admin/reject/<id>` | POST | **Admin** | Reject/delete pending user |
| `/admin/toggle-admin/<id>` | POST | **Admin** | Promote/demote admin |
| `/admin/delete-user/<id>` | POST | **Admin** | Delete approved user |

## API Documentation

### External — CoinGecko API

| Endpoint | Purpose |
|---|---|
| `/coins/markets` | Coin list with prices, market cap |
| `/coins/{id}` | Coin detail (description, supply) |
| `/coins/{id}/market_chart` | Price history for chart + ML |
| `/search` | Coin search |
| `/search/trending` | Trending coins |
| `/global` | Global market stats |

### Internal — App Routes

See `docs/API_DOCUMENTATION.md` for full API documentation.

## Database Schema

### User
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    is_approved BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Watchlist
```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    coin_id VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, coin_id)
);
```

## ML Prediction — Quick Summary

- **Method:** Linear Regression (scikit-learn)
- **Training:** 30 days of daily price data
- **Output:** Signal (STRONG BUY/BUY/HOLD/SELL/STRONG SELL) + predicted change % + confidence
- **Forecast:** 7 days ahead
- **Signal Logic:** Based on predicted_change_pct only (R² < 0.3 = HOLD)
- **Public Access:** Price chart visible to all; ML signal requires login
- **Details:** See `docs/ML_PREDICTION.md`

## Student Info

- **Nama:** Bemis Huntala
- **NIM:** 1002240018
- **Prodi:** Teknologi Informasi, Semester 4

## Author

Bemis Huntala — 2026
