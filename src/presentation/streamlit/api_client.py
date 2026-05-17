import base64
import json
import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class SessionExpiredError(Exception):
    pass


class APIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class APIClient:
    def __init__(self, base_url: str, access_token: str, refresh_token: str) -> None:
        self._base_url = base_url
        self._access_token = access_token
        self._refresh_token = refresh_token

    def get(self, path: str, **params) -> dict | list:
        filtered = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", path, params=filtered).json()

    def post(self, path: str, body: dict | None = None) -> dict | None:
        resp = self._request("POST", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def patch(self, path: str, body: dict) -> dict | None:
        resp = self._request("PATCH", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def put(self, path: str, body: dict) -> dict | None:
        resp = self._request("PUT", path, json=body)
        if resp.status_code == 204:
            return None
        return resp.json()

    def delete(self, path: str) -> None:
        self._request("DELETE", path)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            new_tokens = self._try_refresh()
            if new_tokens is None:
                raise SessionExpiredError()
            self._access_token = new_tokens["access_token"]
            self._refresh_token = new_tokens["refresh_token"]
            st.session_state["tokens"] = new_tokens
            headers = {"Authorization": f"Bearer {self._access_token}"}
            with httpx.Client(timeout=10.0) as client:
                resp = client.request(method, url, headers=headers, **kwargs)
            if resp.status_code == 401:
                raise SessionExpiredError()

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, str(detail))

        return resp

    def _try_refresh(self) -> dict | None:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self._base_url}/auth/refresh",
                    json={"refresh_token": self._refresh_token},
                )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None


def decode_token_payload(token: str) -> dict:
    """Decode JWT payload (middle segment) without signature verification."""
    payload_b64 = token.split(".")[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def get_client() -> APIClient:
    tokens = st.session_state.get("tokens")
    if not tokens:
        raise SessionExpiredError()
    return APIClient(
        base_url=API_BASE_URL,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )
