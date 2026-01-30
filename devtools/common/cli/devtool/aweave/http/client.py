"""Base HTTP client with error handling."""

import json
from typing import Any

import httpx


class HTTPClientError(Exception):
    """HTTP client error with actionable details."""

    def __init__(self, code: str, message: str, suggestion: str | None = None):
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class HTTPClient:
    """Base HTTP client with retry, timeout, and error handling."""

    def __init__(
        self,
        base_url: str,
        auth: tuple[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._auth = auth
        self._headers = headers or {}
        self._timeout = timeout

    def _build_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base_url,
            auth=self._auth,
            headers=self._headers,
            timeout=self._timeout,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        GET request, returns raw JSON response.

        Raises HTTPClientError on failure.
        """
        with self._build_client() as client:
            response = client.get(path, params=params)
            return self._handle_response(response)

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.post(path, json=json)
            return self._handle_response(response)

    def put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """PUT request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.put(path, json=json)
            return self._handle_response(response)

    def delete(self, path: str) -> dict[str, Any]:
        """DELETE request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.delete(path)
            return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response, raise on error."""
        if response.status_code == 401:
            raise HTTPClientError(
                code="AUTH_FAILED",
                message="Authentication failed",
                suggestion="Check your credentials (username/password or token)",
            )

        if response.status_code == 403:
            raise HTTPClientError(
                code="FORBIDDEN",
                message="Access denied",
                suggestion="Check if you have the required permissions",
            )

        if response.status_code == 404:
            raise HTTPClientError(
                code="NOT_FOUND",
                message="Resource not found",
                suggestion="Verify the resource ID/path is correct",
            )

        if response.status_code >= 400:
            raise HTTPClientError(
                code=f"HTTP_{response.status_code}",
                message=f"Request failed: {response.text}",
            )

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPClientError(
                code="BAD_JSON",
                message=f"Invalid JSON response: {e}",
                suggestion="Check if endpoint returns JSON or verify Accept header",
            ) from e
