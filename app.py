from flask import Flask, render_template, request, redirect, url_for, session
import requests
import math

app = Flask(__name__)
app.secret_key = 'crypto-tracker-secret-key-2026'

# CoinGecko API Configuration
API_KEY = 'REMOVED_API_KEY'
BASE_URL = 'https://api.coingecko.com/api/v3'
HEADERS = {'x-cg-demo-api-key': API_KEY}

# Cache for storing coin data
cache = {}
CACHE_DURATION = 300  # 5 minutes


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


@app.route('/')
def index():
    """Homepage - Display list of cryptocurrencies"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '')

    if search_query:
        # Search mode
        search_results = fetch_search(search_query)
        coins = search_results.get('coins', [])[:20]
        total_pages = 1
        is_search = True
    else:
        # Normal market data mode
        coins = fetch_coins(per_page=per_page, page=page)
        total_pages = math.ceil(100 / per_page)  # CoinGecko has ~100 coins
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


@app.route('/coin/<coin_id>')
def coin_detail(coin_id):
    """Detail page for a specific coin"""
    coin = fetch_coin_detail(coin_id)

    if not coin:
        return render_template('error.html', message='Coin not found or API error')

    # Get market data
    market_data = coin.get('market_data', {})
    current_price = market_data.get('current_price', {})
    price_change_24h = market_data.get('price_change_percentage_24h', 0)
    market_cap = market_data.get('market_cap', {})
    total_volume = market_data.get('total_volume', {})
    circulating_supply = market_data.get('circulating_supply', 0)
    ath = market_data.get('ath', {})
    atl = market_data.get('atl', {})

    # Parse community stats
    community_data = coin.get('community_score', 0) or 0
    developer_data = coin.get('developer_score', 0) or 0

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
        community_data=community_data,
        developer_data=developer_data,
        format_number=format_number,
        format_market_cap=format_market_cap
    )


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


if __name__ == '__main__':
    print('Starting Crypto Tracker Flask App...')
    print('API Key:', API_KEY[:10] + '...')
    print('Open http://127.0.0.1:5000 in your browser')
    app.run(debug=True, port=5000)