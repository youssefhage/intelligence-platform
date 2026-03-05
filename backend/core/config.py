from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://fmcg:fmcg_secret@localhost:5432/fmcg_intelligence"
    database_url_sync: str = "postgresql://fmcg:fmcg_secret@localhost:5432/fmcg_intelligence"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API Keys
    anthropic_api_key: str = ""
    world_bank_api_url: str = "https://api.worldbank.org/v2"
    fao_api_url: str = "https://www.fao.org/faostat/api/v1"

    # ERP Integration
    erp_base_url: str = "http://localhost:8080/api"
    erp_api_key: str = ""
    erp_sync_interval_minutes: int = 15

    # POS Integration
    pos_base_url: str = "http://localhost:9090/api"
    pos_api_key: str = ""
    pos_sync_interval_minutes: int = 5

    # Application
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Lebanon-specific
    default_currency: str = "USD"
    secondary_currency: str = "LBP"
    lbp_exchange_rate: float = 89500.0

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
