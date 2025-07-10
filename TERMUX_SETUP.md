# 📱 Запуск Селла на телефоне через Termux

## 🚀 Быстрая установка

### 1. Установка Termux
1. Скачайте Termux из F-Droid (рекомендуется) или Google Play
2. Откройте Termux

### 2. Обновление системы
```bash
pkg update && pkg upgrade -y
```

### 3. Установка Python и зависимостей
```bash
pkg install python git -y
```

### 4. Клонирование репозитория
```bash
cd ~
git clone https://github.com/1Momori1/Sella-bot.git
cd Sella-bot
```

### 5. Установка Python зависимостей
```bash
pip install -r requirements.txt
```

### 6. Настройка конфигурации
```bash
cp config.example.json config.json
nano config.json
```

Добавьте токен вашего бота в `config.json`:
```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "admin_ids": [123456789],
  "permissions": {
    "system": ["view", "monitor"],
    "server": ["view", "start", "stop", "backup"],
    "storage": ["view", "upload", "download", "delete"],
    "admin": ["users", "permissions", "logs", "config"]
  }
}
```

### 7. Запуск бота
```bash
python main.py
```

## 🔧 Дополнительные настройки

### Автозапуск при загрузке Termux
Создайте файл `~/.bashrc`:
```bash
echo "cd ~/Sella-bot && python main.py" >> ~/.bashrc
```

### Запуск в фоновом режиме
```bash
nohup python main.py > bot.log 2>&1 &
```

### Просмотр логов
```bash
tail -f bot.log
```

## 📊 Особенности работы на телефоне

### Мониторинг системы
- **CPU**: Показывает загрузку процессора телефона
- **RAM**: Использование оперативной памяти
- **Батарея**: Уровень заряда и статус зарядки
- **Хранилище**: Свободное место на внутреннем диске
- **Сеть**: Скорость передачи данных

### Облачное хранилище
- **Локальное хранение**: Файлы сохраняются в папке `storage/` на телефоне
- **Ограничения**: 50MB на файл, 1GB общий объем
- **Безопасность**: Проверка типов файлов, запрет исполняемых файлов

### Динамический мониторинг
- **Автообновление**: Каждые 2 секунды при активном просмотре
- **Умная остановка**: Автоматически останавливается при выходе из раздела
- **Горизонтальные шкалы**: Визуальное отображение загрузки системы

## 🛠️ Устранение проблем

### Ошибка "Permission denied"
```bash
chmod +x main.py
```

### Ошибка "Module not found"
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Проблемы с сетью
```bash
termux-wake-lock
```

### Очистка кэша
```bash
pkg clean
```

## 📱 Оптимизация для телефона

### Экономия батареи
- Мониторинг останавливается при неактивности
- Файлы хранятся локально (нет сетевых запросов)
- Минимальное использование ресурсов

### Удобство использования
- Адаптивное меню для маленьких экранов
- Кнопки оптимального размера для пальцев
- Понятная навигация

## 🔄 Обновление бота

### Автоматическое обновление
```bash
cd ~/Sella-bot
git pull
pip install -r requirements.txt --upgrade
```

### Ручное обновление
```bash
cd ~/Sella-bot
git fetch origin
git reset --hard origin/master
pip install -r requirements.txt
```

## 📊 Мониторинг производительности

### Проверка использования ресурсов
```bash
top
```

### Просмотр логов
```bash
tail -f ~/Sella-bot/logs/system.log
```

### Очистка старых данных
```bash
cd ~/Sella-bot
python -c "from services.system_monitor import SystemMonitor; SystemMonitor().cleanup_old_data()"
```

## 🎯 Готово!

Теперь ваш бот Селла работает на телефоне и готов к использованию!

**Основные функции:**
- ✅ Динамический мониторинг системы
- ✅ Облачное хранилище файлов
- ✅ Управление сервером
- ✅ Админ-панель
- ✅ Система уведомлений

**Для запуска:** `python main.py`
**Для остановки:** `Ctrl+C`
**Для фонового режима:** `nohup python main.py &` 