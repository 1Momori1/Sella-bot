# 🐧 Установка бота "Селла" в Termux

## 📋 Требования
- Android 7.0+
- Termux (установить из F-Droid)
- Интернет-соединение

## 🚀 Пошаговая установка

### 1. Установка Termux
```bash
# Скачайте Termux с F-Droid (не Google Play!)
# https://f-droid.org/packages/com.termux/
```

### 2. Обновление системы
```bash
pkg update && pkg upgrade -y
```

### 3. Установка Python и зависимостей
```bash
pkg install python git -y
```

### 4. Клонирование проекта
```bash
cd ~
git clone https://github.com/your-username/sella-bot.git
cd sella-bot
```

### 5. Установка Python-зависимостей
```bash
pip install -r requirements_termux.txt
```

### 6. Настройка конфигурации
```bash
# Скопируйте пример конфигурации
cp config.example.json config.json

# Отредактируйте конфигурацию
nano config.json
```

### 7. Настройка config.json
```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "admin_ids": [YOUR_TELEGRAM_ID],
  "roles": {
    "admin": {
      "permissions": ["*"]
    },
    "moderator": {
      "permissions": ["system:view", "system:monitor", "process:view", "storage:view"]
    },
    "user": {
      "permissions": ["system:view", "storage:view"]
    },
    "guest": {
      "permissions": ["system:view"]
    }
  },
  "system": {
    "monitoring": {
      "cpu_threshold": 80,
      "memory_threshold": 85,
      "disk_threshold": 90,
      "temperature_threshold": 45
    }
  },
  "storage": {
    "path": "./storage",
    "max_file_size_mb": 50
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot_termux.log"
  }
}
```

### 8. Создание необходимых папок
```bash
mkdir -p storage logs
```

## 🏃‍♂️ Запуск бота

### Обычный запуск
```bash
python main_termux.py
```

### Запуск в фоне (рекомендуется)
```bash
# Установка screen
pkg install screen -y

# Создание новой сессии
screen -S sella-bot

# Запуск бота
python main_termux.py

# Отключение от сессии (бот продолжит работать)
# Нажмите Ctrl+A, затем D

# Подключение к сессии
screen -r sella-bot
```

### Автозапуск при загрузке Termux
```bash
# Создание скрипта автозапуска
nano ~/.bashrc

# Добавьте в конец файла:
if [ ! -f ~/.sella_running ]; then
    cd ~/sella-bot
    screen -dmS sella-bot python main_termux.py
    touch ~/.sella_running
fi
```

## 🔧 Управление ботом

### Проверка статуса
```bash
# Проверка запущенных процессов
ps aux | grep python

# Проверка логов
tail -f logs/sella_bot_termux.log
```

### Остановка бота
```bash
# Найти PID процесса
ps aux | grep main_termux.py

# Остановить процесс
kill -9 PID_NUMBER

# Или через screen
screen -X -S sella-bot quit
```

### Перезапуск бота
```bash
# Остановить
screen -X -S sella-bot quit

# Запустить заново
screen -dmS sella-bot python main_termux.py
```

## 📱 Использование в Telegram

### Основные команды
- `/start` - Запуск бота
- `/menu` - Главное меню
- `/status` - Статус системы
- `/bots` - Статус процессов
- `/storage` - Облачное хранилище
- `/help` - Справка

### Интерактивные кнопки
Бот поддерживает удобные кнопки для навигации и управления.

## ✅ Улучшения для Termux

### Расширенные возможности
1. **🌡️ Температура**: Множественные методы получения (psutil, системные файлы, команда sensors, Android-specific)
2. **🔧 Процессы**: Полное управление процессами с логированием и автоперезапуском
3. **💾 Системная информация**: Расширенная информация о CPU, RAM, диске, сети, батарее
4. **📊 Мониторинг**: Детальная статистика процессов, сетевых интерфейсов, I/O операций
5. **🔋 Батарея**: Мониторинг заряда и времени работы от батареи
6. **📝 Логирование**: Подробные логи для каждого бота и системных событий

### Рекомендации
1. Используйте `screen` для фоновой работы
2. Регулярно проверяйте логи
3. Настройте автозапуск
4. Следите за использованием памяти

## 🐛 Решение проблем

### Ошибка "Permission denied"
```bash
chmod +x main_termux.py
```

### Ошибка импорта модулей
```bash
# Переустановите зависимости
pip install --force-reinstall -r requirements_termux.txt
```

### Бот не отвечает
```bash
# Проверьте токен в config.json
# Проверьте интернет-соединение
# Проверьте логи
tail -f logs/sella_bot_termux.log
```

### Проблемы с памятью
```bash
# Очистка кэша Python
pip cache purge

# Перезапуск Termux
exit
# Откройте Termux заново
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/sella_bot_termux.log`
2. Убедитесь в правильности конфигурации
3. Проверьте интернет-соединение
4. Перезапустите бота

## 🔄 Обновление

```bash
cd ~/sella-bot
git pull
pip install -r requirements_termux.txt
# Перезапустите бота
```

---

**Удачного использования бота "Селла" в Termux! 🚀** 