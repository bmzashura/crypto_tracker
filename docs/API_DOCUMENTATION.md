# API Documentation — CryptoTracker BMZ

## 1. External API — CoinGecko

This app uses the **CoinGecko API** (free demo tier) for all cryptocurrency market data.

### Base URL
```
https://api.coingecko.com/api/v3
```

### API Key
Demo key: `REMOVED_API_KEY`
> For production, set environment variable: `export COINGECKO_API_KEY='your_api_key'`

### Endpoints Used

#### GET /coins/markets
Fetch market data for multiple coins.

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `vs_currency` | string | `usd` | Currency (usd, eur, etc.) |
| `order` | string | `market_cap_desc` | Sort order |
| `per_page` | int | 20 | Results per page (max 250) |
| `page` | int | 1 | Page number |
| `ids` | string | — | Comma-separated coin IDs (optional) |
| `sparkline` | bool | `false` | Include sparkline |
| `price_change_percentage` | string | — | Include 24h change |

**Response:** Array of coin objects with: `id`, `symbol`, `name`, `image`, `current_price`, `market_cap`, `market_cap_rank`, `total_volume`, `high_24h`, `low_24h`, `price_change_24h`, `price_change_percentage_24h`, `circulating_supply`, `total_supply`, `max_supply`, `ath`, `ath_date`, `atl`, `atl_date`.

**Used in:** Homepage coin list, watchlist

---

#### GET /coins/{id}
Fetch detailed info for a specific coin.

**Parameters:**
| Param | Type | Description |
|---|---|---|
| `localization` | bool | Include localized languages (default: false) |
| `tickers` | bool | Include tickers (default: false) |
| `community_data` | bool | Include community stats (default: false) |
| `developer_data` | bool | Include developer stats (default: false) |

**Response:** Full coin object with: `id`, `symbol`, `name`, `image`, `description`, `market_data` (prices, ATH, ATL, market cap, volume, supply), etc.

**Used in:** Coin detail page

---

#### GET /coins/{id}/market_chart
Fetch price history for chart and ML prediction.

**Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `vs_currency` | string | `usd` | Currency |
| `days` | int | 7 | Days of history (1, 7, 14, 30, 90, 180, 365, max) |

**Response:** Object with:
- `prices`: `[[timestamp_ms, price], ...]`
- `market_caps`: `[[timestamp_ms, market_cap], ...]`
- `total_volumes`: `[[timestamp_ms, volume], ...]`

**Used in:** Price chart (detail page), ML prediction (dashboard)

---

#### GET /search
Search for coins by name or symbol.

**Parameters:**
| Param | Type | Description |
|---|---|---|
| `query` | string | Search term |

**Response:** Object with `coins` array: `[{id, name, symbol, thumb, market_cap_rank}, ...]`

**Used in:** Homepage search

---

#### GET /search/trending
Fetch top 7 trending coins.

**Response:** Object with `coins` array — each contains `item`: `{id, name, symbol, thumb, market_cap_rank, price_btc}`

**Used in:** Dashboard trending section

---

#### GET /global
Fetch global market statistics.

**Response:** Object with `data`:
- `total_market_cap`: `{usd: number}`
- `total_volume`: `{usd: number}`
- `active_cryptocurrencies`: `number`
- `market_cap_percentage`: `{btc: number}`

**Used in:** Dashboard market overview

---

## 2. Internal API Routes

### Authentication

#### POST /register
Create a new user account.

**Request Body:**
```
username=<string>&email=<string>&password=<string>&confirm_password=<string>
```

**Responses:**
- `302` → Redirect to login on success
- `200` → Render register page with flash errors

**Validations:**
- Username: min 3 chars, unique
- Email: valid format, unique
- Password: min 6 chars, must match confirm_password

---

#### POST /login
Authenticate user and create session.

**Request Body:**
```
username=<string>&password=<string>
```

**Responses:**
- `302` → Redirect to dashboard (or `next` param) on success
- `200` → Render login page with flash error on failure

**Session:** Sets `user_id` in Flask session via Flask-Login

---

#### GET /logout
Clear user session.

**Responses:**
- `302` → Redirect to index

**Session:** `logout_user()` clears Flask-Login session

---

### Market Data (Public)

#### GET /
Homepage — paginated coin list or search results.

**Query Params:**
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `search` | string | — | Search query (triggers search mode) |

**Template Context:** `coins`, `page`, `total_pages`, `is_search`, `search_query`, `user_watchlist_ids` (if authenticated)

---

#### GET /coin/{coin_id}
Coin detail page with price chart.

**Query Params:**
| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | 7 | Chart range (7, 30, 90) |

**Template Context:** `coin`, `current_price`, `price_change_24h`, `market_cap`, `total_volume`, `circulating_supply`, `ath`, `atl`, `market_extra` (from markets endpoint), `price_points` (for chart), `chart_days`, `in_watchlist` (if authenticated)

---

#### GET /about
Static about page.

---

### User Features (Protected — Require Login)

#### GET /dashboard
User dashboard with watchlist, market overview, trending, and predictions.

**Template Context:** `user`, `watchlist_coins` (with `prediction` attached), `global_data`, `trending_coins`

**Note:** Each watchlist coin has a `prediction` dict attached:
```python
{
    'signal': 'BUY',
    'signal_icon': 'trending-up',
    'confidence': 'High',
    'predicted_change_pct': 12.4,
    'current_price': 45000.0,
    'predicted_price': 50640.0,
    'slope': 0.32,
    'r2': 0.85
}
```

---

#### POST /watchlist/add/{coin_id}
Add coin to user's watchlist.

**Responses:** `302` → Redirect back to `referer` or dashboard

**Note:** If already in watchlist, no action taken. Flash success message on add.

---

#### POST /watchlist/remove/{coin_id}
Remove coin from user's watchlist.

**Responses:** `302` → Redirect back to `referer` or dashboard

**Note:** If not in watchlist, no action taken. Flash info message on remove.

---

#### GET/POST /profile
Edit user profile (username and email).

**GET:** Render profile form with current user data
**POST:** Update user record in database, flash success

**Validations:**
- Username: min 3 chars, unique
- Email: valid format, unique

---

#### GET/POST /change-password
Change user password.

**GET:** Render change password form
**POST:** Verify current password, update to new password

**Validations:**
- Current password: must match
- New password: min 6 chars, different from current
- Confirm: must match new password

---

### Theme

#### GET /theme
Toggle between light and dark mode.

**Responses:** `302` → Redirect to `referer` or index

**Note:** Toggles `theme` key in session: `'light'` ↔ `'dark'`. Changes `html` class on page.

---

### Admin (Protected — Require Admin)

#### GET /admin
Admin dashboard — manage user registrations.

**Access:** `current_user.is_admin == True`

**Template Context:** `pending_users`, `approved_users`

**Responses:**
- `200` → Render admin page
- `302` → Redirect to dashboard with flash error if not admin

---

#### POST /admin/approve/{user_id}
Approve a pending user (sets `is_approved = True`).

**Responses:** `302` → Redirect to admin

---

#### POST /admin/reject/{user_id}
Reject and delete a pending user.

**Responses:** `302` → Redirect to admin with flash error message

---

#### POST /admin/toggle-admin/{user_id}
Toggle admin status of a user.

**Responses:** `302` → Redirect to admin

**Note:** Cannot change own admin status.

---

#### POST /admin/delete-user/{user_id}
Delete a user and their watchlist.

**Responses:** `302` → Redirect to admin with flash error message

**Note:** Cannot delete self.

---

## 3. Database Models

### User
| Field | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(256) | NOT NULL |
| `is_admin` | BOOLEAN | DEFAULT FALSE |
| `is_approved` | BOOLEAN | DEFAULT FALSE |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| `password_hash` | VARCHAR(256) | NOT NULL |
| `created_at` | DATETIME | DEFAULT `func.now()` |

### Watchlist
| Field | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | FOREIGN KEY → `user.id` |
| `coin_id` | VARCHAR(100) | NOT NULL |

---

## 4. Response Codes

| Code | Meaning |
|---|---|
| 200 | OK — Page rendered successfully |
| 302 | Found — Redirect |
| 403 | Forbidden — Session/cookie issue (see: SESSION_COOKIE_SAMESITE) |
| 404 | Not Found — Invalid route |
| 500 | Internal Server Error |

---

## 5. Rate Limiting

CoinGecko free demo API has rate limits:
- ~10-30 requests/minute
- Demo API key has lower limits than paid

**Best Practice:** The app caches data implicitly through Flask's debug mode reloader. For production, add caching layer.

---

## 6. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `COINGECKO_API_KEY` | `REMOVED_API_KEY` | CoinGecko API key |
