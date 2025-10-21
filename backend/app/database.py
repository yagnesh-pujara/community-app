from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

def get_supabase(service: bool = False) -> Client:
    key = (
        settings.supabase_jwt_secret
        if service
        else settings.supabase_key
    )
    return create_client(settings.supabase_url, key)