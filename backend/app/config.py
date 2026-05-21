from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    fred_api_key: str = ""
    database_url: str = "sqlite:///./advisor.db"
    ml_enabled: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    price_cache_ttl_minutes: int = 60
    rebalance_drift_threshold: float = 5.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
