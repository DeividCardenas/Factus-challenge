"""Schemas compartidos"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Parámetros de paginación"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
