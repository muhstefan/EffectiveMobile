#!/bin/bash

echo "🚀 Запуск системы авторизации с инициализацией тестовых данных"
echo "=============================================================="

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск с инициализацией данных
echo "🔨 Сборка и запуск приложения с тестовыми данными..."
docker-compose --profile init up --build

echo "✅ Приложение запущено с тестовыми данными!"
echo "📖 API документация: http://localhost:8000/docs"
echo "🌐 Приложение: http://localhost:8000"
echo ""
echo "Тестовые пользователи:"
echo "👑 Админ: admin@example.com / admin123"
echo "👨‍💼 Менеджер: manager@example.com / manager123"
echo "👤 Пользователь: user@example.com / user123"



