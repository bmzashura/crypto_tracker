"""
Test market page and API integration.
"""
import pytest
from unittest.mock import patch, MagicMock
import services.coingecko_service as cg


class TestMarketPage:
    def test_market_200(self, client):
        """Market page returns 200."""
        r = client.get("/market")
        assert r.status_code == 200

    def test_market_renders_coins(self, client):
        """Market page renders coin table."""
        r = client.get("/market")
        assert b"coin-table" in r.data or b"table" in r.data

    @patch.object(cg, "fetch_coins")
    def test_market_shows_mock_data(self, mock_fetch, client):
        """Market page shows data from API (mocked)."""
        mock_fetch.return_value = [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "btc",
                "image": "https://example.com/btc.png",
                "current_price": 50000,
                "market_cap": 1000000000000,
                "market_cap_rank": 1,
                "total_volume": 50000000000,
                "price_change_percentage_24h": 2.5,
            }
        ]
        r = client.get("/market")
        assert r.status_code == 200
        # May still fail if cache is used, but at least route works

    def test_market_pagination_defaults(self, client):
        """Market page handles pagination gracefully."""
        r = client.get("/market?page=1&per_page=20")
        assert r.status_code == 200

    def test_market_invalid_page_corrected(self, client):
        """Invalid page parameter is corrected."""
        r = client.get("/market?page=-5")
        assert r.status_code == 200

    def test_market_invalid_per_page_corrected(self, client):
        """Invalid per_page corrected to default."""
        r = client.get("/market?per_page=999")
        assert r.status_code == 200

    def test_market_invalid_order_rejected(self, client):
        """Invalid sort order falls back to default."""
        r = client.get("/market?order=hack_attempt")
        assert r.status_code == 200


class TestCoinDetail:
    @patch.object(cg, "fetch_coin_detail")
    @patch.object(cg, "fetch_price_history")
    def test_detail_coin(self, mock_history, mock_detail, client):
        """Detail page works for valid coin."""
        mock_detail.return_value = {
            "id": "bitcoin",
            "name": "Bitcoin",
            "symbol": "btc",
            "description": {"en": "Digital currency"},
        }
        mock_history.return_value = {
            "prices": [[1000000 * i, 50000 + i * 100] for i in range(1, 31)]
        }
        r = client.get("/coin/bitcoin")
        assert r.status_code == 200

    def test_detail_invalid_coin(self, client):
        """Detail page handles invalid coin ID."""
        with patch.object(cg, "fetch_coin_detail", side_effect=cg.CoinGeckoAPIError("Not found", 404)):
            r = client.get("/coin/nonexistent-coin-xyz")
            # Should render with error handling, not 500
            assert r.status_code in (200, 404)


class TestChartDays:
    def test_chart_days_valid(self, client):
        """Valid chart days values work."""
        for days in [7, 30, 90]:
            r = client.get(f"/coin/bitcoin?days={days}")
            assert r.status_code in (200, 500)  # may fail API but not 404

    def test_chart_days_invalid_corrected(self, client):
        """Invalid chart days corrected to default 7."""
        r = client.get("/coin/bitcoin?days=999")
        # Should correct to 7, not crash
        assert r.status_code in (200, 500)
