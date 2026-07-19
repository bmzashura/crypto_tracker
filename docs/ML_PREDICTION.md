# ML Price Prediction — Documentation
**CryptoTracker BMZ | Module: `ml_model.py`**

---

## Overview

The app uses **Linear Regression** as the primary price prediction engine. Three additional indicators (RSI, SMA, Bollinger Bands) are computed and displayed on the detail page as **informational reference only** — they do not influence the trading signal.

| Indicator | Type | Purpose | Affects Signal? |
|---|---|---|---|
| **Linear Regression** | Trend | Predict price direction and magnitude | **YES** |
| **RSI** | Momentum | Detect overbought / oversold | No (display only) |
| **SMA Crossover** | Trend | Identify bullish / bearish momentum | No (display only) |
| **Bollinger Bands** | Volatility | Measure price envelope and breakout zones | No (display only) |

---

## 1. Linear Regression

### Method
Simple Linear Regression fits a straight line through 30 days of price data, then extrapolates to day `n + 7`.

```
y = mx + c
  m = slope (daily trend direction x magnitude)
  c = intercept
```

### Signal Classification

| Predicted Change % | Signal |
|---|---|
| > +10% | STRONG BUY |
| +5% to +10% | BUY |
| -5% to +5% | HOLD |
| -10% to -5% | SELL |
| < -10% | STRONG SELL |

### Confidence (R² Score)

| R² | Confidence | Meaning |
|---|---|---|
| > 0.7 | High | Model fits data very well |
| 0.4 – 0.7 | Medium | Moderate fit |
| < 0.3 | Low | Weak fit — **HOLD regardless of predicted %** |

**Important:** If R² < 0.3, the signal is always **HOLD** regardless of predicted change, because the model fit is too weak to be reliable.

### Implementation (`ml_model.py`)

```python
def get_price_prediction(coin_id, fetch_func, days_history=30, days_ahead=7):
    # 1. Fetch 30 days of price history
    data = fetch_func(coin_id, days=days_history)
    prices = data['prices']  # [[ts, price], ...]

    # 2. Build X (day index) and y (price)
    X = np.array(range(len(prices))).reshape(-1, 1)
    y = np.array([p[1] for p in prices])

    # 3. Fit Linear Regression
    model = LinearRegression()
    model.fit(X, y)

    # 4. Predict at day n + 7
    slope = model.coef_[0]
    current_price = y[-1]
    predicted_price = model.predict([[len(prices) + days_ahead]])[0]

    # 5. Calculate metrics
    predicted_change_pct = ((predicted_price - current_price) / current_price) * 100
    r2 = model.score(X, y)  # R² confidence
    confidence = 'High' if r2 > 0.7 else ('Medium' if r2 > 0.4 else 'Low')

    # 6. Classify signal
    if r2 < 0.3:
        signal = 'HOLD'
    elif predicted_change_pct > 10:
        signal = 'STRONG BUY'
    elif predicted_change_pct > 5:
        signal = 'BUY'
    elif predicted_change_pct < -10:
        signal = 'STRONG SELL'
    elif predicted_change_pct < -5:
        signal = 'SELL'
    else:
        signal = 'HOLD'
```

---

## 2. RSI — Relative Strength Index (Display Only)

### Method
RSI measures the magnitude and speed of price changes over a 14-period window.

```
RSI = 100 - (100 / (1 + RS))
RS  = average_gain / average_loss
```

| RSI Value | Status | Interpretation |
|---|---|---|
| > 70 | Overbought | Price may be inflated |
| < 30 | Oversold | Price may be undervalued |
| 30–70 | Neutral | No extreme condition |

```python
def calculate_rsi(prices, period=14):
    closes = np.array(prices)
    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain  = np.mean(gains[-period:])
    avg_loss  = np.mean(losses[-period:])
    rs  = avg_gain / avg_loss if avg_loss != 0 else 100
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)
```

---

## 3. SMA — Simple Moving Average (Display Only)

### Method
SMA smooths price data over a fixed period. The **crossover** of SMA-7 and SMA-30 is a classic trend signal.

A crossover is considered significant only when the difference between SMA-7 and SMA-30 is **greater than 1%**.

| Condition | Signal |
|---|---|
| SMA-7 > SMA-30 by > 1% | BULLISH |
| SMA-7 < SMA-30 by > 1% | BEARISH |
| Difference < 1% | NEUTRAL |

```python
def calculate_sma(prices, period):
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))
```

---

## 4. Bollinger Bands (Display Only)

### Method
Bollinger Bands plot a 20-period SMA with upper/lower bands at ±2 standard deviations.

| Position | Interpretation |
|---|---|
| Price above upper band | Above volatility ceiling |
| Price between upper and middle | Mild bullish |
| Price between middle and lower | Mild bearish |
| Price below lower band | Below volatility floor |

### Formula
```
Upper Band  = SMA(20) + (2 x STD)
Middle Band = SMA(20)
Lower Band  = SMA(20) - (2 x STD)
Bandwidth   = ((Upper - Lower) / SMA) x 100  (volatility metric)
```

```python
def calculate_bollinger(prices, period=20, num_std=2):
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper = sma + std * num_std
    lower = sma - std * num_std
    return {
        'upper': round(upper, 4),
        'middle': round(sma, 4),
        'lower': round(lower, 4),
        'bandwidth': round(((upper - lower) / sma) * 100, 2)
    }
```

---

## 5. Advanced Prediction (`get_advanced_prediction`)

Combines all indicators into a single response. The signal is determined by LR only; RSI/SMA/Bollinger are included as informational fields.

```python
def get_advanced_prediction(coin_id, fetch_func, days_history=30, days_ahead=7):
    # 1. Linear Regression
    lr = get_price_prediction(...)

    # 2. RSI (informational)
    rsi_val = calculate_rsi(prices, 14)
    rsi_status = 'Overbought' if rsi_val > 70 else ('Oversold' if rsi_val < 30 else 'Neutral')

    # 3. SMA (informational)
    sma_7 = calculate_sma(prices, 7)
    sma_30 = calculate_sma(prices, 30)
    sma_diff_pct = ((sma_7 - sma_30) / sma_30) * 100
    if sma_diff_pct > 1:
        sma_signal = 'BULLISH'
    elif sma_diff_pct < -1:
        sma_signal = 'BEARISH'
    else:
        sma_signal = 'NEUTRAL'

    # 4. Bollinger Bands (informational)
    bb = calculate_bollinger(prices, 20)

    return {
        'lr': lr,
        'rsi': rsi_val,
        'rsi_status': rsi_status,
        'sma_7': sma_7,
        'sma_30': sma_30,
        'sma_diff_pct': sma_diff_pct,
        'sma_signal': sma_signal,
        'bollinger': bb,
        'overall_signal': lr['signal'],
        'overall_icon': lr['icon'],
        'prices': prices,       # price points for chart
        'timestamps': timestamps,  # timestamps for chart
    }
```

---

## Display on Detail Page

### Signal Card (Logged-in users only)
Shows the overall signal with:
- Signal name (STRONG BUY / BUY / HOLD / SELL / STRONG SELL)
- Predicted 7-day change %
- Current price
- Predicted price (7 days ahead)
- Confidence level + R² score

### Price Chart (All users)
Shows historical price line. For logged-in users, also shows:
- **Forecast line** (LR prediction, 7 days ahead, purple dashed)

### Indicator Display (Logged-in users)
Three informational cards:
- **RSI Card** — RSI value (0-100) + overbought/oversold/neutral bar
- **SMA Card** — SMA-7 vs SMA-30 values + BULLISH/BEARISH/NEUTRAL badge
- **Bollinger Card** — Upper/Middle/Lower band values + current position

---

## Access Control

| Feature | Public | Logged In |
|---|---|---|
| Price chart | Yes | Yes |
| Price history (7D/30D/90D) | Yes | Yes |
| ML Signal card | No | Yes |
| RSI/SMA/Bollinger cards | No | Yes |
| Forecast line on chart | No | Yes |
| Signal filter on market page | No | Yes |

---

## File Locations

| File | Contents |
|---|---|
| `ml_model.py` | All ML functions (LR, RSI, SMA, Bollinger, Advanced) |
| `app.py` | `get_advanced_prediction()` called in `coin_detail()` and `index()` routes |

---

## Limitations

1. **Linear** — LR assumes linear trend; markets are often non-linear
2. **No external factors** — ignores news, macro events, volume
3. **Short horizon** — 7-day forecast; accuracy drops for longer periods
4. **Crypto volatility** — Sudden news/events can invalidate patterns
5. **R² threshold** — Conservative threshold (0.3) may miss valid signals

> **Disclaimer:** For educational/demonstration purposes only. Not financial advice.

---

## Dependencies

```
numpy>=1.24.0
scikit-learn>=1.3.0
```
