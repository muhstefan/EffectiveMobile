from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from effective_mobile_fast_api.api_v1.auth.dependencies import get_user_strict, require_permission
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.entities.users import UserUpdate, UserRead, UserPublic
from effective_mobile_fast_api.core.models.tables import User, UserStatus
from effective_mobile_fast_api.api_v1.auth.security import hash_password

router = APIRouter(tags=["Users"])


@router.get("/me/", response_model=UserRead)
async def get_current_user(
        current_user: UserPublic = Depends(get_user_strict),
        session: AsyncSession = Depends(get_db)
):
    """Получить информацию о текущем пользователе"""
    user = await session.get(User, current_user.id)
    return UserRead.model_validate(user)


@router.put("/me/", response_model=UserRead)
async def update_current_user(
        user_update: UserUpdate,
        current_user: UserPublic = Depends(get_user_strict),
        session: AsyncSession = Depends(get_db)
):
    """Обновить информацию о текущем пользователе"""
    user = await session.get(User, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Обновляем поля, если они переданы
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await session.commit()
    await session.refresh(user)
    
    return UserRead.model_validate(user)


@router.delete("/me/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
        current_user: UserPublic = Depends(get_user_strict),
        session: AsyncSession = Depends(get_db)
):
    """Мягкое удаление аккаунта пользователя"""
    user = await session.get(User, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Мягкое удаление - меняем статус на deleted
    user.status = UserStatus.deleted
    await session.commit()
    
    return {"message": "Account deleted successfully"}


@router.get("/{user_id}/", response_model=UserPublic)
async def get_user(
        user_id: int,
        current_user: UserPublic = Depends(require_permission("users", "read")),
        session: AsyncSession = Depends(get_db)
):
    """Получить информацию о пользователе (требует права на чтение пользователей)"""
    user = await session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserPublic.model_validate(user)
