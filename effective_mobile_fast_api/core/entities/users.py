from enum import Enum
from typing import Optional, List
import re

from pydantic import BaseModel, Field, EmailStr, field_validator
from pydantic import ConfigDict

from effective_mobile_fast_api.core.models.tables import UserStatus


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=25)
    last_name: str = Field(..., min_length=2, max_length=25)
    middle_name: Optional[str] = Field(default=None, max_length=25)
    email: EmailStr = Field(..., max_length=100)
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_required_name(cls, v):
        # Проверяем, что первая буква заглавная, остальные строчные
        if not v[0].isupper() or not v[1:].islower():
            raise ValueError('Имя должно начинаться с заглавной буквы, остальные строчные')
        # Проверяем, что только буквы
        if not v.isalpha():
            raise ValueError('Имя должно содержать только буквы')
        return v
    
    @field_validator('middle_name')
    @classmethod
    def validate_optional_name(cls, v):
        if v is None or v == "":
            return None
        # Проверяем, что первая буква заглавная, остальные строчные
        if not v[0].isupper() or not v[1:].islower():
            raise ValueError('Отчество должно начинаться с заглавной буквы, остальные строчные')
        # Проверяем, что только буквы
        if not v.isalpha():
            raise ValueError('Отчество должно содержать только буквы')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    password_confirm: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Проверяем, что пароль содержит минимум одну цифру и одну букву
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Пароль должен содержать минимум одну букву')
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать минимум одну цифру')
        return v
    
    @field_validator('password_confirm')
    @classmethod
    def validate_password_confirm(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v


class UserCreateDB(UserBase):
    password_hash: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = Field(default=None, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


class UserRead(UserBase):
    id: str
    status: UserStatus
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    id: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    email: str
    status: UserStatus
    model_config = ConfigDict(from_attributes=True)


# RBAC схемы
class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)


class PermissionCreate(PermissionBase):
    pass


class PermissionRead(PermissionBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class UserRoleCreate(BaseModel):
    user_id: str
    role_id: str


class UserRoleRead(BaseModel):
    id: str
    user_id: str
    role_id: str
    role: RoleRead
    model_config = ConfigDict(from_attributes=True)


class RolePermissionCreate(BaseModel):
    role_id: str
    permission_id: str


class RolePermissionRead(BaseModel):
    id: str
    role_id: str
    permission_id: str
    permission: PermissionRead
    model_config = ConfigDict(from_attributes=True)


# Бизнес-схемы
class ProductBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: float = Field(..., ge=0)
    category: str = Field(..., max_length=50)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    user_id: str
    product_id: str
    quantity: int = Field(..., ge=1)
    total_amount: float = Field(..., ge=0)
    status: str = Field(default="pending", max_length=20)


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: str
    product: ProductRead
    model_config = ConfigDict(from_attributes=True)
