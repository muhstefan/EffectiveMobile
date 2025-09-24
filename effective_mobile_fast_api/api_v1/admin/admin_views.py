from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from effective_mobile_fast_api.api_v1.auth.dependencies import require_admin
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.entities.users import (
    RoleCreate, RoleRead, PermissionCreate, PermissionRead,
    UserRoleCreate, UserRoleRead, RolePermissionCreate, RolePermissionRead
)
from effective_mobile_fast_api.core.models.tables import (
    Role, Permission, UserRole, RolePermission, User
)

router = APIRouter(tags=["Admin Access Control"])


# Управление ролями
@router.post("/roles/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Создать новую роль"""
    # Проверяем, что роль с таким именем не существует
    query = select(Role).where(Role.name == role_data.name)
    result = await session.execute(query)
    existing_role = result.scalar_one_or_none()
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    
    role = Role(**role_data.model_dump())
    session.add(role)
    await session.commit()
    await session.refresh(role)
    
    return role


@router.get("/roles/", response_model=List[RoleRead])
async def get_roles(
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Получить все роли"""
    query = select(Role)
    result = await session.execute(query)
    roles = result.scalars().all()
    
    return list(roles)


@router.get("/roles/{role_id}/", response_model=RoleRead)
async def get_role(
    role_id: int,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Получить роль по ID"""
    role = await session.get(Role, role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return role


# Управление разрешениями
@router.post("/permissions/", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Создать новое разрешение"""
    # Проверяем, что разрешение с таким именем не существует
    query = select(Permission).where(Permission.name == permission_data.name)
    result = await session.execute(query)
    existing_permission = result.scalar_one_or_none()
    
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    
    permission = Permission(**permission_data.model_dump())
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    
    return permission


@router.get("/permissions/", response_model=List[PermissionRead])
async def get_permissions(
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Получить все разрешения"""
    query = select(Permission)
    result = await session.execute(query)
    permissions = result.scalars().all()
    
    return list(permissions)


# Управление ролями пользователей
@router.post("/user-roles/", response_model=UserRoleRead, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_role_data: UserRoleCreate,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Назначить роль пользователю"""
    # Проверяем, что пользователь существует
    user = await session.get(User, user_role_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Проверяем, что роль существует
    role = await session.get(Role, user_role_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Проверяем, что у пользователя еще нет этой роли
    query = select(UserRole).where(
        UserRole.user_id == user_role_data.user_id,
        UserRole.role_id == user_role_data.role_id
    )
    result = await session.execute(query)
    existing_user_role = result.scalar_one_or_none()
    
    if existing_user_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role"
        )
    
    user_role = UserRole(**user_role_data.model_dump())
    session.add(user_role)
    await session.commit()
    await session.refresh(user_role)
    
    # Загружаем связанную роль для ответа
    await session.refresh(user_role, ['role'])
    
    return user_role


@router.delete("/user-roles/{user_role_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_role_id: int,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Удалить роль у пользователя"""
    user_role = await session.get(UserRole, user_role_id)
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found"
        )
    
    await session.delete(user_role)
    await session.commit()


# Управление разрешениями ролей
@router.post("/role-permissions/", response_model=RolePermissionRead, status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_permission_data: RolePermissionCreate,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Назначить разрешение роли"""
    # Проверяем, что роль существует
    role = await session.get(Role, role_permission_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Проверяем, что разрешение существует
    permission = await session.get(Permission, role_permission_data.permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Проверяем, что у роли еще нет этого разрешения
    query = select(RolePermission).where(
        RolePermission.role_id == role_permission_data.role_id,
        RolePermission.permission_id == role_permission_data.permission_id
    )
    result = await session.execute(query)
    existing_role_permission = result.scalar_one_or_none()
    
    if existing_role_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already has this permission"
        )
    
    role_permission = RolePermission(**role_permission_data.model_dump())
    session.add(role_permission)
    await session.commit()
    await session.refresh(role_permission)
    
    # Загружаем связанное разрешение для ответа
    await session.refresh(role_permission, ['permission'])
    
    return role_permission


@router.delete("/role-permissions/{role_permission_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_permission_id: int,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Удалить разрешение у роли"""
    role_permission = await session.get(RolePermission, role_permission_id)
    
    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role permission not found"
        )
    
    await session.delete(role_permission)
    await session.commit()


# Получение информации о пользователях и их ролях
@router.get("/users/", response_model=List[dict])
async def get_users_with_roles(
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Получить всех пользователей с их ролями"""
    query = select(User).where(User.status == "active")
    result = await session.execute(query)
    users = result.scalars().all()
    
    users_with_roles = []
    for user in users:
        # Получаем роли пользователя
        user_roles_query = select(UserRole).where(UserRole.user_id == user.id)
        user_roles_result = await session.execute(user_roles_query)
        user_roles = user_roles_result.scalars().all()
        
        roles = []
        for user_role in user_roles:
            await session.refresh(user_role, ['role'])
            roles.append(user_role.role.name)
        
        users_with_roles.append({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "status": user.status,
            "roles": roles
        })
    
    return users_with_roles
