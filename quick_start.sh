#!/data/data/com.termux/files/usr/bin/bash

echo "⚡ Быстрый запуск бота Селла"
echo "============================"

# Проверяем, есть ли папка Sella-bot
if [ ! -d "Sella-bot" ]; then
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/1Momori1/Sella-bot.git
fi

# Переходим в папку
cd Sella-bot

# Делаем скрипт исполняемым
chmod +x start_termux.sh

# Запускаем автоматическую установку
echo "🚀 Запуск автоматической установки..."
./start_termux.sh 