from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RUNWAY_API_KEY: str = ""
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""
    KLING_API_BASE: str = "https://api.klingai.com"
    ANTHROPIC_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    OUTPUTS_DIR: str = "outputs/videos"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    DEBUG: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
