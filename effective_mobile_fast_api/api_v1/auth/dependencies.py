from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from effective_mobile_fast_api.api_v1.auth.crud import get_user_by_id
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.entities.users import UserPublic
from effective_mobile_fast_api.core.access_control import AccessControlService


async def get_user_soft(
        request: Request,
        session: AsyncSession = Depends(get_db)
):
    """Получить пользователя, если он авторизован (может вернуть None)"""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        return None  # Гость или неавторизованный пользователь

    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    
    user_public = UserPublic.model_validate(user)
    return user_public


async def get_user_id(user=Depends(get_user_soft)) -> str | None:
    """Получить ID пользователя"""
    if user:
        return user.id
    return None


async def get_user_strict(
        user: UserPublic = Depends(get_user_soft)
):
    """Получить пользователя, обязательно авторизованного"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
        current_user: UserPublic = Depends(get_user_strict),
        session: AsyncSession = Depends(get_db)
):
    """Проверить, что пользователь является администратором"""
    access_control = AccessControlService(session)
    is_admin = await access_control.is_admin(current_user.id)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_permission(resource: str, action: str):
    """Фабрика для создания зависимости проверки разрешений"""
    async def _require_permission(
            current_user: UserPublic = Depends(get_user_strict),
            session: AsyncSession = Depends(get_db)
    ):
        """Проверить, что у пользователя есть определенное разрешение"""
        access_control = AccessControlService(session)
        has_permission = await access_control.has_permission(current_user.id, resource, action)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {action} on {resource}"
            )
        return current_user
    
    return _require_permission
