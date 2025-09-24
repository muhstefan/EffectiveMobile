from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from effective_mobile_fast_api.core.models.base import BaseModel


class UserStatus(str, Enum):
    active = "active"
    deleted = "deleted"


class User(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    email: str = Field(..., max_length=100, unique=True)
    password_hash: str
    status: UserStatus = Field(default=UserStatus.active)
    
    # Связи с ролями
    user_roles: List["UserRole"] = Relationship(back_populates="user")


class Role(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(..., max_length=50, unique=True)
    description: Optional[str] = Field(default=None, max_length=200)
    
    # Связи
    user_roles: List["UserRole"] = Relationship(back_populates="role")
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")


class Permission(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(..., max_length=100, unique=True)
    resource: str = Field(..., max_length=50)  # например: "users", "products", "orders"
    action: str = Field(..., max_length=50)    # например: "read", "write", "delete"
    description: Optional[str] = Field(default=None, max_length=200)
    
    # Связи
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")


class UserRole(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    role_id: str = Field(foreign_key="roles.id")
    
    # Связи
    user: "User" = Relationship(back_populates="user_roles")
    role: "Role" = Relationship(back_populates="user_roles")
    
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )


class RolePermission(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    role_id: str = Field(foreign_key="roles.id")
    permission_id: str = Field(foreign_key="permissions.id")
    
    # Связи
    role: "Role" = Relationship(back_populates="role_permissions")
    permission: "Permission" = Relationship(back_populates="role_permissions")
    
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


# Бизнес-модели
class Product(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: float = Field(..., ge=0)
    category: str = Field(..., max_length=50)


class Order(BaseModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    product_id: str = Field(foreign_key="products.id")
    quantity: int = Field(..., ge=1)
    total_amount: float = Field(..., ge=0)
    status: str = Field(default="pending", max_length=20)
    
    # Связи
    user: "User" = Relationship()
    product: "Product" = Relationship()

