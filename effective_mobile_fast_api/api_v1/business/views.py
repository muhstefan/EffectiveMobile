from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from effective_mobile_fast_api.api_v1.auth.dependencies import get_user_strict, require_permission
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.entities.users import ProductRead, ProductCreate, OrderRead, OrderCreate
from effective_mobile_fast_api.core.models.tables import Product, Order, User

router = APIRouter(tags=["Mock Business Objects"])


# Управление продуктами
@router.get("/products/", response_model=List[ProductRead])
async def get_products(
    current_user=Depends(require_permission("products", "read")),
    session: AsyncSession = Depends(get_db)
):
    """Получить список всех продуктов (требует права на чтение продуктов)"""
    query = select(Product)
    result = await session.execute(query)
    products = result.scalars().all()
    
    return list(products)


@router.get("/products/{product_id}/", response_model=ProductRead)
async def get_product(
    product_id: int,
    current_user=Depends(require_permission("products", "read")),
    session: AsyncSession = Depends(get_db)
):
    """Получить продукт по ID (требует права на чтение продуктов)"""
    product = await session.get(Product, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.post("/products/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user=Depends(require_permission("products", "write")),
    session: AsyncSession = Depends(get_db)
):
    """Создать новый продукт (требует права на запись продуктов)"""
    product = Product(**product_data.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    
    return product


@router.put("/products/{product_id}/", response_model=ProductRead)
async def update_product(
    product_id: int,
    product_data: ProductCreate,
    current_user=Depends(require_permission("products", "write")),
    session: AsyncSession = Depends(get_db)
):
    """Обновить продукт (требует права на запись продуктов)"""
    product = await session.get(Product, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Обновляем поля
    for field, value in product_data.model_dump().items():
        setattr(product, field, value)
    
    await session.commit()
    await session.refresh(product)
    
    return product


@router.delete("/products/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user=Depends(require_permission("products", "delete")),
    session: AsyncSession = Depends(get_db)
):
    """Удалить продукт (требует права на удаление продуктов)"""
    product = await session.get(Product, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Жесткое удаление - удаляем продукт из БД
    await session.delete(product)
    await session.commit()
    
    return {"message": "Product deleted successfully"}


# Управление заказами
@router.get("/orders/", response_model=List[OrderRead])
async def get_orders(
    current_user=Depends(require_permission("orders", "read")),
    session: AsyncSession = Depends(get_db)
):
    """Получить список всех заказов (требует права на чтение заказов)"""
    query = select(Order)
    result = await session.execute(query)
    orders = result.scalars().all()
    
    # Загружаем связанные продукты
    for order in orders:
        await session.refresh(order, ['product'])
    
    return list(orders)


@router.get("/orders/my/", response_model=List[OrderRead])
async def get_my_orders(
    current_user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Получить заказы текущего пользователя (доступно всем авторизованным пользователям)"""
    query = select(Order).where(Order.user_id == current_user.id)
    result = await session.execute(query)
    orders = result.scalars().all()
    
    # Загружаем связанные продукты
    for order in orders:
        await session.refresh(order, ['product'])
    
    return list(orders)


@router.get("/orders/{order_id}/", response_model=OrderRead)
async def get_order(
    order_id: int,
    current_user=Depends(require_permission("orders", "read")),
    session: AsyncSession = Depends(get_db)
):
    """Получить заказ по ID (требует права на чтение заказов)"""
    order = await session.get(Order, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Загружаем связанный продукт
    await session.refresh(order, ['product'])
    
    return order


@router.post("/orders/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user=Depends(require_permission("orders", "write")),
    session: AsyncSession = Depends(get_db)
):
    """Создать новый заказ (требует права на запись заказов)"""
    # Проверяем, что продукт существует
    product = await session.get(Product, order_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Проверяем, что пользователь существует
    user = await session.get(User, order_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    order = Order(**order_data.model_dump())
    session.add(order)
    await session.commit()
    await session.refresh(order)
    
    # Загружаем связанный продукт
    await session.refresh(order, ['product'])
    
    return order


@router.put("/orders/{order_id}/", response_model=OrderRead)
async def update_order(
    order_id: int,
    order_data: OrderCreate,
    current_user=Depends(require_permission("orders", "write")),
    session: AsyncSession = Depends(get_db)
):
    """Обновить заказ (требует права на запись заказов)"""
    order = await session.get(Order, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Обновляем поля
    for field, value in order_data.model_dump().items():
        setattr(order, field, value)
    
    await session.commit()
    await session.refresh(order)
    
    # Загружаем связанный продукт
    await session.refresh(order, ['product'])
    
    return order


@router.delete("/orders/{order_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    current_user=Depends(require_permission("orders", "delete")),
    session: AsyncSession = Depends(get_db)
):
    """Удалить заказ (требует права на удаление заказов)"""
    order = await session.get(Order, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    await session.delete(order)
    await session.commit()
    
    return {"message": "Order deleted successfully"}


# Публичные endpoints
@router.get("/public/")
async def public_endpoint():
    """Публичный endpoint - доступен всем"""
    return {"message": "This is a public endpoint, no authentication required"}


@router.get("/protected/")
async def protected_endpoint(
    current_user=Depends(get_user_strict)
):
    """Защищенный endpoint - требует авторизации"""
    return {
        "message": "This is a protected endpoint",
        "user": {
            "id": current_user.id,
            "name": f"{current_user.first_name} {current_user.last_name}",
            "email": current_user.email
        }
    }


@router.get("/admin-only/")
async def admin_only_endpoint(
    current_user=Depends(require_permission("admin", "access"))
):
    """Endpoint только для администраторов"""
    return {
        "message": "This is an admin-only endpoint",
        "user": {
            "id": current_user.id,
            "name": f"{current_user.first_name} {current_user.last_name}",
            "email": current_user.email
        }
    }

