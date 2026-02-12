from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# 1. Crear el motor asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG, # Log queries en debug
    future=True
)

# 2. Inicializar tablas
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Solo para dev agresivo
        await conn.run_sync(SQLModel.metadata.create_all)

# 3. Dependencia para obtener sesión
async def get_session():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
