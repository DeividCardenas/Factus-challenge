import os
from pathlib import Path
from dotenv import load_dotenv

# 1. RASTREO DEL ARCHIVO .ENV
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# 2. CARGA EXPLÍCITA
print(f"📂 Buscando .env en: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    """
    Configuración SIMPLIFICADA para Desarrollo Local
    """
    # Modo LOCAL (no hay cambios, siempre TEST)
    APP_MODE: str = "TEST"
    
    # URLs y tokens (vacíos por ahora, no se usan en TEST)
    FACTUS_URL: str = "http://localhost:5000"  # URL dummy para modo local
    FACTUS_TOKEN: str = "mock-token-local"     # Token dummy para modo local
    
    # Configuración de la APP
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

settings = Settings()

# 3. REPORTE EN LA TERMINAL
print("---------------------------------------------------")
print("🚀 MODO LOCAL ACTIVADO")
print(f"   ▶ Ambiente: {settings.APP_MODE}")
print(f"   ▶ Debug: {settings.DEBUG}")
print(f"   ▶ Servidor: http://{settings.HOST}:{settings.PORT}")
print("---------------------------------------------------")