from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from effective_mobile_fast_api.core.models.tables import User, Role, UserRole
from effective_mobile_fast_api.core.entities.users import UserCreate, UserCreateDB
from effective_mobile_fast_api.api_v1.auth.security import hash_password


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Получить пользователя по email"""
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    """Получить пользователя по ID"""
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_user_db(session: AsyncSession, user_data: UserCreate) -> User:
    """Создать нового пользователя в БД"""
    # Хешируем пароль
    password_hash = hash_password(user_data.password)
    
    # Создаем объект пользователя
    user_create_db = UserCreateDB(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        email=user_data.email,
        password_hash=password_hash
    )
    
    # Создаем пользователя в БД
    user = User(**user_create_db.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Назначаем роль "user" новому пользователю
    role_query = select(Role).where(Role.name == "user")
    role_result = await session.execute(role_query)
    user_role = role_result.scalar_one_or_none()
    
    if user_role:
        user_role_assignment = UserRole(
            user_id=user.id,
            role_id=user_role.id
        )
        session.add(user_role_assignment)
        await session.commit()
    
    return user
