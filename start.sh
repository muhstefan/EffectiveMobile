#!/bin/bash

echo "🚀 Запуск системы авторизации и аутентификации"
echo "=============================================="

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск
echo "🔨 Сборка и запуск приложения..."
docker-compose up --build

echo "✅ Приложение запущено!"
echo "📖 API документация: http://localhost:8000/docs"
echo "🌐 Приложение: http://localhost:8000"
echo ""
echo "Тестовые пользователи:"
echo "👑 Админ: admin@example.com / admin123"
echo "👨‍💼 Менеджер: manager@example.com / manager123"
echo "👤 Пользователь: user@example.com / user123"



