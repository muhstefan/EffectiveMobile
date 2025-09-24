from fastapi import Depends, HTTPException, status, Cookie, Response, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from effective_mobile_fast_api.api_v1.auth.config import Production
from effective_mobile_fast_api.api_v1.auth.security import verify_password, generate_and_set_tokens, decode_jwt_token
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.models.tables import User, UserStatus
from effective_mobile_fast_api.core.entities.users import UserCreate, UserCreateDB, UserRead
from effective_mobile_fast_api.api_v1.auth.crud import create_user_db

router = APIRouter(tags=["Auth"])


@router.post("/register/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    """Регистрация нового пользователя"""
    try:
        # Проверяем, что пользователь с таким email не существует
        query = select(User).where(User.email == user_data.email)
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Создаем пользователя
        user_db = await create_user_db(session, user_data)
        return user_db
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Обрабатываем другие ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка регистрации: {str(e)}"
        )


@router.post("/login/")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    """Вход в систему по email и паролю"""
    # Ищем пользователя по email
    query = select(User).where(User.email == form_data.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Проверяем, что пользователь не удален
    if user.status == UserStatus.deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deleted"
        )

    generate_and_set_tokens(response, str(user.id), secure=Production)

    return {"message": "Logged in successfully", "user_id": user.id}


@router.post("/refresh/")
async def refresh_token(
        response: Response,
        refresh_token: str | None = Cookie(default=None)
):
    """Обновление токенов доступа"""
    user_id = decode_jwt_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    generate_and_set_tokens(response, str(user_id), secure=Production)

    return {"message": "Access and refresh tokens refreshed"}


@router.post("/logout/", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Выход из системы"""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=Production)
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax", secure=Production)
    return {"message": "Logged out successfully"}
