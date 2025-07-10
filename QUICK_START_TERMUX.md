# 🚀 Быстрый запуск бота "Селла" в Termux

## ⚡ Быстрая установка (5 минут)

### 1. Установка Termux
```bash
# Скачайте с F-Droid: https://f-droid.org/packages/com.termux/
```

### 2. Обновление и установка Python
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### 3. Клонирование проекта
```bash
cd ~
git clone https://github.com/your-username/sella-bot.git
cd sella-bot
```

### 4. Установка зависимостей
```bash
pip install -r requirements_termux.txt
```

### 5. Настройка бота
```bash
# Скопируйте конфигурацию
cp config.example.json config.json

# Отредактируйте токен бота
nano config.json
# Замените "YOUR_BOT_TOKEN" на ваш токен от @BotFather
# Замените admin_ids на ваш Telegram ID
```

### 6. Создание папок
```bash
mkdir -p storage logs
```

### 7. Тестирование
```bash
python test_termux.py
```

### 8. Запуск
```bash
python main_termux.py
```

## 🔧 Управление ботом

### Запуск в фоне
```bash
# Установка screen
pkg install screen -y

# Запуск в фоне
screen -dmS sella-bot python main_termux.py

# Подключение к сессии
screen -r sella-bot

# Отключение (бот продолжит работать)
# Ctrl+A, затем D
```

### Остановка
```bash
# Найти процесс
ps aux | grep main_termux.py

# Остановить
kill -9 PID_NUMBER

# Или через screen
screen -X -S sella-bot quit
```

### Проверка логов
```bash
tail -f logs/sella_bot_termux.log
```

## 📱 Использование

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Используйте кнопки для навигации
4. Основные команды:
   - `/status` - статус системы
   - `/storage` - файловое хранилище
   - `/help` - справка

## ✅ Преимущества Termux-версии

- 🌡️ **Расширенный мониторинг температуры** - множественные методы получения
- 🔧 **Полное управление процессами** - запуск, остановка, перезапуск, логирование
- 💾 **Детальная системная информация** - CPU, RAM, диск, сеть, батарея
- 📊 **Продвинутая статистика** - процессы, сетевые интерфейсы, I/O операции
- 🔋 **Мониторинг батареи** - заряд, время работы, статус подключения
- 📝 **Подробное логирование** - логи для каждого бота и системных событий

## ⚠️ Важно

- Используйте Termux из F-Droid, не из Google Play
- Убедитесь, что у вас есть токен бота от @BotFather
- Бот работает только при активном интернет-соединении
- Для автозапуска настройте скрипт в `~/.bashrc`

## 🆘 Если что-то не работает

1. Проверьте логи: `tail -f logs/sella_bot_termux.log`
2. Убедитесь в правильности токена в `config.json`
3. Проверьте интернет-соединение
4. Перезапустите бота

---

**Готово! Ваш бот "Селла" работает в Termux! 🎉** 