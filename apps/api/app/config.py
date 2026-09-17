from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./deepfold.db"
    redis_url: str = "redis://localhost:6379/0"
    approve_and_publish_enabled: bool = False
    kill_switch: bool = False
    wp_live: bool = False
    wp_username: str = ""
    wp_application_password: str = ""
    default_actor: str = "journalist@newsworld.local"
    publisher_name: str = "Newsworld"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Instant seed fulfill on Go is OFF by default so jobs stay queued for Grok Bot.
    demo_instant_fulfill: bool = False
    # Localhost-only loop that claims/completes jobs with stub copy. Not an LLM call.
    demo_grok_worker: bool = False
    demo_grok_worker_delay_seconds: float = 3.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
