from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_jwt_secret: str

    # OpenAI
    openai_api_key: str

    # FCM
    fcm_project_id: str = ""
    fcm_private_key: str = ""
    fcm_client_email: str = ""

    # App
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()