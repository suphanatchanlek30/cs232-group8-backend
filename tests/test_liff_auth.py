"""Tests for LIFF Auth endpoints."""


class TestLiffExchange:
    def test_exchange_mock_token(self, client):
        r = client.post("/api/v1/liff/auth/exchange", json={
            "idToken": "mock-line-token-testuser001",
            "displayName": "Test User 001",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]
        assert body["data"]["user"]["role"] == "REPORTER"

    def test_exchange_invalid_token(self, client):
        r = client.post("/api/v1/liff/auth/exchange", json={
            "idToken": "bad-token",
        })
        assert r.status_code == 401

    def test_exchange_empty_token(self, client):
        r = client.post("/api/v1/liff/auth/exchange", json={
            "idToken": "mock-line-token-",
        })
        assert r.status_code == 400


class TestLiffRefreshAndLogout:
    def _get_tokens(self, client):
        r = client.post("/api/v1/liff/auth/exchange", json={
            "idToken": "mock-line-token-flowuser",
            "displayName": "Flow User",
        })
        data = r.json()["data"]
        return data["accessToken"], data["refreshToken"]

    def test_refresh_token(self, client):
        access, refresh = self._get_tokens(client)
        r = client.post("/api/v1/liff/auth/refresh", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 200
        assert "accessToken" in r.json()["data"]

    def test_me_endpoint(self, client):
        access, _ = self._get_tokens(client)
        r = client.get("/api/v1/liff/auth/me", headers={
            "Authorization": f"Bearer {access}",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["role"] == "REPORTER"
        assert "fullName" in data

    def test_logout_then_refresh_fails(self, client):
        _, refresh = self._get_tokens(client)
        # logout
        r = client.post("/api/v1/liff/auth/logout", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 200
        # try refresh after logout
        r = client.post("/api/v1/liff/auth/refresh", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 403


class TestLiffMeUnauth:
    def test_me_without_token(self, client):
        r = client.get("/api/v1/liff/auth/me")
        assert r.status_code == 403  # HTTPBearer auto_error
