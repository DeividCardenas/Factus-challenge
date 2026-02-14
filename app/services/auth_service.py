"""Auth Service - Lógica de autenticación"""

from datetime import datetime, timedelta
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.models import User
from app.repositories.user_repository import UserRepository
from app.core.config import settings
from app.api.errors.http_errors import UnauthorizedException, NotFoundException


# Setup password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Servicio de autenticación y autorización.
    
    Usada por:
    - Login endpoint (POST /login)
    - Token validation (GET_CURRENT_USER dependency)
    - GraphQL resolvers
    """
    
    def __init__(self, session: AsyncSession):
        """Inicializar con UserRepository"""
        self.repo = UserRepository(session)
    
    # ============= PASSWORD =============
    
    def hash_password(self, password: str) -> str:
        """
        Hashear password con bcrypt.
        
        Args:
            password: Password en texto plano
            
        Returns:
            Password hasheado
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verificar password contra hash.
        
        Args:
            plain_password: Password en texto plano
            hashed_password: Password hasheado
            
        Returns:
            True si coinciden, False si no
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    # ============= TOKENS =============
    
    def create_access_token(
        self,
        user_id: int,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crear JWT token de acceso.
        
        Args:
            user_id: ID del usuario
            email: Email del usuario
            expires_delta: Tiempo de expiración (default: 24 horas)
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": datetime.utcnow() + expires_delta
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """
        Verificar y decodificar JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Payload del token
            
        Raises:
            UnauthorizedException: Si token es inválido o expirado
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            return payload
        except JWTError as e:
            raise UnauthorizedException(f"Invalid token: {str(e)}")
    
    # ============= USER OPERATIONS =============
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtener usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            User object o None
        """
        return await self.repo.get_by_email(email)
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> User:
        """
        Autenticar usuario (email + password).
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            
        Returns:
            User object si autenticación exitosa
            
        Raises:
            UnauthorizedException: Si email/password inválidos
        """
        user = await self.get_user_by_email(email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        if not self.verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        return user
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str = ""
    ) -> User:
        """
        Crear nuevo usuario.
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            full_name: Nombre del usuario
            
        Returns:
            User object creado
            
        Raises:
            ConflictException: Si email ya existe
        """
        # Verificar que no exista
        existing = await self.repo.get_by_email(email)
        if existing:
            from app.api.errors.http_errors import ConflictException
            raise ConflictException(f"User with email '{email}' already exists")
        
        # Crear usuario
        user = User(
            email=email,
            password_hash=self.hash_password(password),
            full_name=full_name,
            is_active=True
        )
        
        return await self.repo.create(user)
    
    # ============= AUTHORIZATION =============
    
    def is_user_owner(self, resource_user_id: int, current_user_id: int) -> bool:
        """
        Verificar si el usuario actual es dueño del recurso.
        
        Args:
            resource_user_id: ID del usuario del recurso
            current_user_id: ID del usuario actual
            
        Returns:
            True si es dueño, False si no
        """
        return resource_user_id == current_user_id
