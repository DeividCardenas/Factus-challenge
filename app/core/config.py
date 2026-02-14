import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

# 1. RASTREO DEL ARCHIVO .ENV
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# 2. CARGA EXPLÍCITA
print(f"📂 Buscando .env en: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseSettings):
    """
    Configuración Profesional con Pydantic Settings
    Soporta dev, staging y producción
    """
    
    # ========== MODO DE APLICACIÓN ==========
    APP_MODE: str = os.getenv("APP_MODE", "development")  # development, staging, production
    APP_NAME: str = "Factus Challenge API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # ========== SERVIDOR ==========
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # ========== BASE DE DATOS ==========
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://factus_user:factus_password@localhost:5432/factus_db"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # ========== SEGURIDAD ==========
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS384")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # ========== API EXTERNA - FACTUS ==========
    FACTUS_URL: str = os.getenv("FACTUS_URL", "http://localhost:5000")
    FACTUS_TOKEN: str = os.getenv("FACTUS_TOKEN", "mock-token-local")
    FACTUS_TIMEOUT: int = int(os.getenv("FACTUS_TIMEOUT", "30"))
    FACTUS_MOCK_MODE: bool = os.getenv("FACTUS_MOCK_MODE", "True").lower() == "true"
    
    # ========== REDIS / CACHÉ ==========
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    
    # ========== CORS ==========
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]
    
    # ========== LOGGING ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json" if APP_MODE == "production" else "text")
    
    # ========== RATE LIMITING ==========
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtener settings con caché singleton"""
    return Settings()


# Instancia global
settings = get_settings()

# 3. REPORTE EN LA TERMINAL
print("---------------------------------------------------")
print("🚀 CONFIGURACIÓN CARGADA")
print(f"   ▶ Ambiente: {settings.APP_MODE}")
print(f"   ▶ Debug: {settings.DEBUG}")
print(f"   ▶ Servidor: http://{settings.HOST}:{settings.PORT}")
print(f"   ▶ GraphQL: http://{settings.HOST}:{settings.PORT}/graphql")
print(f"   ▶ Docs: http://{settings.HOST}:{settings.PORT}/docs")
print("---------------------------------------------------")
