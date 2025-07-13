# 🐧 Установка бота в Termux

## 📋 Предварительные требования

1. **Termux** - установлен из F-Droid (не из Google Play)
2. **Интернет соединение** для загрузки пакетов

## 🚀 Быстрая установка

### Шаг 1: Обновление системы
```bash
pkg update -y && pkg upgrade -y
```

### Шаг 2: Установка необходимых пакетов
```bash
pkg install python python-pip git -y
```

### Шаг 3: Клонирование проекта
```bash
git clone <ваш-репозиторий>
cd <папка-проекта>
```

### Шаг 4: Запуск автоматической установки
```bash
chmod +x start_termux.sh
./start_termux.sh
```

## 🔧 Ручная установка

### 1. Установка Python и зависимостей
```bash
pkg install python python-pip -y
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Установка Python библиотек
```bash
pip install -r requirements_termux.txt
```

### 4. Настройка конфигурации
Отредактируйте `config.json`:
```json
{
  "bot_token": "ВАШ_ТОКЕН_БОТА",
  "admin_ids": [ВАШ_TELEGRAM_ID],
  "termux_mode": true
}
```

### 5. Запуск бота
```bash
python main.py
```

## ⚠️ Важные особенности Termux

### Проблемы с библиотеками
- **matplotlib/plotly** - не работают в Termux
- **WMI** - только для Windows
- **aiohttp** - может требовать дополнительных пакетов

### Решения:
1. Используется `simple_analytics.py` вместо matplotlib
2. Убраны Windows-специфичные библиотеки
3. Упрощена система мониторинга

### Ограничения Termux:
- Нет графического интерфейса
- Ограниченный доступ к системным ресурсам
- Может быть медленнее чем на ПК

## 📊 Аналитика в Termux

Вместо графиков используется текстовая аналитика:

```python
from simple_analytics import SimpleAnalytics

analytics = SimpleAnalytics()
analytics.record_system_stats()
analytics.record_bot_event("startup")
print(analytics.get_performance_report())
```

## 🔄 Автозапуск в Termux

### Вариант 1: Через cron
```bash
# Установка cronie
pkg install cronie -y

# Редактирование crontab
crontab -e

# Добавить строку для автозапуска
@reboot cd /path/to/bot && ./start_termux.sh
```

### Вариант 2: Через screen
```bash
# Установка screen
pkg install screen -y

# Создание сессии
screen -S bot
cd /path/to/bot
./start_termux.sh

# Отключение от сессии (Ctrl+A, затем D)
# Подключение к сессии
screen -r bot
```

## 🛠️ Устранение проблем

### Ошибка "Permission denied"
```bash
chmod +x start_termux.sh
```

### Ошибка "Module not found"
```bash
source venv/bin/activate
pip install -r requirements_termux.txt
```

### Ошибка "No space left"
```bash
pkg clean
rm -rf ~/.cache/pip
```

### Бот не запускается
```bash
# Проверка логов
tail -f logs/bot.log

# Проверка конфигурации
python -c "import json; print(json.load(open('config.json')))"
```

## 📱 Управление через Telegram

После запуска бота используйте команды:
- `/start` - запуск бота
- `/status` - статус системы
- `/analytics` - аналитика
- `/restart` - перезапуск
- `/stop` - остановка

## 🔒 Безопасность

1. Не публикуйте токен бота
2. Используйте только доверенные репозитории
3. Регулярно обновляйте Termux
4. Ограничьте доступ к боту только администраторам

## 📞 Поддержка

При проблемах:
1. Проверьте логи в папке `logs/`
2. Убедитесь в правильности конфигурации
3. Проверьте интернет соединение
4. Перезапустите Termux при необходимости 