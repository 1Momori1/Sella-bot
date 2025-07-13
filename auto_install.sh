#!/data/data/com.termux/files/usr/bin/bash

# Автономный установщик бота Селла для Termux
# Автоматически определяет и устанавливает все необходимые зависимости

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Функции для вывода
print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
print_success() { echo -e "${CYAN}[SUCCESS]${NC} $1"; }

# Функция проверки команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Функция проверки файла
file_exists() {
    [ -f "$1" ]
}

# Функция проверки директории
dir_exists() {
    [ -d "$1" ]
}

# Функция проверки интернета
check_internet() {
    print_step "Проверка интернет соединения..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_success "Интернет соединение работает"
        return 0
    else
        print_error "Нет интернет соединения!"
        return 1
    fi
}

# Функция определения архитектуры и версии Termux
detect_system() {
    print_step "Определение системы..."
    
    # Архитектура
    ARCH=$(uname -m)
    print_info "Архитектура: $ARCH"
    
    # Версия Termux
    if file_exists "/data/data/com.termux/files/usr/bin/termux-info"; then
        TERMUX_VERSION=$(termux-info | grep "TERMUX_VERSION" | cut -d'=' -f2)
        print_info "Версия Termux: $TERMUX_VERSION"
    else
        print_warn "Не удалось определить версию Termux"
    fi
    
    # Версия Python
    if command_exists python; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        print_info "Версия Python: $PYTHON_VERSION"
    fi
}

# Функция настройки репозитория
setup_repository() {
    print_step "Настройка репозитория Termux..."
    
    # Проверяем текущий репозиторий
    if file_exists "/data/data/com.termux/files/usr/etc/apt/sources.list.d/termux-main.list"; then
        CURRENT_REPO=$(cat /data/data/com.termux/files/usr/etc/apt/sources.list.d/termux-main.list | head -1)
        print_info "Текущий репозиторий: $CURRENT_REPO"
    fi
    
    # Обновляем пакеты
    print_info "Обновление списка пакетов..."
    pkg update -y || {
        print_warn "Ошибка обновления репозитория, попробуем другой способ..."
        # Попытка обновления без обновления репозитория
        pkg update --no-upgrade -y || print_warn "Продолжаем без обновления..."
    }
}

# Функция установки системных пакетов
install_system_packages() {
    print_step "Установка системных пакетов..."
    
    # Основные пакеты (обязательные)
    ESSENTIAL_PACKAGES="python python-pip git"
    
    # Дополнительные пакеты (опциональные)
    OPTIONAL_PACKAGES="libjpeg-turbo libpng freetype clang"
    
    # Устанавливаем обязательные пакеты
    for pkg in $ESSENTIAL_PACKAGES; do
        if ! command_exists $pkg; then
            print_info "Установка $pkg..."
            pkg install $pkg -y || print_error "Ошибка установки $pkg"
        else
            print_info "$pkg уже установлен"
        fi
    done
    
    # Пытаемся установить опциональные пакеты
    for pkg in $OPTIONAL_PACKAGES; do
        print_info "Попытка установки $pkg..."
        pkg install $pkg -y 2>/dev/null && print_success "$pkg установлен" || print_warn "$pkg недоступен, пропускаем"
    done
}

# Функция создания виртуального окружения
setup_virtual_env() {
    print_step "Настройка виртуального окружения..."
    
    if ! dir_exists "venv"; then
        print_info "Создание виртуального окружения..."
        python -m venv venv || {
            print_error "Ошибка создания виртуального окружения!"
            return 1
        }
    else
        print_info "Виртуальное окружение уже существует"
    fi
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Обновление pip
    print_info "Обновление pip..."
    pip install --upgrade pip || print_warn "Ошибка обновления pip, продолжаем..."
}

# Функция установки Python зависимостей
install_python_deps() {
    print_step "Установка Python зависимостей..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Список зависимостей с версиями
    DEPS=(
        "python-telegram-bot==20.7"
        "psutil==5.9.6"
    )
    
    # Устанавливаем каждую зависимость отдельно
    for dep in "${DEPS[@]}"; do
        print_info "Установка $dep..."
        pip install $dep || {
            print_error "Ошибка установки $dep"
            return 1
        }
    done
    
    # Проверяем установку
    print_info "Проверка установленных модулей..."
    if python -c "
import telegram
import psutil
import asyncio
if python -c "import telegram, psutil, asyncio, json, os, logging; print('All modules installed successfully')" 2>/dev/null; then
        print_success "Все зависимости установлены успешно!"
    else
        print_error "Ошибка проверки зависимостей!"
        return 1
    fi
}

# Функция создания структуры папок
create_project_structure() {
    print_step "Создание структуры проекта..."
    
    # Список необходимых папок
    DIRS=(
        "logs"
        "storage"
        "storage/backups"
        "storage/temp"
    )
    
    for dir in "${DIRS[@]}"; do
        if ! dir_exists "$dir"; then
            print_info "Создание папки $dir..."
            mkdir -p "$dir"
        else
            print_info "Папка $dir уже существует"
        fi
    done
}

# Функция проверки и создания конфигурации
setup_config() {
    print_step "Настройка конфигурации..."
    
    if ! file_exists "config.json"; then
        print_warn "Файл config.json не найден, создаем шаблон..."
        cat > config.json << 'EOF'
{
  "bot_token": "ВАШ_ТОКЕН_ЗДЕСЬ",
  "admin_ids": [ВАШ_TELEGRAM_ID],
  "termux_mode": true,
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot.log"
  },
  "storage": {
    "path": "storage",
    "max_file_size": 52428800
  },
  "security": {
    "max_failed_attempts": 5,
    "session_timeout": 3600
  }
}
EOF
        print_info "Создан шаблон config.json"
        print_warn "Отредактируйте config.json и вставьте ваш токен бота!"
        return 1
    fi
    
    # Проверяем токен
    if grep -q "ВАШ_ТОКЕН_ЗДЕСЬ" config.json; then
        print_warn "Токен бота не настроен!"
        print_info "Отредактируйте config.json и вставьте ваш токен от @BotFather"
        return 1
    fi
    
    print_success "Конфигурация проверена"
    return 0
}

# Функция проверки готовности к запуску
check_readiness() {
    print_step "Проверка готовности к запуску..."
    
    local errors=0
    
    # Проверяем Python
    if ! command_exists python; then
        print_error "Python не установлен!"
        ((errors++))
    fi
    
    # Проверяем виртуальное окружение
    if ! dir_exists "venv"; then
        print_error "Виртуальное окружение не создано!"
        ((errors++))
    fi
    
    # Проверяем основные файлы
    if ! file_exists "main.py"; then
        print_error "Файл main.py не найден!"
        ((errors++))
    fi
    
    # Проверяем конфигурацию
    if ! file_exists "config.json"; then
        print_error "Файл config.json не найден!"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        print_success "Система готова к запуску!"
        return 0
    else
        print_error "Найдено $errors ошибок!"
        return 1
    fi
}

# Функция запуска бота
start_bot() {
    print_step "Запуск бота..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    print_success "Бот запускается..."
    print_info "Для остановки нажмите Ctrl+C"
    echo ""
    
    # Запуск бота
    python main.py
}

# Функция диагностики проблем
diagnose_issues() {
    print_step "Диагностика проблем..."
    
    # Проверяем Python модули
    source venv/bin/activate
    
    print_info "Проверка Python модулей..."
    python -c "
import sys
modules = ['telegram', 'psutil', 'asyncio', 'json', 'os', 'logging']
missing = []
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        missing.append(module)
        print(f'❌ {module}')
if missing:
    print(f'\\nОтсутствуют модули: {missing}')
    sys.exit(1)
else:
    print('\\n✅ Все модули доступны')
"
    
    # Проверяем права доступа
    print_info "Проверка прав доступа..."
    if [ -w "." ]; then
        print_success "Права на запись в текущую папку есть"
    else
        print_error "Нет прав на запись в текущую папку!"
    fi
    
    # Проверяем свободное место
    print_info "Проверка свободного места..."
    FREE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ $FREE_SPACE -gt 100000 ]; then
        print_success "Свободного места достаточно: ${FREE_SPACE}KB"
    else
        print_warn "Мало свободного места: ${FREE_SPACE}KB"
    fi
}

# Функция очистки временных файлов
cleanup_temp() {
    print_step "Очистка временных файлов..."
    
    # Удаляем временные файлы pip
    if dir_exists "/tmp"; then
        find /tmp -name "pip-*" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Удаляем кэш pip
    if dir_exists "~/.cache/pip"; then
        rm -rf ~/.cache/pip 2>/dev/null || true
    fi
    
    print_success "Временные файлы очищены"
}

# Главная функция
main() {
    echo ""
    echo "🤖 Автономный установщик бота Селла"
    echo "==================================="
    echo ""
    
    # Проверяем интернет
    if ! check_internet; then
        print_error "Нет интернет соединения! Проверьте подключение."
        exit 1
    fi
    
    # Определяем систему
    detect_system
    
    # Настраиваем репозиторий
    setup_repository
    
    # Устанавливаем системные пакеты
    install_system_packages
    
    # Создаем виртуальное окружение
    if ! setup_virtual_env; then
        print_error "Ошибка создания виртуального окружения!"
        exit 1
    fi
    
    # Устанавливаем Python зависимости
    if ! install_python_deps; then
        print_error "Ошибка установки Python зависимостей!"
        print_info "Попробуйте запустить диагностику: ./auto_install.sh diagnose"
        exit 1
    fi
    
    # Создаем структуру проекта
    create_project_structure
    
    # Настраиваем конфигурацию
    if ! setup_config; then
        print_warn "Конфигурация не настроена!"
        print_info "Отредактируйте config.json и запустите скрипт снова"
        exit 1
    fi
    
    # Проверяем готовность
    if ! check_readiness; then
        print_error "Система не готова к запуску!"
        print_info "Запустите диагностику: ./auto_install.sh diagnose"
        exit 1
    fi
    
    # Очищаем временные файлы
    cleanup_temp
    
    echo ""
    print_success "Установка завершена успешно!"
    echo ""
    
    # Запускаем бота
    start_bot
}

# Обработка аргументов командной строки
case "${1:-}" in
    "diagnose")
        detect_system
        setup_virtual_env
        diagnose_issues
        ;;
    "clean")
        cleanup_temp
        ;;
    "check")
        check_readiness
        ;;
    "help"|"-h"|"--help")
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  (без аргументов) - Полная установка и запуск"
        echo "  diagnose         - Диагностика проблем"
        echo "  clean           - Очистка временных файлов"
        echo "  check           - Проверка готовности"
        echo "  help            - Эта справка"
        ;;
    *)
        main
        ;;
esac 