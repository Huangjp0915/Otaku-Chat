from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARACTER_DIR = DATA_DIR / "characters"
CONVERSATION_DIR = DATA_DIR / "conversations"
RUNTIME_DIR = DATA_DIR / "runtime"
UPLOAD_DIR = RUNTIME_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

for folder in [CHARACTER_DIR, CONVERSATION_DIR, RUNTIME_DIR, UPLOAD_DIR, STATIC_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    llm_mode: str = "mock"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    user_id: str = "default_user"
    desktop_window_title: str = "突破次元壁"
    proactive_cooldown_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()