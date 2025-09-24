"""
Скрипт для инициализации тестовых данных в системе авторизации
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# from effective_mobile_fast_api.core.db import get_async_session  # Не используется
from effective_mobile_fast_api.core.models.tables import (
    User, Role, Permission, UserRole, RolePermission, Product, Order, UserStatus
)
from effective_mobile_fast_api.api_v1.auth.security import hash_password


async def create_test_data():
    """Создать тестовые данные для демонстрации системы"""
    
    # Получаем URL базы данных из переменных окружения
    db_url = os.getenv("DB_URL", "postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_system_db")
    
    # Создаем engine и session
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Проверяем, есть ли уже данные
            from sqlalchemy import select
            existing_roles = await session.execute(select(Role))
            if existing_roles.scalars().first():
                print("✅ Тестовые данные уже существуют!")
                return
            
            # Создаем роли
            admin_role = Role(
                name="admin",
                description="Администратор системы"
            )
            user_role = Role(
                name="user",
                description="Обычный пользователь"
            )
            manager_role = Role(
                name="manager",
                description="Менеджер"
            )
            
            session.add_all([admin_role, user_role, manager_role])
            await session.commit()
            await session.refresh(admin_role)
            await session.refresh(user_role)
            await session.refresh(manager_role)
            
            # Создаем разрешения
            permissions = [
                # Пользователи
                Permission(name="users_read", resource="users", action="read", description="Чтение пользователей"),
                Permission(name="users_write", resource="users", action="write", description="Создание/изменение пользователей"),
                Permission(name="users_delete", resource="users", action="delete", description="Удаление пользователей"),
                
                # Продукты
                Permission(name="products_read", resource="products", action="read", description="Чтение продуктов"),
                Permission(name="products_write", resource="products", action="write", description="Создание/изменение продуктов"),
                Permission(name="products_delete", resource="products", action="delete", description="Удаление продуктов"),
                
                # Заказы
                Permission(name="orders_read", resource="orders", action="read", description="Чтение заказов"),
                Permission(name="orders_write", resource="orders", action="write", description="Создание/изменение заказов"),
                Permission(name="orders_delete", resource="orders", action="delete", description="Удаление заказов"),
                
                # Админ
                Permission(name="admin_access", resource="admin", action="access", description="Доступ к админ панели"),
            ]
            
            session.add_all(permissions)
            await session.commit()
            
            # Назначаем разрешения ролям
            role_permissions = [
                # Админ - все права
                RolePermission(role_id=admin_role.id, permission_id=permissions[0].id),  # users_read
                RolePermission(role_id=admin_role.id, permission_id=permissions[1].id),  # users_write
                RolePermission(role_id=admin_role.id, permission_id=permissions[2].id),  # users_delete
                RolePermission(role_id=admin_role.id, permission_id=permissions[3].id),  # products_read
                RolePermission(role_id=admin_role.id, permission_id=permissions[4].id),  # products_write
                RolePermission(role_id=admin_role.id, permission_id=permissions[5].id),  # products_delete
                RolePermission(role_id=admin_role.id, permission_id=permissions[6].id),  # orders_read
                RolePermission(role_id=admin_role.id, permission_id=permissions[7].id),  # orders_write
                RolePermission(role_id=admin_role.id, permission_id=permissions[8].id),  # orders_delete
                RolePermission(role_id=admin_role.id, permission_id=permissions[9].id),  # admin_access
                
                # Менеджер - управление продуктами и заказами
                RolePermission(role_id=manager_role.id, permission_id=permissions[3].id),  # products_read
                RolePermission(role_id=manager_role.id, permission_id=permissions[4].id),  # products_write
                RolePermission(role_id=manager_role.id, permission_id=permissions[5].id),  # products_delete
                RolePermission(role_id=manager_role.id, permission_id=permissions[6].id),  # orders_read
                RolePermission(role_id=manager_role.id, permission_id=permissions[7].id),  # orders_write
                RolePermission(role_id=manager_role.id, permission_id=permissions[8].id),  # orders_delete
                
                # Пользователь - чтение продуктов и создание заказов
                RolePermission(role_id=user_role.id, permission_id=permissions[3].id),  # products_read
                RolePermission(role_id=user_role.id, permission_id=permissions[6].id),  # orders_read
                RolePermission(role_id=user_role.id, permission_id=permissions[7].id),  # orders_write
            ]
            
            session.add_all(role_permissions)
            await session.commit()
            
            # Создаем тестовых пользователей
            users = [
                User(
                    first_name="Админ",
                    last_name="Админов",
                    middle_name="Админович",
                    email="admin@example.com",
                    password_hash=hash_password("admin1234"),
                    status=UserStatus.active
                ),
                User(
                    first_name="Менеджер",
                    last_name="Менеджеров",
                    middle_name="Менеджерович",
                    email="manager@example.com",
                    password_hash=hash_password("manager1234"),
                    status=UserStatus.active
                ),
                User(
                    first_name="Пользователь",
                    last_name="Пользователев",
                    middle_name="Пользователевич",
                    email="user@example.com",
                    password_hash=hash_password("user1234"),
                    status=UserStatus.active
                ),
                User(
                    first_name="Удаленный",
                    last_name="Пользователь",
                    email="deleted@example.com",
                    password_hash=hash_password("deleted123"),
                    status=UserStatus.deleted
                )
            ]
            
            session.add_all(users)
            await session.commit()
            
            # Назначаем роли пользователям
            user_roles = [
                UserRole(user_id=users[0].id, role_id=admin_role.id),      # Админ
                UserRole(user_id=users[1].id, role_id=manager_role.id),    # Менеджер
                UserRole(user_id=users[2].id, role_id=user_role.id),       # Пользователь
                UserRole(user_id=users[3].id, role_id=user_role.id),       # Удаленный пользователь
            ]
            
            session.add_all(user_roles)
            await session.commit()
            
            # Создаем тестовые продукты
            products = [
                Product(
                    name="Ноутбук Dell XPS 13",
                    description="Высокопроизводительный ноутбук для работы и развлечений",
                    price=120000.0,
                    category="Электроника"
                ),
                Product(
                    name="iPhone 15 Pro",
                    description="Новейший смартфон от Apple",
                    price=150000.0,
                    category="Электроника"
                ),
                Product(
                    name="Книга 'Python для начинающих'",
                    description="Учебник по программированию на Python",
                    price=2500.0,
                    category="Книги"
                ),
                Product(
                    name="Тестовый продукт",
                    description="Демонстрационный продукт",
                    price=1000.0,
                    category="Тест"
                )
            ]
            
            session.add_all(products)
            await session.commit()
            
            # Создаем тестовые заказы
            orders = [
                Order(
                    user_id=users[2].id,  # Пользователь
                    product_id=products[0].id,
                    quantity=1,
                    total_amount=120000.0,
                    status="completed"
                ),
                Order(
                    user_id=users[2].id,  # Пользователь
                    product_id=products[2].id,
                    quantity=2,
                    total_amount=5000.0,
                    status="pending"
                ),
                Order(
                    user_id=users[1].id,  # Менеджер
                    product_id=products[1].id,
                    quantity=1,
                    total_amount=150000.0,
                    status="processing"
                )
            ]
            
            session.add_all(orders)
            await session.commit()
            
            print("✅ Тестовые данные успешно созданы!")
            print("\n📋 Созданные пользователи:")
            print("👑 Админ: admin@example.com / admin123")
            print("👨‍💼 Менеджер: manager@example.com / manager123")
            print("👤 Пользователь: user@example.com / user123")
            print("🗑️ Удаленный: deleted@example.com / deleted123")
            
            print("\n🔐 Роли и разрешения:")
            print("• admin - все права")
            print("• manager - управление продуктами и заказами")
            print("• user - только чтение продуктов")
            
            print("\n📦 Созданы тестовые продукты и заказы")
            
        except Exception as e:
            print(f"❌ Ошибка при создании тестовых данных: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_data())
