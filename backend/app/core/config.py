from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RUNWAY_API_KEY: str = ""
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""
    KLING_API_BASE: str = "https://api.klingai.com"
    GROQ_API_KEY: str = ""
    GROQ_MODEL_PRIMARY: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_FALLBACK: str = "llama-3.1-8b-instant"
    OLLAMA_URL: str = ""          # Ex: http://ton-ip:11434 — active le GPU local
    OLLAMA_MODEL: str = "qwen2.5:14b"  # Modèle Ollama à utiliser
    PEXELS_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""
    APP_URL: str = "https://sunny-surprise-production-fec2.up.railway.app"
    OUTPUTS_DIR: str = "outputs/videos"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    DEBUG: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
