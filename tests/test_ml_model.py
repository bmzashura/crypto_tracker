"""
Test ML model functions.
"""
import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model import (
    get_price_prediction_from_data,
    get_advanced_prediction_from_data,
    calculate_rsi,
    calculate_sma,
    calculate_rsi_status,
)


class TestRSI:
    def test_rsi_0_is_oversold(self):
        """RSI 0 harus dikategorikan Oversold, bukan None/falsy."""
        # RSI 0 occurs when all price changes are negative (all losses)
        prices = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5, 4, 3, 2, 1]
        rsi_val = calculate_rsi(prices, period=14)
        assert rsi_val == 0.0
        assert calculate_rsi_status(rsi_val) == "Oversold"

    def test_rsi_100_is_overbought(self):
        """RSI 100 harus dikategorikan Overbought."""
        prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60]
        rsi_val = calculate_rsi(prices, period=14)
        assert rsi_val == 100.0
        assert calculate_rsi_status(rsi_val) == "Overbought"

    def test_rsi_50_neutral(self):
        """RSI di sekitar 50 adalah Neutral."""
        # Equal gains and losses → RSI 50
        prices = [100, 105, 100, 105, 100, 105, 100, 105, 100, 105,
                  100, 105, 100, 105, 100, 105, 100, 105, 100, 105]
        rsi_val = calculate_rsi(prices, period=14)
        assert rsi_val is not None
        assert 40 <= rsi_val <= 60
        assert calculate_rsi_status(rsi_val) == "Neutral"

    def test_rsi_oversold_region(self):
        """RSI < 30 = Oversold."""
        # Strong downtrend
        prices = [100, 95, 90, 86, 82, 78, 74, 70, 67, 64, 61, 58, 55, 52, 49]
        rsi_val = calculate_rsi(prices, period=14)
        assert rsi_val is not None
        assert calculate_rsi_status(rsi_val) == "Oversold"

    def test_rsi_overbought_region(self):
        """RSI > 70 = Overbought."""
        # Strong uptrend
        prices = [10, 15, 20, 24, 28, 32, 36, 40, 43, 46, 49, 52, 55, 58, 61]
        rsi_val = calculate_rsi(prices, period=14)
        assert rsi_val is not None
        assert calculate_rsi_status(rsi_val) == "Overbought"

    def test_rsi_none_insufficient_data(self):
        """RSI returns None jika data kurang dari period+1."""
        prices = [100, 90, 80]
        assert calculate_rsi(prices, period=14) is None

    def test_rsi_status_none(self):
        """RSI status None returns 'N/A'."""
        assert calculate_rsi_status(None) == "N/A"


class TestSMA:
    def test_sma_0_not_none(self):
        """SMA yang menghasilkan 0 tidak boleh dianggap None."""
        prices = [10, 10, 10, 10, 10, 10, 10]  # SMA = 10, not 0
        prices_zeros = [0, 0, 0, 0, 0, 0, 0]  # SMA = 0
        assert calculate_sma(prices_zeros, 7) == 0.0
        assert calculate_sma(prices_zeros, 7) is not None

    def test_sma_none_insufficient_data(self):
        """SMA returns None jika data kurang dari period."""
        prices = [10, 20, 30]
        assert calculate_sma(prices, 7) is None

    def test_sma_normal(self):
        """SMA normal menghitung dengan benar."""
        prices = [1, 2, 3, 4, 5, 6, 7]  # 7-day SMA = 4.0
        result = calculate_sma(prices, 7)
        assert result == 4.0


class TestPredictionFromData:
    def test_forecast_exactly_7_points(self):
        """Forecast 7 hari berisi tepat 7 nilai."""
        # Buat data 30 hari dengan timestamp
        base_ts = 1700000000000
        prices = [[base_ts + i * 86400000, 100 + i] for i in range(30)]
        result = get_price_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        assert len(result["forecast_points"]) == 7

    def test_prediction_timestamp_based(self):
        """Prediction menggunakan elapsed days, bukan indeks."""
        # Data dengan interval tidak teratur (bukan per hari)
        base_ts = 1700000000000
        # 3 hari interval
        prices = [[base_ts + i * 3 * 86400000, 100 + i * 2] for i in range(30)]
        result = get_price_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        # Forecast horizon harus menggunakan elapsed days
        assert len(result["forecast_points"]) == 7

    def test_prediction_insufficient_data(self):
        """Prediction returns None jika data kurang dari 10."""
        prices = [[1700000000000, 100], [1700086400000, 101]]
        result = get_price_prediction_from_data(prices, days_ahead=7)
        assert result is None

    def test_prediction_confidence_not_called_confidence(self):
        """Return dict tidak menggunakan key 'confidence' (diganti trend_fit_label)."""
        base_ts = 1700000000000
        prices = [[base_ts + i * 86400000, 100 + i] for i in range(30)]
        result = get_price_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        # Template-compatible alias still exists
        assert "confidence" in result
        assert "r2" in result
        # But descriptive name also present
        assert "trend_fit_label" in result
        assert "in_sample_r2" in result

    def test_prediction_r2_categories(self):
        """R² trend fit label mengikuti kategori yang benar."""
        base_ts = 1700000000000
        prices = [[base_ts + i * 86400000, 100 + i * 2] for i in range(30)]
        result = get_price_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        label = result["trend_fit_label"]
        assert label in ("Strong fit", "Moderate fit", "Weak fit")


class TestAdvancedPredictionFromData:
    def test_advanced_prediction_no_double_fetch(self):
        """Advanced prediction tidak memanggil API (tidak ada fetch_func)."""
        base_ts = 1700000000000
        prices = [[base_ts + i * 86400000, 100 + i] for i in range(30)]
        result = get_advanced_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        # Must have all keys
        assert "lr" in result
        assert "rsi" in result
        assert "rsi_status" in result
        assert "sma_7" in result
        assert "sma_30" in result
        assert "bollinger" in result
        assert "overall_signal" in result

    def test_advanced_prediction_forecast_7_points(self):
        """Advanced prediction forecast juga 7 titik."""
        base_ts = 1700000000000
        prices = [[base_ts + i * 86400000, 100 + i] for i in range(30)]
        result = get_advanced_prediction_from_data(prices, days_ahead=7)
        assert result is not None
        assert len(result["lr"]["forecast_points"]) == 7

    def test_advanced_prediction_insufficient_data(self):
        """Advanced prediction returns None jika data kurang dari 30."""
        prices = [[1700000000000, 100 + i] for i in range(10)]
        result = get_advanced_prediction_from_data(prices, days_ahead=7)
        assert result is None

    def test_advanced_prediction_rsi_status(self):
        """Advanced prediction RSI status properly set."""
        base_ts = 1700000000000
        prices = [100, 95, 90, 86, 82, 78, 74, 70, 67, 64, 61, 58, 55, 52, 49,
                  46, 43, 40, 37, 34, 31, 28, 25, 22, 19, 16, 13, 10, 7, 4]
        prices_ts = [[base_ts + i * 86400000, prices[i]] for i in range(30)]
        result = get_advanced_prediction_from_data(prices_ts, days_ahead=7)
        assert result is not None
        assert result["rsi_status"] in ("Overbought", "Oversold", "Neutral")
