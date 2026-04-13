from pathlib import Path
from typing import Any, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VR Score API"
    app_env: str = "dev"
    database_url: str = "sqlite:///./data/app.db"
    cors_origins: str = "http://localhost:4321,http://127.0.0.1:4321"
    fibra_lookup_url: str = "https://www.fibratelecom.ec/contrato/busqueda_contracto/?cedula="
    fibra_lookup_timeout_seconds: float = 6.0
    turso_auth_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("libsql://"):
            raw = self.database_url.replace("libsql://", "sqlite+libsql://", 1)
            parsed = urlsplit(raw)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            # Turso remoto requiere secure=true para evitar redirecciones 308.
            query.setdefault("secure", "true")
            if self.turso_auth_token:
                query.setdefault("authToken", self.turso_auth_token)
            return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
        return self.database_url

    @property
    def database_connect_args(self) -> dict[str, Any]:
        if self.database_url.startswith("libsql://"):
            return {}

        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}

        return {}

    @property
    def is_local_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite:///./")

    @property
    def sqlite_file_path(self) -> Path | None:
        if not self.is_local_sqlite:
            return None
        return Path(self.database_url.replace("sqlite:///", "", 1))


settings = Settings()
