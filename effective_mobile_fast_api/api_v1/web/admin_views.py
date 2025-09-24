from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from effective_mobile_fast_api.api_v1.auth.dependencies import get_user_strict, require_admin
from effective_mobile_fast_api.core.db import get_db
from effective_mobile_fast_api.core.models.tables import User, Role, Permission, UserRole, RolePermission, UserStatus
from effective_mobile_fast_api.core.entities.users import UserCreate
from effective_mobile_fast_api.api_v1.auth.crud import create_user_db, get_user_by_email
from effective_mobile_fast_api.api_v1.auth.security import hash_password

router = APIRouter(tags=["Admin Web"])
templates = Jinja2Templates(directory="effective_mobile_fast_api/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    current_user=Depends(require_admin)
):
    """Главная страница админ-панели"""
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": current_user
    })


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Страница управления пользователями"""
    try:
        # Получаем всех пользователей с их ролями
        query = select(User)
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Загружаем роли для каждого пользователя и создаем словари
        users_data = []
        for user in users:
            user_roles_query = (
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user.id)
            )
            user_roles_result = await session.execute(user_roles_query)
            user_roles = list(user_roles_result.scalars().all())
            
            # Создаем словарь с данными пользователя
            user_data = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "middle_name": user.middle_name,
                "email": user.email,
                "status": user.status,
                "roles": user_roles
            }
            users_data.append(user_data)
        
        return templates.TemplateResponse("admin_users.html", {
            "request": request,
            "user": current_user,
            "users": users_data
        })
    except Exception as e:
        return templates.TemplateResponse("admin_users.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка загрузки пользователей: {str(e)}"
        })


@router.post("/admin/users/create")
async def admin_create_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Создание нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await get_user_by_email(session, email)
        if existing_user:
            return templates.TemplateResponse("admin_users.html", {
                "request": request,
                "user": current_user,
                "error": "Пользователь с таким email уже существует"
            })
        
        # Создаем пользователя
        user_data = UserCreate(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            password=password
        )
        
        user = await create_user_db(session, user_data)
        
        return RedirectResponse(url="/admin/users?success=Пользователь создан успешно", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse("admin_users.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка создания пользователя: {str(e)}"
        })


@router.post("/admin/users/{user_id}/delete")
async def admin_delete_user(
    user_id: str,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Мягкое удаление пользователя"""
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        user.status = UserStatus.deleted
        session.add(user)
        await session.commit()
        
        return RedirectResponse(url="/admin/users?success=Пользователь удален", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error=Ошибка удаления: {str(e)}", status_code=302)


@router.post("/admin/users/{user_id}/restore")
async def admin_restore_user(
    user_id: str,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Восстановление пользователя"""
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        user.status = UserStatus.active
        session.add(user)
        await session.commit()
        
        return RedirectResponse(url="/admin/users?success=Пользователь восстановлен", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error=Ошибка восстановления: {str(e)}", status_code=302)


@router.get("/admin/roles", response_class=HTMLResponse)
async def admin_roles(
    request: Request,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Страница управления ролями"""
    try:
        # Получаем все роли с их разрешениями
        query = select(Role)
        result = await session.execute(query)
        roles = result.scalars().all()
        
        # Загружаем разрешения и количество пользователей для каждой роли
        roles_data = []
        for role in roles:
            # Разрешения роли
            role_permissions_query = (
                select(Permission)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .where(RolePermission.role_id == role.id)
            )
            role_permissions_result = await session.execute(role_permissions_query)
            role_permissions = list(role_permissions_result.scalars().all())
            
            # Количество пользователей с этой ролью
            user_count_query = select(func.count(UserRole.id)).where(UserRole.role_id == role.id)
            user_count_result = await session.execute(user_count_query)
            user_count = user_count_result.scalar()
            
            # Создаем словарь с данными роли
            role_data = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role_permissions,
                "user_count": user_count
            }
            roles_data.append(role_data)
        
        return templates.TemplateResponse("admin_roles.html", {
            "request": request,
            "user": current_user,
            "roles": roles_data
        })
    except Exception as e:
        return templates.TemplateResponse("admin_roles.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка загрузки ролей: {str(e)}"
        })




@router.get("/admin/permissions", response_class=HTMLResponse)
async def admin_permissions(
    request: Request,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Страница управления разрешениями"""
    try:
        # Получаем все разрешения
        query = select(Permission)
        result = await session.execute(query)
        permissions = result.scalars().all()
        
        # Загружаем количество ролей для каждого разрешения
        for permission in permissions:
            role_count_query = select(func.count(RolePermission.id)).where(RolePermission.permission_id == permission.id)
            role_count_result = await session.execute(role_count_query)
            permission.role_count = role_count_result.scalar()
        
        return templates.TemplateResponse("admin_permissions.html", {
            "request": request,
            "user": current_user,
            "permissions": permissions
        })
    except Exception as e:
        return templates.TemplateResponse("admin_permissions.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка загрузки разрешений: {str(e)}"
        })




@router.post("/admin/users/{user_id}/roles/assign")
async def admin_assign_role(
    user_id: str,
    role_id: str = Form(...),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Назначить роль пользователю"""
    try:
        # Проверяем, что роль еще не назначена
        existing_query = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
        existing_result = await session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=Роль уже назначена", status_code=302)
        
        # Назначаем роль
        user_role = UserRole(user_id=user_id, role_id=role_id)
        session.add(user_role)
        await session.commit()
        
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?success=Роль назначена", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=Ошибка назначения роли: {str(e)}", status_code=302)


@router.post("/admin/users/{user_id}/roles/remove")
async def admin_remove_role(
    user_id: str,
    role_id: str = Form(...),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Убрать роль у пользователя"""
    try:
        # Находим и удаляем связь
        user_role_query = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
        user_role_result = await session.execute(user_role_query)
        user_role = user_role_result.scalar_one_or_none()
        
        if user_role:
            await session.delete(user_role)
            await session.commit()
        
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?success=Роль удалена", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=Ошибка удаления роли: {str(e)}", status_code=302)


@router.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user(
    user_id: str,
    request: Request,
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Страница редактирования пользователя"""
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Получаем все роли
        all_roles_query = select(Role)
        all_roles_result = await session.execute(all_roles_query)
        all_roles = all_roles_result.scalars().all()
        
        # Получаем роли пользователя
        user_roles_query = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        user_roles_result = await session.execute(user_roles_query)
        user_roles = list(user_roles_result.scalars().all())
        user_role_ids = {role.id for role in user_roles}
        
        # Создаем объект пользователя с ролями
        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "email": user.email,
            "status": user.status,
            "roles": user_roles
        }
        
        return templates.TemplateResponse("admin_edit_user.html", {
            "request": request,
            "user": current_user,
            "target_user": user_data,
            "all_roles": all_roles,
            "user_role_ids": user_role_ids
        })
    except Exception as e:
        return templates.TemplateResponse("admin_edit_user.html", {
            "request": request,
            "user": current_user,
            "error": f"Ошибка загрузки пользователя: {str(e)}"
        })


@router.post("/admin/users/{user_id}/edit")
async def admin_update_user(
    user_id: str,
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str = Form(None),
    email: str = Form(...),
    current_user=Depends(require_admin),
    session: AsyncSession = Depends(get_db)
):
    """Обновление данных пользователя"""
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем, не занят ли email другим пользователем
        if email != user.email:
            existing_user = await get_user_by_email(session, email)
            if existing_user:
                return templates.TemplateResponse("admin_edit_user.html", {
                    "request": request,
                    "user": current_user,
                    "target_user": user,
                    "error": "Пользователь с таким email уже существует"
                })
        
        # Обновляем данные
        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name
        user.email = email
        
        session.add(user)
        await session.commit()
        
        return RedirectResponse(url="/admin/users?success=Пользователь обновлен", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse("admin_edit_user.html", {
            "request": request,
            "user": current_user,
            "target_user": user,
            "error": f"Ошибка обновления пользователя: {str(e)}"
        })
