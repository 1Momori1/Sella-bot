#!/data/data/com.termux/files/usr/bin/bash

# Скрипт запуска бота для Termux
echo "🚀 Запуск бота в Termux..."

# Проверяем, установлен ли Python
if ! command -v python &> /dev/null; then
    echo "❌ Python не найден. Устанавливаем..."
    pkg update -y
    pkg install python -y
fi

# Проверяем, установлен ли pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip не найден. Устанавливаем..."
    pkg install python-pip -y
fi

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Устанавливаем зависимости..."
pip install -r requirements_termux.txt

# Создаем папки если их нет
mkdir -p logs
mkdir -p storage

# Запускаем бота
echo "🤖 Запускаем бота..."
python main.py 