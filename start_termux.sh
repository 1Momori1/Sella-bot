#!/data/data/com.termux/files/usr/bin/bash

echo "🤖 Запуск бота Селла в Termux..."
echo "=================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка интернета
check_internet() {
    print_step "Проверка интернет соединения..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_status "Интернет соединение работает"
    else
        print_error "Нет интернет соединения!"
        exit 1
    fi
}

# Обновление репозитория Termux
update_repo() {
    print_step "Обновление репозитория Termux..."
    if command -v termux-change-repo >/dev/null 2>&1; then
        print_warning "Выполните 'termux-change-repo' для выбора репозитория"
        print_warning "Выберите любой доступный репозиторий"
    fi
    
    pkg update -y
    if [ $? -eq 0 ]; then
        print_status "Репозиторий обновлен"
    else
        print_warning "Ошибка обновления репозитория, продолжаем..."
    fi
}

# Установка системных пакетов
install_system_packages() {
    print_step "Установка системных пакетов..."
    
    # Список пакетов для установки
    packages="python python-pip git"
    
    # Попытка установить дополнительные пакеты (если доступны)
    additional_packages="libjpeg-turbo libpng freetype clang"
    
    for pkg in $packages; do
        print_status "Установка $pkg..."
        pkg install $pkg -y
    done
    
    # Попытка установить дополнительные пакеты
    for pkg in $additional_packages; do
        print_status "Попытка установки $pkg..."
        pkg install $pkg -y 2>/dev/null || print_warning "$pkg недоступен, пропускаем"
    done
}

# Создание виртуального окружения
setup_virtual_env() {
    print_step "Настройка виртуального окружения..."
    
    if [ ! -d "venv" ]; then
        print_status "Создание виртуального окружения..."
        python -m venv venv
    else
        print_status "Виртуальное окружение уже существует"
    fi
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Обновление pip
    print_status "Обновление pip..."
    pip install --upgrade pip
}

# Установка Python зависимостей
install_python_deps() {
    print_step "Установка Python зависимостей..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Установка основных зависимостей
    print_status "Установка python-telegram-bot..."
    pip install python-telegram-bot==20.7
    
    print_status "Установка psutil..."
    pip install psutil==5.9.6
    
    # Проверка установки
    if python -c "import telegram; import psutil; print('✅ Все модули установлены')" 2>/dev/null; then
        print_status "Все зависимости установлены успешно!"
    else
        print_error "Ошибка установки зависимостей!"
        exit 1
    fi
}

# Создание необходимых папок
create_directories() {
    print_step "Создание необходимых папок..."
    
    mkdir -p logs
    mkdir -p storage
    mkdir -p storage/backups
    
    print_status "Папки созданы"
}

# Проверка конфигурации
check_config() {
    print_step "Проверка конфигурации..."
    
    if [ ! -f "config.json" ]; then
        print_error "Файл config.json не найден!"
        print_warning "Создайте config.json с вашим токеном бота"
        exit 1
    fi
    
    # Проверка токена
    if grep -q "ВАШ_ТОКЕН_ЗДЕСЬ" config.json; then
        print_warning "Токен бота не настроен!"
        print_warning "Отредактируйте config.json и вставьте ваш токен"
        print_warning "Получите токен у @BotFather в Telegram"
        exit 1
    fi
    
    print_status "Конфигурация проверена"
}

# Запуск бота
start_bot() {
    print_step "Запуск бота..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    print_status "Бот запускается..."
    print_status "Для остановки нажмите Ctrl+C"
    echo ""
    
    # Запуск бота
    python main.py
}

# Основная функция
main() {
    echo "🤖 Автоматическая установка и запуск бота Селла"
    echo "================================================"
    echo ""
    
    # Проверки
    check_internet
    update_repo
    install_system_packages
    setup_virtual_env
    install_python_deps
    create_directories
    check_config
    
    echo ""
    print_status "Установка завершена успешно!"
    echo ""
    
    # Запуск бота
    start_bot
}

# Запуск основной функции
main 