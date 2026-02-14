"""Repositories - Data access layer with optimizations"""

from app.repositories.base import BaseRepository
from app.repositories.factura_repository import FacturaRepository
from app.repositories.user_repository import UserRepository
from app.repositories.lote_repository import LoteRepository

__all__ = [
    "BaseRepository",
    "FacturaRepository",
    "UserRepository",
    "LoteRepository",
]
