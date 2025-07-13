# 🚀 Руководство по запуску бота Селла в Termux

## 📋 Быстрый старт

### 1️⃣ Установка Termux
```bash
# Скачайте Termux с F-Droid (НЕ из Google Play!)
# Установите и откройте приложение
```

### 2️⃣ Обновление системы
```bash
pkg update -y && pkg upgrade -y
```

### 3️⃣ Установка необходимых пакетов
```bash
pkg install python python-pip git -y
```

### 4️⃣ Клонирование проекта
```bash
git clone https://github.com/1Momori1/Sella-bot.git
cd Sella-bot
```

### 5️⃣ Автоматическая установка
```bash
chmod +x start_termux.sh
./start_termux.sh
```

---

## ⚙️ Настройка бота

### 1️⃣ Настройка конфигурации
Откройте файл `config.json` и измените:

```json
{
  "bot_token": "ВАШ_ТОКЕН_ЗДЕСЬ",
  "admin_ids": [ВАШ_TELEGRAM_ID],
  "termux_mode": true
}
```

### 2️⃣ Получение токена бота
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

### 3️⃣ Получение вашего Telegram ID
1. Найдите @userinfobot в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш ID

---

## 🚀 Запуск бота

### Способ 1: Автоматический запуск
```bash
./start_termux.sh
```

### Способ 2: Ручной запуск
```bash
# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей (если нужно)
pip install -r requirements_termux.txt

# Запуск бота
python main.py
```

### Способ 3: Запуск в фоне
```bash
# Запуск в фоновом режиме
nohup python main.py > bot.log 2>&1 &

# Проверка работы
tail -f bot.log
```

---

## 🔧 Управление ботом

### Проверка статуса
```bash
# Проверка процессов Python
ps aux | grep python

# Проверка логов
tail -f logs/sella_bot.log
```

### Остановка бота
```bash
# Найти PID процесса
ps aux | grep python

# Остановить процесс
kill -9 <PID>
```

### Перезапуск бота
```bash
# Остановить текущий процесс
pkill -f "python main.py"

# Запустить заново
python main.py
```

---

## 📱 Автозапуск при перезагрузке

### Установка cronie
```bash
pkg install cronie -y
```

### Настройка автозапуска
```bash
# Открыть crontab
crontab -e

# Добавить строку (замените путь на ваш)
@reboot cd /data/data/com.termux/files/home/Sella-bot && ./start_termux.sh
```

### Альтернативный способ (через .bashrc)
```bash
# Открыть .bashrc
nano ~/.bashrc

# Добавить в конец файла
cd /data/data/com.termux/files/home/Sella-bot && ./start_termux.sh &

# Сохранить и перезагрузить
source ~/.bashrc
```

---

## 🛠️ Устранение проблем

### Ошибка "Module not found"
```bash
source venv/bin/activate
pip install -r requirements_termux.txt
```

### Ошибка "Permission denied"
```bash
chmod +x start_termux.sh
chmod +x *.py
```

### Бот не отвечает
```bash
# Проверить токен
cat config.json

# Проверить логи
tail -f logs/sella_bot.log

# Перезапустить
pkill -f "python main.py" && python main.py
```

### Проблемы с памятью
```bash
# Очистка кэша
pkg clean
rm -rf ~/.cache/pip

# Проверка свободного места
df -h
```

---

## 📊 Мониторинг

### Проверка ресурсов
```bash
# Использование CPU и памяти
top

# Свободное место на диске
df -h

# Сетевые соединения
netstat -tuln
```

### Просмотр логов
```bash
# Последние строки лога
tail -f logs/sella_bot.log

# Поиск ошибок
grep "ERROR" logs/sella_bot.log

# Очистка логов
> logs/sella_bot.log
```

---

## 🔒 Безопасность

### Резервное копирование
```bash
# Создание бэкапа
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz storage/ logs/ config.json

# Восстановление бэкапа
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
```

### Обновление бота
```bash
# Сохранение изменений
git add .
git commit -m "Локальные изменения"

# Получение обновлений
git pull origin master

# Перезапуск
pkill -f "python main.py" && python main.py
```

---

## 📞 Полезные команды

### Основные команды бота
- `/start` - запуск бота
- `/help` - справка
- `/menu` - главное меню
- `/status` - статус системы

### Команды Termux
```bash
# Обновление системы
pkg update -y && pkg upgrade -y

# Установка пакета
pkg install <пакет> -y

# Поиск пакета
pkg search <пакет>

# Удаление пакета
pkg remove <пакет> -y
```

---

## 🎯 Проверка работы

### 1️⃣ Запустите бота
```bash
python main.py
```

### 2️⃣ Найдите бота в Telegram
- Откройте Telegram
- Найдите вашего бота по username
- Нажмите "Start"

### 3️⃣ Проверьте функции
- Откройте главное меню
- Проверьте все разделы
- Убедитесь, что кнопки работают

### 4️⃣ Проверьте логи
```bash
tail -f logs/sella_bot.log
```

---

## ✅ Готово!

Если все работает корректно, вы увидите:
- ✅ Бот отвечает на команды
- ✅ Все меню открываются
- ✅ Функции работают
- ✅ Логи записываются

**🎉 Поздравляем! Ваш бот Селла успешно запущен в Termux!**

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f logs/sella_bot.log`
2. Убедитесь в правильности токена
3. Проверьте интернет соединение
4. Перезапустите бота

**Ссылка на репозиторий:** https://github.com/1Momori1/Sella-bot.git 