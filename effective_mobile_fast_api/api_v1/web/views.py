from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from effective_mobile_fast_api.api_v1.auth.dependencies import get_user_soft, get_user_strict, require_permission
from effective_mobile_fast_api.api_v1.web.admin_views import router as admin_router
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.models.tables import Product, Order
from effective_mobile_fast_api.core.access_control import AccessControlService
from effective_mobile_fast_api.api_v1.auth.crud import get_user_by_email, create_user_db
from effective_mobile_fast_api.core.entities.users import UserCreate
from effective_mobile_fast_api.api_v1.auth.security import verify_password, generate_and_set_tokens
from effective_mobile_fast_api.api_v1.auth.config import Production

router = APIRouter(tags=["Web"])
templates = Jinja2Templates(directory="effective_mobile_fast_api/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_user_soft), session: AsyncSession = Depends(get_db)):
    """Главная страница"""
    user_roles = []
    if user:
        access_control = AccessControlService(session)
        user_roles = await access_control.get_user_roles(user.id)
    
    # Создаем словарь с информацией о пользователе для шаблона
    user_data = None
    if user:
        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "email": user.email,
            "status": user.status,
            "role": [role.name for role in user_roles]
        }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user_data
    })


@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@router.post("/auth/login")
async def login_submit(
    request: Request,
    response: RedirectResponse,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """Обработка формы входа"""
    try:
        # Ищем пользователя по email
        user = await get_user_by_email(session, username)
        
        if not user or not verify_password(password, user.password_hash):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Неверный email или пароль"
            })
        
        # Проверяем статус пользователя
        if user.status.value == "deleted":
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Аккаунт был удален"
            })
        
        # Генерируем токены
        generate_and_set_tokens(response, str(user.id), secure=Production)
        
        # Используем тот же response объект для редиректа
        response.headers["location"] = "/"
        response.status_code = 302
        return response
        
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Ошибка входа: {str(e)}"
        })


@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": error
    })


@router.post("/auth/register")
async def register_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    """Обработка формы регистрации"""
    try:
        # Проверяем совпадение паролей
        if password != password_confirm:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пароли не совпадают",
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "email": email
            })
        
        # Проверяем, что пользователь с таким email не существует
        from effective_mobile_fast_api.api_v1.auth.crud import get_user_by_email
        existing_user = await get_user_by_email(session, email)
        if existing_user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пользователь с таким email уже существует",
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "email": email
            })
        
        # Обрабатываем пустое отчество
        if middle_name and middle_name.strip() == "":
            middle_name = None
        
        # Создаем объект пользователя
        user_data = UserCreate(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            password=password,
            password_confirm=password_confirm
        )
        
        # Создаем пользователя
        user = await create_user_db(session, user_data)
        
        # Показываем сообщение об успехе и редиректим на страницу входа
        return templates.TemplateResponse("register.html", {
            "request": request,
            "success": f"Пользователь {user.first_name} {user.last_name} успешно зарегистрирован! Теперь вы можете войти в систему."
        })
        
    except Exception as e:
        # Обрабатываем ошибки валидации Pydantic и SQLAlchemy
        error_message = str(e)
        
        # SQLAlchemy ошибки
        if "duplicate key value violates unique constraint" in error_message and "users_email_key" in error_message:
            error_message = "Пользователь с таким email уже существует"
        # Pydantic ошибки валидации
        elif "Имя должно начинаться с заглавной буквы" in error_message:
            error_message = "Имя должно начинаться с заглавной буквы, остальные строчные"
        elif "Имя должно содержать только буквы" in error_message:
            error_message = "Имя должно содержать только буквы"
        elif "Отчество должно начинаться с заглавной буквы" in error_message:
            error_message = "Отчество должно начинаться с заглавной буквы, остальные строчные"
        elif "Отчество должно содержать только буквы" in error_message:
            error_message = "Отчество должно содержать только буквы"
        elif "Пароль должен содержать минимум одну букву" in error_message:
            error_message = "Пароль должен содержать минимум одну букву"
        elif "Пароль должен содержать минимум одну цифру" in error_message:
            error_message = "Пароль должен содержать минимум одну цифру"
        elif "Пароли не совпадают" in error_message:
            error_message = "Пароли не совпадают"
        elif "Пользователь с таким email уже существует" in error_message:
            error_message = "Пользователь с таким email уже существует"
        
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": error_message,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "email": email
        })


@router.post("/auth/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token", httponly=True, samesite="lax", secure=Production)
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax", secure=Production)
    return response


@router.get("/users/me", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Страница профиля пользователя"""
    # Получаем роли пользователя
    access_control = AccessControlService(session)
    user_roles = await access_control.get_user_roles(user.id)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "user_roles": user_roles
    })


@router.get("/business/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Страница продуктов"""
    try:
        # Проверяем права доступа
        access_control = AccessControlService(session)
        
        can_read = await access_control.has_permission(user.id, "products", "read")
        can_create = await access_control.has_permission(user.id, "products", "write")
        can_edit = await access_control.has_permission(user.id, "products", "write")
        can_delete = await access_control.has_permission(user.id, "products", "delete")
        can_order = await access_control.has_permission(user.id, "orders", "write")
        
        if not can_read:
            return templates.TemplateResponse("products.html", {
                "request": request,
                "user": user,
                "products": [],  # Пустой список продуктов
                "can_create": False,
                "can_edit": False,
                "can_delete": False,
                "can_order": False,
                "error": "У вас нет прав для просмотра продуктов"
            })
        
        # Получаем продукты
        from sqlalchemy import select
        query = select(Product)
        result = await session.execute(query)
        products = result.scalars().all()
        
        return templates.TemplateResponse("products.html", {
            "request": request,
            "user": user,
            "products": products,
            "can_create": can_create,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_order": can_order
        })
        
    except Exception as e:
        return templates.TemplateResponse("products.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка загрузки продуктов: {str(e)}"
        })


@router.get("/business/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_stub(
    request: Request,
    product_id: str,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Заглушка для редактирования продукта - проверка прав доступа"""
    access_control = AccessControlService(session)
    can_edit = await access_control.has_permission(user.id, "products", "write")
    
    if can_edit:
        return templates.TemplateResponse("stub.html", {
            "request": request,
            "user": user,
            "title": "Редактирование продукта",
            "message": f"✅ У вас есть права для редактирования продукта {product_id}",
            "description": "Это заглушка. В реальном приложении здесь была бы форма редактирования."
        })
    else:
        return templates.TemplateResponse("stub.html", {
            "request": request,
            "user": user,
            "title": "Доступ запрещен",
            "message": "❌ У вас нет прав для редактирования продуктов",
            "description": "Только менеджеры и администраторы могут редактировать продукты."
        })


@router.get("/business/orders/create", response_class=HTMLResponse)
async def create_order_page(
    request: Request,
    product_id: str = None,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Страница создания заказа"""
    try:
        # Проверяем права на создание заказов
        access_control = AccessControlService(session)
        can_order = await access_control.has_permission(user.id, "orders", "write")
        
        if not can_order:
            return templates.TemplateResponse("create_order.html", {
                "request": request,
                "user": user,
                "error": "У вас нет прав для создания заказов"
            })
        
        # Получаем продукт, если указан product_id
        product = None
        if product_id:
            product = await session.get(Product, product_id)
            if not product:
                return templates.TemplateResponse("create_order.html", {
                    "request": request,
                    "user": user,
                    "error": "Продукт не найден"
                })
        
        # Получаем все продукты для выбора
        from sqlalchemy import select
        query = select(Product)
        result = await session.execute(query)
        products = result.scalars().all()
        
        return templates.TemplateResponse("create_order.html", {
            "request": request,
            "user": user,
            "products": products,
            "selected_product": product
        })
        
    except Exception as e:
        return templates.TemplateResponse("create_order.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка загрузки страницы: {str(e)}"
        })


@router.post("/business/orders/create")
async def create_order_submit(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(...),
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Создание заказа"""
    try:
        # Проверяем права на создание заказов
        access_control = AccessControlService(session)
        can_order = await access_control.has_permission(user.id, "orders", "write")
        
        if not can_order:
            return templates.TemplateResponse("create_order.html", {
                "request": request,
                "user": user,
                "error": "У вас нет прав для создания заказов"
            })
        
        # Получаем продукт
        product = await session.get(Product, product_id)
        if not product:
            return templates.TemplateResponse("create_order.html", {
                "request": request,
                "user": user,
                "error": "Продукт не найден"
            })
        
        # Создаем заказ
        total_amount = product.price * quantity
        order = Order(
            user_id=user.id,
            product_id=product_id,
            quantity=quantity,
            total_amount=total_amount,
            status="pending"
        )
        
        session.add(order)
        await session.commit()
        
        # Перенаправляем на страницу заказов
        return RedirectResponse(url="/business/orders/my", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("create_order.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка создания заказа: {str(e)}"
        })


@router.get("/business/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Страница заказов"""
    try:
        # Проверяем права доступа
        access_control = AccessControlService(session)
        can_read = await access_control.has_permission(user.id, "orders", "read")
        
        if not can_read:
            return templates.TemplateResponse("orders.html", {
                "request": request,
                "user": user,
                "error": "У вас нет прав для просмотра заказов"
            })
        
        # Получаем заказы в зависимости от роли
        from sqlalchemy import select
        access_control = AccessControlService(session)
        is_admin = await access_control.is_admin(user.id)
        is_manager = await access_control.has_role(user.id, "manager")
        
        if is_admin or is_manager:
            # Админы и менеджеры видят все заказы
            query = select(Order)
            result = await session.execute(query)
            orders = result.scalars().all()
            
            return templates.TemplateResponse("orders.html", {
                "request": request,
                "user": user,
                "orders": orders,
                "show_all_orders": True
            })
        else:
            # Обычные пользователи видят сообщение о недостатке прав
            return templates.TemplateResponse("orders.html", {
                "request": request,
                "user": user,
                "orders": [],
                "show_all_orders": False,
                "access_denied_message": "У вас нет доступа ко всем заказам. Перейдите в 'Мои заказы' для просмотра ваших заказов."
            })
        
    except Exception as e:
        return templates.TemplateResponse("orders.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка загрузки заказов: {str(e)}"
        })


@router.get("/business/orders/my", response_class=HTMLResponse)
async def my_orders_page(
    request: Request,
    user=Depends(get_user_strict),
    session: AsyncSession = Depends(get_db)
):
    """Страница моих заказов"""
    try:
        # Получаем заказы пользователя
        from sqlalchemy import select
        query = select(Order).where(Order.user_id == user.id)
        result = await session.execute(query)
        orders = result.scalars().all()
        
        return templates.TemplateResponse("my_orders.html", {
            "request": request,
            "user": user,
            "orders": orders
        })
        
    except Exception as e:
        return templates.TemplateResponse("my_orders.html", {
            "request": request,
            "user": user,
            "error": f"Ошибка загрузки заказов: {str(e)}"
        })


# Подключаем админ-роутер
router.include_router(admin_router)

