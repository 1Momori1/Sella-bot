#!/bin/bash

echo "🚀 Автоматическая установка бота Селла"
echo "======================================"

# Проверяем интернет
if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "❌ Нет интернет соединения!"
    exit 1
fi

# Скачиваем автоустановщик
echo "📥 Загрузка автоустановщика..."
curl -s https://raw.githubusercontent.com/1Momori1/Sella-bot/master/auto_install.sh > auto_install.sh

# Делаем исполняемым
chmod +x auto_install.sh

# Запускаем автоустановщик
echo "⚡ Запуск автоустановщика..."
./auto_install.sh 