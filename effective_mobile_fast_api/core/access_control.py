from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from effective_mobile_fast_api.core.models.tables import User, Role, Permission, UserRole, RolePermission


class AccessControlService:
    """Сервис для управления правами доступа (Access Control System)"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Получить все разрешения пользователя через его роли"""
        query = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, RolePermission.role_id == Role.id)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """Получить все роли пользователя"""
        query = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def has_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Проверить, есть ли у пользователя разрешение на выполнение действия с ресурсом"""
        query = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, RolePermission.role_id == Role.id)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Permission.resource == resource,
                    Permission.action == action
                )
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def has_role(self, user_id: str, role_name: str) -> bool:
        """Проверить, есть ли у пользователя определенная роль"""
        query = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Role.name == role_name
                )
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def is_admin(self, user_id: str) -> bool:
        """Проверить, является ли пользователь администратором"""
        return await self.has_role(user_id, "admin")


def check_permission(resource: str, action: str):
    """Декоратор для проверки прав доступа к endpoint"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Получаем session и user_id из зависимостей
            session = None
            user_id = None
            
            # Ищем session и user_id в аргументах
            for arg in args:
                if hasattr(arg, 'execute'):  # Это AsyncSession
                    session = arg
                elif isinstance(arg, int):  # Это может быть user_id
                    user_id = arg
            
            # Ищем в kwargs
            if not session:
                session = kwargs.get('session')
            if not user_id:
                user_id = kwargs.get('user_id') or kwargs.get('current_user_id')
            
            if not session or not user_id:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Проверяем права доступа
            access_control = AccessControlService(session)
            has_access = await access_control.has_permission(user_id, resource, action)
            
            if not has_access:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {action} on {resource}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

