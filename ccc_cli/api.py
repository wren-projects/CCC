"""Client for codingcontest.org and its game servers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests

from .config import Config

PLATFORM_URL = "https://codingcontest.org"
DEFAULT_TIMEOUT = 60.0


class ApiError(Exception):
    """Raised when a platform or game request fails."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def _error_detail(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return f": {text[:300]}" if text else ""

    if isinstance(data, dict):
        for key in ("error", "message"):
            if data.get(key):
                return f": {data[key]}"
        if data.get("maxSizeMb") is not None:
            return f": file too large (max {data['maxSizeMb']} MB)"
        if data.get("cooldownSec") is not None:
            return f": retry after {data['cooldownSec']}s"
    return f": {data!r}"[:300]


class Api:
    """Platform API: authentication, contest lookup, and game tokens."""

    def __init__(self, config: Config, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.config = config
        self.timeout = timeout
        self.session = requests.Session()
        self.session.cookies.update(config.cookies)
        self.session.headers.update(
            {
                "User-Agent": "ccc-cli/0.1",
                "Accept": "application/json",
            }
        )
        if config.xsrf_token:
            self.session.headers["X-XSRF-TOKEN"] = config.xsrf_token

    def _request(
        self, method: str, path_or_url: str, **kwargs: Any
    ) -> requests.Response:
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else f"{PLATFORM_URL}{path_or_url}"
        )

        # Prefer the current XSRF cookie; the platform can rotate it.
        xsrf = self.session.cookies.get("XSRF-TOKEN")
        if xsrf:
            self.session.headers["X-XSRF-TOKEN"] = xsrf

        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            detail = _error_detail(error.response) if error.response is not None else ""
            raise ApiError(
                f"{method} {url} failed ({status}){detail}",
                status=status,
            ) from error
        except requests.RequestException as error:
            raise ApiError(f"{method} {url} failed: {error}") from error

    def _json(self, method: str, path_or_url: str, **kwargs: Any) -> Any:
        response = self._request(method, path_or_url, **kwargs)
        try:
            return response.json()
        except ValueError as error:
            raise ApiError(
                f"Expected JSON from {response.url}, got:\n{response.text[:500]}"
            ) from error

    def current_user(self) -> str:
        data = self._json("GET", "/api/auth/current-user")
        username = data.get("username") if isinstance(data, dict) else None
        if not username:
            raise ApiError("The session is not valid; run `ccc setup` again.")
        return str(username)

    def resolve_contest(self, value: str) -> dict[str, Any]:
        """Resolve a contest name or training game slug."""

        value = value.strip()
        if not value:
            raise ApiError("No contest configured. Run `ccc setup` first.")

        try:
            data = self._json("GET", f"/api/contests/{value}")
        except ApiError as error:
            if error.status not in (400, 404):
                raise
            data = None

        if isinstance(data, dict) and data.get("gameBaseUrl"):
            return data

        # Fall back to a training game slug.
        try:
            game = self._json("GET", f"/api/training/{value}")
        except ApiError as error:
            if error.status == 404:
                raise ApiError(
                    f"Contest or game {value!r} was not found. Use the training "
                    "contest name from "
                    "https://codingcontest.org/contests/<name>/game."
                ) from error
            raise
        if not isinstance(game, dict):
            raise ApiError(f"Contest or game {value!r} was not found.")

        started = self._json(
            "POST",
            f"/api/training/{value}/start",
            params={"mode": "exploration"},
        )
        contest_name = started.get("contestName") if isinstance(started, dict) else None
        if not contest_name:
            raise ApiError(f"Could not start a training session for {value!r}.")

        contest = self._json("GET", f"/api/contests/{contest_name}")
        if not isinstance(contest, dict) or not contest.get("gameBaseUrl"):
            raise ApiError(f"Could not load contest {contest_name!r}.")
        return contest

    def game_token(self, contest_slug: str) -> str:
        data = self._json(
            "POST",
            "/api/game-token",
            json={"contestSlug": contest_slug},
        )
        token = data.get("token") if isinstance(data, dict) else None
        if not token:
            raise ApiError("Could not obtain a game token.")
        return str(token)

    def game(self, contest: dict[str, Any]) -> GameApi:
        base_url = str(contest.get("gameBaseUrl") or "").rstrip("/")
        slug = str(contest.get("slug") or "")
        if not base_url or not slug:
            raise ApiError("The contest does not have a game server.")
        return GameApi(base_url, self.game_token(slug), slug, timeout=self.timeout)


class GameApi:
    """Per-contest game server: level files and solution submissions."""

    def __init__(
        self,
        base_url: str,
        token: str,
        contest_slug: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": token,
                "X-CCC-SLUG": contest_slug,
                "Referer": self.base_url + "/",
                "Accept": "*/*",
                "User-Agent": "ccc-cli/0.1",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            detail = _error_detail(error.response) if error.response is not None else ""
            raise ApiError(
                f"{method} {url} failed ({status}){detail}",
                status=status,
            ) from error
        except requests.RequestException as error:
            raise ApiError(f"{method} {url} failed: {error}") from error

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as error:
            raise ApiError(
                f"Expected JSON from {response.url}, got:\n{response.text[:500]}"
            ) from error

    def contestant_info(self) -> dict[str, Any]:
        data = self._json("GET", "/api/contestant/contestant-info")
        if not isinstance(data, dict):
            raise ApiError("Unexpected contestant info response.")
        return data

    def current_level(self) -> int:
        info = self.contestant_info()
        try:
            return int(info["score"]["gameScore"]["level"])
        except (KeyError, TypeError, ValueError):
            return 1

    def level_files_url(self, level: int) -> str:
        data = self._json("GET", f"/api/contestant/level/{level}/files")
        url = data.get("url") if isinstance(data, dict) else None
        if not url:
            raise ApiError(f"Could not find the files for level {level}.")
        return urljoin(self.base_url + "/", str(url))

    def download_level_zip(self, level: int) -> bytes:
        url = self.level_files_url(level)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as error:
            raise ApiError(f"Could not download level {level}: {error}") from error

    def submit_solution(
        self,
        level: int,
        file_id: str,
        content: bytes,
        filename: str,
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/contestant/submit-{level}-{file_id}",
            files={"solution": (filename, content, "application/octet-stream")},
        )
        try:
            data = response.json()
        except ValueError as error:
            raise ApiError(
                f"Unexpected submission response:\n{response.text[:500]}"
            ) from error
        if not isinstance(data, dict):
            raise ApiError(f"Unexpected submission response: {data!r}")
        return data
