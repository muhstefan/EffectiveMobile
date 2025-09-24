# Система управления ограничениями доступа (ACS)

Собственная система аутентификации и авторизации на основе ролей (Role-Based Access Control - RBAC) с административным интерфейсом для управления правами доступа.

## Быстрый запуск

### Через Docker Compose (рекомендуется)
```bash
# Запуск с автоматической инициализацией тестовых данных
docker-compose --profile init up --build

# Обычный запуск
docker-compose up --build
```

### Через скрипты
```bash
# Windows
.\start-with-data.bat    # С тестовыми данными
.\start.bat              # Без тестовых данных

# Linux/Mac
chmod +x start-with-data.sh && ./start-with-data.sh
chmod +x start.sh && ./start.sh
```

### После запуска
После сборки, перейдите на сервер: **http://localhost:8000**

**Тестовые пользователи для входа:**
- **Менеджер**: `manager@example.com` / `manager1234`
- **Админ**: `admin@example.com` / `admin1234`  
- **Пользователь**: `user@example.com` / `user1234`

### Доступные страницы по ролям

#### **Админ** (`admin@example.com`)
- Главная страница
- Все продукты
- Все заказы  
- **Админ-панель** (`/admin`)
  - Управление пользователями
  - Просмотр ролей и разрешений
  - Назначение ролей пользователям

#### **Менеджер** (`manager@example.com`)
- Главная страница
- Все продукты
- Все заказы

#### **Пользователь** (`user@example.com`)
- Главная страница
- Все продукты
- Мои заказы (только свои)
- Создание заказов

## Технологии

### Основные библиотеки
- **FastAPI** - современный веб-фреймворк для создания API
- **SQLModel** - интеграция SQLAlchemy и Pydantic для работы с БД
- **SQLAlchemy** - ORM для работы с PostgreSQL
- **Pydantic** - валидация данных и настройки
- **Alembic** - миграции базы данных
- **Jinja2** - шаблонизатор для HTML страниц
- **Uvicorn** - ASGI сервер для запуска приложения

### Аутентификация и безопасность
- **python-jose** - работа с JWT токенами
- **passlib** - хеширование паролей
- **bcrypt** - криптографическое хеширование
- **python-multipart** - обработка форм

### База данных
- **PostgreSQL** - основная база данных
- **asyncpg** - асинхронный драйвер для подключения к PostgreSQL
- **psycopg2-binary** - синхронный драйвер для миграций Alembic

### Управление зависимостями
- **Poetry** - управление зависимостями и виртуальными окружениями


## Структура системы

### Основные компоненты

1. **Пользователи (Users)** - основная сущность системы
2. **Роли (Roles)** - группы пользователей с определенными правами
3. **Разрешения (Permissions)** - конкретные действия с ресурсами
4. **Связи** - таблицы для связи пользователей с ролями и ролей с разрешениями

### Схема базы данных

```
Users (Пользователи)
├── id (PK, UUID)
├── first_name (Имя)
├── last_name (Фамилия)
├── middle_name (Отчество, опционально)
├── email (Email, уникальный)
├── password_hash (Хеш пароля)
└── status (active/deleted - для мягкого удаления)

Roles (Роли)
├── id (PK, UUID)
├── name (Название роли, уникальное)
└── description (Описание роли)

Permissions (Разрешения)
├── id (PK, UUID)
├── name (Название разрешения, уникальное)
├── resource (Ресурс: users, products, orders, admin)
├── action (Действие: read, write, delete, access)
└── description (Описание разрешения)

UserRole (Связь пользователей и ролей)
├── id (PK, UUID)
├── user_id (FK -> Users.id)
└── role_id (FK -> Roles.id)

RolePermission (Связь ролей и разрешений)
├── id (PK, UUID)
├── role_id (FK -> Roles.id)
└── permission_id (FK -> Permissions.id)

Products (Продукты)
├── id (PK, UUID)
├── name (Название)
├── description (Описание)
├── price (Цена)
└── category (Категория)

Orders (Заказы)
├── id (PK, UUID)
├── user_id (FK -> Users.id)
├── product_id (FK -> Products.id)
├── quantity (Количество)
├── total_amount (Общая сумма)
└── status (Статус заказа)
```

## Схема системы управления ограничениями доступа

### Принципы работы

#### 1. Иерархическая модель доступа
```
Пользователь → Роль → Разрешения → Ресурсы/Действия
```

#### 2. Типы разрешений
- **Ресурс (Resource)**: `products`, `orders`, `users`, `admin`
- **Действие (Action)**: `read`, `write`, `delete`, `access`

#### 3. Комбинирование прав
Разрешения формируются как: `{resource}:{action}`
- `products:read` - чтение продуктов
- `orders:write` - создание/редактирование заказов
- `admin:access` - доступ к административным функциям

### Предустановленные роли

#### admin (Администратор)
```yaml
Разрешения:
  - users:read, users:write, users:delete
  - products:read, products:write, products:delete
  - orders:read, orders:write, orders:delete
  - admin:access
  - roles:read, roles:write, roles:delete
  - permissions:read, permissions:write, permissions:delete
```

#### manager (Менеджер)
```yaml
Разрешения:
  - products:read, products:write, products:delete
  - orders:read, orders:write
  - users:read
```

#### user (Пользователь)
```yaml
Разрешения:
  - products:read
  - orders:read (только свои заказы)
  - orders:write (создание заказов)
```

### Механизм проверки прав

#### 1. Middleware аутентификации
- Проверяет JWT токены и устанавливает user_id в request.state
- Автоматическое обновление токенов

#### 2. Проверка прав доступа
- **AccessControlService** проверяет права через цепочку: User → Role → Permission
- **Dependency Injection** в FastAPI автоматически проверяет доступ к endpoints
- **401/403 ошибки** для неавторизованных/неавторизованных запросов

## Безопасность

### 1. JWT токены
- **Access Token**: короткоживущий (15 минут)
- **Refresh Token**: долгоживущий (7 дней)
- Автоматическое обновление через middleware

### 2. Хеширование паролей
- Используется bcrypt для безопасного хранения паролей

### 3. Мягкое удаление
- Пользователи помечаются как deleted, но не удаляются физически

### 4. Валидация прав
- Все административные операции требуют роль `admin`
- Проверка прав происходит на уровне каждого endpoint
- 401/403 ошибки для неавторизованных/неавторизованных запросов

## Переменные окружения

- `DB_URL` - URL подключения к базе данных PostgreSQL
- `SECRET_KEY` - Секретный ключ для JWT токенов
