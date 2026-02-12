from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# CONEXIÓN POSTGRESQL (asyncpg)
# Formato: postgresql+asyncpg://usuario:password@host:puerto/base_de_datos
DATABASE_URL = "postgresql+asyncpg://factus_user:factus_password@localhost:5432/factus_db"

# Motor Asíncrono de Alto Rendimiento
engine = create_async_engine(
    DATABASE_URL,
    echo=False, # Pon True si quieres ver cada consulta SQL en la terminal
    future=True,
    # Configuración del Pool de Conexiones (Vital para concurrencia masiva)
    pool_size=20,     # Mantiene 20 conexiones abiertas listas para usar
    max_overflow=10   # Puede crear 10 más si hay mucha carga
)

async def init_db():
    async with engine.begin() as conn:
        # Crea las tablas automáticamente al iniciar
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session