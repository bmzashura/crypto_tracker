"""
ml_model.py -- Machine Learning Price Prediction Module
CryptoTracker BMZ

Contains: Linear Regression prediction, RSI, SMA, Bollinger Bands, and advanced combined indicators.
"""

import numpy as np
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')


# =========================================================
# HELPER: Moving Average
# =========================================================

def _sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def _std(prices, period):
    """Standard deviation"""
    if len(prices) < period:
        return None
    return float(np.std(prices[-period:]))


# =========================================================
# LINEAR REGRESSION PREDICTION
# =========================================================

def get_price_prediction(coin_id, fetch_func, days_history=30, days_ahead=7):
    """
    Linear Regression-based price prediction.

    Args:
        coin_id: CoinGecko coin ID
        fetch_func: function(coin_id, days) -> {'prices': [[ts, price], ...]}
        days_history: training window in days (default 30)
        days_ahead: forecast horizon (default 7)

    Returns:
        dict with signal, confidence, predicted_change_pct, current_price,
        predicted_price, slope, r2, or None
    """
    try:
        data = fetch_func(coin_id, days=days_history)
        prices_data = data.get('prices', [])
        if len(prices_data) < 10:
            return None

        X = np.array(range(len(prices_data))).reshape(-1, 1)
        y = np.array([p[1] for p in prices_data])

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        current_price = y[-1]
        future_X = np.array([[len(prices_data) + days_ahead]])
        predicted_price = float(model.predict(future_X)[0])
        predicted_change_pct = float(((predicted_price - current_price) / current_price) * 100)
        slope_ratio = float((slope / current_price) * 100)
        r2 = float(model.score(X, y))
        confidence = 'High' if r2 > 0.7 else ('Medium' if r2 > 0.4 else 'Low')

        # Forecast line points (for chart)
        forecast_points = []
        for i in range(1, days_ahead + 1):
            fx = np.array([[len(prices_data) + i]])
            forecast_points.append(float(model.predict(fx)[0]))

        # Signal
        if slope_ratio > 0.5:
            signal, signal_icon = 'STRONG BUY', 'trending-up'
        elif slope_ratio > 0.1:
            signal, signal_icon = 'BUY', 'trending-up'
        elif slope_ratio < -0.5:
            signal, signal_icon = 'STRONG SELL', 'trending-down'
        elif slope_ratio < -0.1:
            signal, signal_icon = 'SELL', 'trending-down'
        else:
            signal, signal_icon = 'HOLD', 'minus'

        return {
            'signal': signal,
            'signal_icon': signal_icon,
            'confidence': confidence,
            'predicted_change_pct': predicted_change_pct,
            'current_price': float(current_price),
            'predicted_price': predicted_price,
            'slope': slope_ratio,
            'r2': r2,
            'forecast_points': forecast_points,  # list of predicted prices for chart
            'forecast_labels': [f'+{i}d' for i in range(1, days_ahead + 1)]
        }
    except Exception as e:
        print(f'Prediction error for {coin_id}: {e}')
        return None


# =========================================================
# RSI -- Relative Strength Index
# =========================================================

def calculate_rsi(prices, period=14):
    """
    RSI: measures speed and magnitude of price changes.
    RSI > 70 = Overbought (sell signal)
    RSI < 30 = Oversold (buy signal)

    Returns: float 0-100, or None
    """
    try:
        if len(prices) < period + 1:
            return None
        closes = np.array(prices)
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = float(np.mean(gains[-period:]))
        avg_loss = float(np.mean(losses[-period:]))
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(float(100 - (100 / (1 + rs))), 2)
    except Exception:
        return None


def calculate_rsi_status(rsi_val):
    """Return RSI status string, properly handling RSI=0 as Oversold."""
    if rsi_val is None:
        return 'N/A'
    if rsi_val > 70:
        return 'Overbought'
    if rsi_val < 30:
        return 'Oversold'
    return 'Neutral'


# =========================================================
# SMA -- Simple Moving Averages
# =========================================================

def calculate_sma(prices, period):
    """Simple Moving Average -- smooth price line"""
    result = _sma(prices, period)
    return round(result, 4) if result is not None else None


def calculate_sma_points(prices_data, period):
    """
    Returns SMA values for each price point.
    For overlay on chart.
    """
    try:
        if len(prices_data) < period:
            return []
        result = []
        prices = [p[1] for p in prices_data]
        for i in range(period - 1, len(prices)):
            result.append(float(np.mean(prices[i - period + 1:i + 1])))
        return result
    except Exception:
        return []


# =========================================================
# BOLLINGER BANDS
# =========================================================

def calculate_bollinger(prices, period=20, num_std=2):
    """
    Bollinger Bands: envelope around price based on volatility.
    Upper = SMA + (std * num_std)
    Lower = SMA - (std * num_std)
    When bands squeeze = low volatility (breakout coming)
    When bands expand = high volatility
    """
    try:
        if len(prices) < period:
            return None
        sma_val = _sma(prices, period)
        std_val = _std(prices, period)
        if sma_val is None or std_val is None:
            return None
        upper = sma_val + (std_val * num_std)
        lower = sma_val - (std_val * num_std)
        return {
            'upper': round(upper, 4),
            'middle': round(sma_val, 4),
            'lower': round(lower, 4),
            'bandwidth': round(((upper - lower) / sma_val) * 100, 2)  # % bandwidth
        }
    except Exception:
        return None


def calculate_bollinger_points(prices_data, period=20, num_std=2):
    """
    Returns Bollinger Band values for each point.
    For overlay on chart.
    """
    try:
        if len(prices_data) < period:
            return []
        result = {'upper': [], 'middle': [], 'lower': []}
        prices = [p[1] for p in prices_data]
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            sma = np.mean(window)
            std = np.std(window)
            result['upper'].append(float(sma + std * num_std))
            result['middle'].append(float(sma))
            result['lower'].append(float(sma - std * num_std))
        return result
    except Exception:
        return []


# =========================================================
# ADVANCED PREDICTION -- Combined All Indicators
# =========================================================

def get_advanced_prediction(coin_id, fetch_func, days_history=30, days_ahead=7):
    """
    Combines: Linear Regression + RSI + SMA + Bollinger Bands + Volume analysis.

    Returns dict with:
      - lr_prediction: Linear Regression forecast
      - rsi: RSI value + status
      - sma: SMA-7, SMA-30, crossover signal
      - bollinger: bands + position analysis
      - overall_signal: combined BUY/SELL/HOLD
    """
    try:
        data = fetch_func(coin_id, days=days_history)
        prices_data = data.get('prices', [])
        if len(prices_data) < 30:
            return None

        prices = [p[1] for p in prices_data]
        timestamps = [p[0] for p in prices_data]

        # 1. Linear Regression
        lr = get_price_prediction(coin_id, fetch_func, days_history, days_ahead)

        # 2. RSI (14-period)
        rsi_val = calculate_rsi(prices, 14)
        rsi_status = 'Overbought' if rsi_val and rsi_val > 70 else \
                      ('Oversold' if rsi_val and rsi_val < 30 else 'Neutral')

        # 3. SMA Crossover (only significant diff counts as signal)
        sma_7 = calculate_sma(prices, 7)
        sma_30 = calculate_sma(prices, 30)
        sma_diff_pct = 0
        if sma_7 and sma_30 and sma_30 > 0:
            sma_diff_pct = ((sma_7 - sma_30) / sma_30) * 100
        if sma_7 and sma_30:
            if sma_diff_pct > 1.0:       # 7 is more than 1% above 30
                sma_signal = 'BULLISH'
                sma_icon = 'trending-up'
            elif sma_diff_pct < -1.0:    # 7 is more than 1% below 30
                sma_signal = 'BEARISH'
                sma_icon = 'trending-down'
            else:
                sma_signal = 'NEUTRAL'   # too close -- ignore
                sma_icon = 'minus'
        else:
            sma_signal = 'N/A'
            sma_icon = 'minus'

        # 4. Bollinger Bands
        bb = calculate_bollinger(prices, 20)
        if bb and prices[-1]:
            current = prices[-1]
            if current > bb['upper']:
                bb_position = 'Above Upper Band (Strong Buy)'
            elif current > bb['middle']:
                bb_position = 'Above Middle (mild buy signal)'
            elif current > bb['lower']:
                bb_position = 'Below Middle (mild sell signal)'
            else:
                bb_position = 'Below Lower Band (Strong Sell)'
            bb['position'] = bb_position

        # 5. Overall Signal: based on predicted % change (7-day forecast)
        # More intuitive: predicted change > +5% = BUY, < -5% = SELL, else HOLD
        # Confidence (R2) must also support the signal
        if lr:
            pred = lr['predicted_change_pct']
            r2 = lr['r2']
            # Only signal BUY/SELL if confidence is at least Medium (R2 > 0.4)
            if r2 < 0.3:
                overall = 'HOLD'
                overall_icon = 'minus'
            elif pred > 10:
                overall = 'STRONG BUY'
                overall_icon = 'trending-up'
            elif pred > 5:
                overall = 'BUY'
                overall_icon = 'trending-up'
            elif pred < -10:
                overall = 'STRONG SELL'
                overall_icon = 'trending-down'
            elif pred < -5:
                overall = 'SELL'
                overall_icon = 'trending-down'
            else:
                overall = 'HOLD'
                overall_icon = 'minus'
        else:
            overall = 'HOLD'
            overall_icon = 'minus'

        return {
            'lr': lr,
            'rsi': rsi_val,
            'rsi_status': rsi_status,
            'sma_7': sma_7,
            'sma_30': sma_30,
            'sma_diff_pct': round(sma_diff_pct, 3),
            'sma_signal': sma_signal,
            'sma_icon': sma_icon,
            'bollinger': bb,
            'overall_signal': overall,
            'overall_icon': overall_icon,
            'prices': prices[-30:],
            'timestamps': timestamps[-30:],
        }

    except Exception as e:
        print(f'Advanced prediction error for {coin_id}: {e}')
        return None


# =========================================================
# FROM-DATA WRAPPERS (no API fetch, uses existing data)
# =========================================================

def get_price_prediction_from_data(prices_data, days_ahead=7):
    """
    Linear Regression prediction using pre-fetched price data.
    Uses elapsed days from first timestamp for proper forecast horizon.

    Args:
        prices_data: list of [timestamp_ms, price] (from CoinGecko format)
        days_ahead: forecast horizon (default 7)

    Returns:
        dict with signal, trend_fit_label, in_sample_r2, predicted_change_pct,
        current_price, predicted_price, slope, forecast_points,
        or None if insufficient data
    """
    try:
        if len(prices_data) < 10:
            return None

        # Convert timestamps to elapsed days (anchor at first observation)
        timestamps_ms = np.array([p[0] for p in prices_data], dtype=float)
        prices = np.array([p[1] for p in prices_data], dtype=float)

        elapsed_days = (timestamps_ms - timestamps_ms[0]) / 1000.0 / 86400.0

        # Fit model on elapsed days
        model = LinearRegression()
        model.fit(elapsed_days.reshape(-1, 1), prices)

        slope = float(model.coef_[0])
        current_price = float(prices[-1])
        last_day = float(elapsed_days[-1])

        # Forecast exactly `days_ahead` days from last observation
        future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
        forecast_prices = model.predict(future_days)
        predicted_price = float(forecast_prices[-1])
        predicted_change_pct = float(((predicted_price - current_price) / current_price) * 100)
        slope_ratio = float((slope / current_price) * 100) if current_price > 0 else 0.0
        in_sample_r2 = float(model.score(elapsed_days.reshape(-1, 1), prices))

        # Trend fit label (not "confidence")
        if in_sample_r2 >= 0.70:
            trend_fit_label = 'Strong fit'
        elif in_sample_r2 >= 0.40:
            trend_fit_label = 'Moderate fit'
        else:
            trend_fit_label = 'Weak fit'

        # Signal
        if slope_ratio > 0.5:
            signal, signal_icon = 'STRONG BUY', 'trending-up'
        elif slope_ratio > 0.1:
            signal, signal_icon = 'BUY', 'trending-up'
        elif slope_ratio < -0.5:
            signal, signal_icon = 'STRONG SELL', 'trending-down'
        elif slope_ratio < -0.1:
            signal, signal_icon = 'SELL', 'trending-down'
        else:
            signal, signal_icon = 'HOLD', 'minus'

        return {
            'signal': signal,
            'signal_icon': signal_icon,
            'trend_fit_label': trend_fit_label,   # Human-readable R² label
            'in_sample_r2': in_sample_r2,         # Raw R² value
            # Template-compatible aliases:
            'confidence': trend_fit_label,
            'r2': in_sample_r2,
            'predicted_change_pct': predicted_change_pct,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'slope': slope_ratio,
            'forecast_points': [float(p) for p in forecast_prices],
            'forecast_labels': [f'+{i}d' for i in range(1, days_ahead + 1)],
        }
    except Exception as e:
        print(f'Prediction from data error: {e}')
        return None


def get_advanced_prediction_from_data(prices_data, days_ahead=7):
    """
    Advanced prediction using pre-fetched price data.
    Combines: Linear Regression (from_data) + RSI + SMA + Bollinger Bands.
    Does NOT call any API — uses only provided data.

    Args:
        prices_data: list of [timestamp_ms, price]
        days_ahead: forecast horizon (default 7)

    Returns:
        dict with lr, rsi, rsi_status, sma_7, sma_30, sma_diff_pct,
        sma_signal, bollinger, overall_signal, overall_icon,
        prices, timestamps, or None if insufficient data
    """
    try:
        if len(prices_data) < 30:
            return None

        timestamps_ms = np.array([p[0] for p in prices_data], dtype=float)
        prices = np.array([p[1] for p in prices_data], dtype=float)

        # 1. Linear Regression (timestamp-based)
        lr = get_price_prediction_from_data(prices_data, days_ahead)

        # 2. RSI (uses price list)
        rsi_val = calculate_rsi(prices.tolist(), 14)
        rsi_status = calculate_rsi_status(rsi_val)

        # 3. SMA Crossover
        sma_7 = calculate_sma(prices.tolist(), 7)
        sma_30 = calculate_sma(prices.tolist(), 30)
        sma_diff_pct = 0.0
        if sma_7 is not None and sma_30 is not None and sma_30 > 0:
            sma_diff_pct = ((sma_7 - sma_30) / sma_30) * 100
        if sma_7 is not None and sma_30 is not None:
            if sma_diff_pct > 1.0:
                sma_signal = 'BULLISH'
                sma_icon = 'trending-up'
            elif sma_diff_pct < -1.0:
                sma_signal = 'BEARISH'
                sma_icon = 'trending-down'
            else:
                sma_signal = 'NEUTRAL'
                sma_icon = 'minus'
        else:
            sma_signal = 'N/A'
            sma_icon = 'minus'

        # 4. Bollinger Bands
        bb = calculate_bollinger(prices.tolist(), 20)
        if bb is not None and len(prices) > 0:
            current = float(prices[-1])
            if current > bb['upper']:
                bb_position = 'Above upper band'
            elif current > bb['middle']:
                bb_position = 'Above middle band'
            elif current > bb['lower']:
                bb_position = 'Below middle band'
            else:
                bb_position = 'Below lower band'
            bb['position'] = bb_position

        # 5. Overall Signal (heuristic, not a trained model)
        if lr:
            pred = lr['predicted_change_pct']
            r2 = lr['in_sample_r2']
            if r2 < 0.3:
                overall = 'HOLD'
                overall_icon = 'minus'
            elif pred > 10:
                overall = 'STRONG BUY'
                overall_icon = 'trending-up'
            elif pred > 5:
                overall = 'BUY'
                overall_icon = 'trending-up'
            elif pred < -10:
                overall = 'STRONG SELL'
                overall_icon = 'trending-down'
            elif pred < -5:
                overall = 'SELL'
                overall_icon = 'trending-down'
            else:
                overall = 'HOLD'
                overall_icon = 'minus'
        else:
            overall = 'HOLD'
            overall_icon = 'minus'

        return {
            'lr': lr,
            'rsi': rsi_val,
            'rsi_status': rsi_status,
            'sma_7': sma_7,
            'sma_30': sma_30,
            'sma_diff_pct': round(sma_diff_pct, 3),
            'sma_signal': sma_signal,
            'sma_icon': sma_icon,
            'bollinger': bb,
            'overall_signal': overall,
            'overall_icon': overall_icon,
            'prices': prices[-30:].tolist(),
            'timestamps': timestamps_ms[-30:].tolist(),
        }
    except Exception as e:
        print(f'Advanced prediction from data error: {e}')
        return None
