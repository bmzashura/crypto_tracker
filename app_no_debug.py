from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import math
import os
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crypto-tracker-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# CoinGecko API Configuration
API_KEY = os.environ.get('COINGECKO_API_KEY', 'REMOVED_API_KEY')
BASE_URL = 'https://api.coingecko.com/api/v3'
HEADERS = {'x-cg-demo-api-key': API_KEY}

# Cache for storing coin data
cache = {}
CACHE_DURATION = 300  # 5 minutes


# =====================
# Database Models
# =====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin_id = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', backref=db.backref('watchlist', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================
# Helper Functions
# =====================

def fetch_coins(per_page=20, page=1, vs_currency='usd', order='market_cap_desc'):
    """Fetch coin market data from CoinGecko"""
    url = f'{BASE_URL}/coins/markets'
    params = {
        'vs_currency': vs_currency,
        'order': order,
        'per_page': per_page,
        'page': page,
        'sparkline': 'false',
        'price_change_percentage': '24h'
    }
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching coins: {e}')
        return []


def fetch_coin_detail(coin_id):
    """Fetch detailed info for a specific coin"""
    url = f'{BASE_URL}/coins/{coin_id}'
    params = {
        'localization': 'false',
        'tickers': 'false',
        'community_data': 'false',
        'developer_data': 'false'
    }
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching coin detail: {e}')
        return None


def fetch_search(query):
    """Search for coins"""
    url = f'{BASE_URL}/search'
    try:
        response = requests.get(url, params={'query': query}, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error searching: {e}')
        return {'coins': []}


def fetch_global_stats():
    """Fetch global market data"""
    url = f'{BASE_URL}/global'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.RequestException as e:
        print(f'Error fetching global stats: {e}')
        return {}


def fetch_trending():
    """Fetch trending coins"""
    url = f'{BASE_URL}/search/trending'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('coins', [])
    except requests.exceptions.RequestException as e:
        print(f'Error fetching trending: {e}')
        return []


def fetch_price_history(coin_id, days=7):
    """Fetch price history for a coin"""
    url = f'{BASE_URL}/coins/{coin_id}/market_chart'
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching price history: {e}')
        return {'prices': []}


def get_price_prediction(coin_id, days_history=30, days_ahead=7):
    """
    Linear Regression-based price prediction.
    Returns: dict with signal, confidence, predicted_change_pct, current_price, predicted_price
    """
    try:
        data = fetch_price_history(coin_id, days=days_history)
        prices = data.get('prices', [])

        if len(prices) < 10:
            return None

        # Build X (day index) and y (price)
        X = np.array(range(len(prices))).reshape(-1, 1)
        y = np.array([p[1] for p in prices])

        # Fit Linear Regression
        model = LinearRegression()
        model.fit(X, y)

        # Slope indicates trend direction and strength
        slope = model.coef_[0]
        current_price = y[-1]

        # Predict future price
        future_X = np.array([[len(prices) + days_ahead]])
        predicted_price = model.predict(future_X)[0]

        # Calculate predicted change percentage
        predicted_change_pct = ((predicted_price - current_price) / current_price) * 100

        # Signal based on slope relative to price
        slope_ratio = (slope / current_price) * 100  # % per day

        # Confidence based on R^2 score
        r2 = model.score(X, y)
        confidence = 'High' if r2 > 0.7 else ('Medium' if r2 > 0.4 else 'Low')

        # Signal classification
        if slope_ratio > 0.5:
            signal = 'STRONG BUY'
            signal_icon = '^'
        elif slope_ratio > 0.1:
            signal = 'BUY'
            signal_icon = '/\'
        elif slope_ratio < -0.5:
            signal = 'STRONG SELL'
            signal_icon = '\/'
        elif slope_ratio < -0.1:
            signal = 'SELL'
            signal_icon = '\/'
        else:
            signal = 'HOLD'
            signal_icon = '->'

        return {
            'signal': signal,
            'signal_icon': signal_icon,
            'confidence': confidence,
            'predicted_change_pct': predicted_change_pct,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'slope': slope_ratio,
            'r2': r2
        }
    except Exception as e:
        print(f'Prediction error for {coin_id}: {e}')
        return None


def format_number(num):
    """Format number with appropriate suffix"""
    if num is None:
        return 'N/A'
    try:
        num = float(num)
        if num >= 1_000_000_000_000:
            return f'${num / 1_000_000_000_000:.2f}T'
        elif num >= 1_000_000_000:
            return f'${num / 1_000_000_000:.2f}B'
        elif num >= 1_000_000:
            return f'${num / 1_000_000:.2f}M'
        elif num >= 1_000:
            return f'${num:,.2f}'
        else:
            return f'${num:.4f}'
    except (ValueError, TypeError):
        return str(num)


def format_market_cap(num):
    """Format market cap with appropriate suffix"""
    if num is None:
        return 'N/A'
    try:
        num = float(num)
        if num >= 1_000_000_000_000:
            return f'${num / 1_000_000_000_000:.2f}T'
        elif num >= 1_000_000_000:
            return f'${num / 1_000_000_000:.2f}B'
        elif num >= 1_000_000:
            return f'${num / 1_000_000:.2f}M'
        else:
            return f'${num:,.0f}'
    except (ValueError, TypeError):
        return str(num)


# =====================
# Auth Routes
# =====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Clear any lingering flashes from previous pages
    session.pop('_flashes', None)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Clear any lingering flashes from previous pages
    session.pop('_flashes', None)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# =====================
# Main Routes
# =====================

@app.route('/')
def index():
    """Homepage - Display list of cryptocurrencies"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '')

    if search_query:
        search_results = fetch_search(search_query)
        coins = search_results.get('coins', [])[:20]
        total_pages = 1
        is_search = True
    else:
        coins = fetch_coins(per_page=per_page, page=page)
        total_pages = math.ceil(100 / per_page)
        is_search = False

    return render_template(
        'index.html',
        coins=coins,
        page=page,
        total_pages=total_pages,
        is_search=is_search,
        search_query=search_query,
        format_number=format_number,
        format_market_cap=format_market_cap
    )


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with watchlist, market stats, and trending"""
    user_watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
    watchlist_coin_ids = [w.coin_id for w in user_watchlist]

    watchlist_coins = []
    if watchlist_coin_ids:
        url = f'{BASE_URL}/coins/markets'
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(watchlist_coin_ids),
            'order': 'market_cap_desc',
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            watchlist_coins_raw = response.json()

            # Attach prediction to each coin
            for coin in watchlist_coins_raw:
                prediction = get_price_prediction(coin['id'], days_history=30, days_ahead=7)
                coin['prediction'] = prediction
            watchlist_coins = watchlist_coins_raw
        except requests.exceptions.RequestException:
            pass

    # Fetch global market stats
    global_data = fetch_global_stats()

    # Fetch trending coins
    trending_data = fetch_trending()
    trending_coins = []
    for item in trending_data[:7]:
        coin = item.get('item', {})
        trending_coins.append({
            'id': coin.get('id'),
            'name': coin.get('name'),
            'symbol': coin.get('symbol'),
            'thumb': coin.get('thumb'),
            'market_cap_rank': coin.get('market_cap_rank'),
            'price_btc': coin.get('price_btc'),
        })

    return render_template(
        'dashboard.html',
        user=current_user,
        watchlist_coins=watchlist_coins,
        global_data=global_data,
        trending_coins=trending_coins,
        format_number=format_number,
        format_market_cap=format_market_cap
    )


@app.route('/watchlist/add/<coin_id>', methods=['POST'])
@login_required
def watchlist_add(coin_id):
    existing = Watchlist.query.filter_by(user_id=current_user.id, coin_id=coin_id).first()
    if not existing:
        item = Watchlist(user_id=current_user.id, coin_id=coin_id)
        db.session.add(item)
        db.session.commit()
        flash(f'{coin_id} added to watchlist.', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/watchlist/remove/<coin_id>', methods=['POST'])
@login_required
def watchlist_remove(coin_id):
    item = Watchlist.query.filter_by(user_id=current_user.id, coin_id=coin_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f'{coin_id} removed from watchlist.', 'info')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip().lower()

        errors = []

        if not new_username or len(new_username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not new_email or '@' not in new_email:
            errors.append('Valid email is required.')
        if new_username != current_user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                errors.append('Username already taken.')
        if new_email != current_user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile.html', user=current_user)

        current_user.username = new_username
        current_user.email = new_email
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pass = request.form.get('current_password', '')
        new_pass = request.form.get('new_password', '')
        confirm_pass = request.form.get('confirm_password', '')

        errors = []

        if not current_user.check_password(current_pass):
            errors.append('Current password is incorrect.')
        if not new_pass or len(new_pass) < 6:
            errors.append('New password must be at least 6 characters.')
        if new_pass != confirm_pass:
            errors.append('New passwords do not match.')
        if current_pass == new_pass:
            errors.append('New password must be different from current password.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('change_password.html')

        current_user.set_password(new_pass)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')


@app.route('/coin/<coin_id>')
def coin_detail(coin_id):
    """Detail page for a specific coin"""
    coin = fetch_coin_detail(coin_id)

    if not coin:
        return render_template('error.html', message='Coin not found or API error')

    in_watchlist = False
    if current_user.is_authenticated:
        existing = Watchlist.query.filter_by(user_id=current_user.id, coin_id=coin_id).first()
        in_watchlist = existing is not None

    market_data = coin.get('market_data', {})
    current_price = market_data.get('current_price', {})
    price_change_24h = market_data.get('price_change_percentage_24h', 0)
    market_cap = market_data.get('market_cap', {})
    total_volume = market_data.get('total_volume', {})
    circulating_supply = market_data.get('circulating_supply', 0)
    ath = market_data.get('ath', {})
    atl = market_data.get('atl', {})

    # Price history for chart (default 7 days)
    days = request.args.get('days', 7, type=int)
    price_history = fetch_price_history(coin_id, days=days)
    price_points = price_history.get('prices', [])

    # Fetch extra market data from markets endpoint
    market_extra = {}
    try:
        markets_url = f'{BASE_URL}/coins/markets'
        params = {'vs_currency': 'usd', 'ids': coin_id}
        market_resp = requests.get(markets_url, params=params, headers=HEADERS, timeout=10)
        market_resp.raise_for_status()
        market_list = market_resp.json()
        if market_list:
            market_extra = market_list[0]
    except Exception:
        pass

    return render_template(
        'detail.html',
        coin=coin,
        current_price=current_price,
        price_change_24h=price_change_24h,
        market_cap=market_cap,
        total_volume=total_volume,
        circulating_supply=circulating_supply,
        ath=ath,
        atl=atl,
        market_extra=market_extra,
        in_watchlist=in_watchlist,
        price_points=price_points,
        chart_days=days,
        format_number=format_number,
        format_market_cap=format_market_cap
    )


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/theme')
def theme():
    """Toggle between light and dark theme"""
    current = session.get('theme', 'light')
    session['theme'] = 'dark' if current == 'light' else 'light'
    return redirect(request.referrer or url_for('index'))


# =====================
# Init & Run
# =====================

def init_db():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    init_db()
    print('Starting Crypto Tracker Flask App...')
    print(f'API Key: {API_KEY[:10]}...')
    print('Open http://127.0.0.1:5000 in your browser')
    app.run(debug=False, port=5000)
