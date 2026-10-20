"""CatCoder credentials, stored in one small JSON file."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_dir


class ConfigError(Exception):
    """Raised when the configuration is missing or invalid."""


CONFIG_FILE = Path(user_config_dir("ccc")) / "ccc.json"


@dataclass
class Config:
    contest_id: str
    session_cookie: str
    xsrf_token: str = ""

    @property
    def cookies(self) -> dict[str, str]:
        cookies = {"SESSION": self.session_cookie}
        if self.xsrf_token:
            cookies["XSRF-TOKEN"] = self.xsrf_token
        return cookies


def load_config(*, required: bool = False) -> Config:
    config = Config("", "")

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            config = Config(
                contest_id=str(data["contest_id"]),
                session_cookie=str(data["session_cookie"]),
                xsrf_token=str(data.get("xsrf_token", "")),
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ConfigError(f"Could not read {CONFIG_FILE}: {error}") from error

    if required and (not config.contest_id or not config.session_cookie):
        raise ConfigError(
            "No credentials found. Run `ccc setup <contest-name> <session-cookie> "
            "[xsrf-token]` first."
        )
    return config


def save_config(config: Config) -> Path:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(asdict(config), indent=2) + "\n",
        encoding="utf-8",
    )
    return CONFIG_FILE
