# ⚡ Быстрый запуск бота Селла в Termux

## 🚀 Команды для копирования

### 1️⃣ Установка и настройка
```bash
# Обновление системы
pkg update -y && pkg upgrade -y

# Установка пакетов
pkg install python python-pip git -y

# Клонирование проекта
git clone https://github.com/1Momori1/Sella-bot.git
cd Sella-bot

# Автоматическая установка
chmod +x start_termux.sh
./start_termux.sh
```

### 2️⃣ Настройка конфигурации
```bash
# Открыть конфигурацию
nano config.json
```

Замените в `config.json`:
- `"ВАШ_ТОКЕН_ЗДЕСЬ"` → ваш токен от @BotFather
- `[ВАШ_TELEGRAM_ID]` → ваш ID от @userinfobot

### 3️⃣ Запуск бота
```bash
# Способ 1: Автоматический
./start_termux.sh

# Способ 2: Ручной
source venv/bin/activate
python main.py

# Способ 3: В фоне
nohup python main.py > bot.log 2>&1 &
```

## 🔧 Управление

### Проверка работы
```bash
# Логи
tail -f logs/sella_bot.log

# Процессы
ps aux | grep python
```

### Перезапуск
```bash
pkill -f "python main.py" && python main.py
```

### Остановка
```bash
pkill -f "python main.py"
```

## 📱 Автозапуск
```bash
# Установка cronie
pkg install cronie -y

# Настройка автозапуска
crontab -e
# Добавить: @reboot cd /data/data/com.termux/files/home/Sella-bot && ./start_termux.sh
```

## 🛠️ Решение проблем

### Ошибки модулей
```bash
source venv/bin/activate
pip install -r requirements_termux.txt
```

### Права доступа
```bash
chmod +x start_termux.sh
chmod +x *.py
```

### Бот не отвечает
```bash
# Проверить токен
cat config.json

# Перезапустить
pkill -f "python main.py" && python main.py
```

## ✅ Проверка

1. Запустите бота
2. Найдите в Telegram по username
3. Отправьте `/start`
4. Проверьте все меню

**🎉 Готово! Бот работает в Termux!**

---
**Подробная инструкция:** `TERMUX_LAUNCH_GUIDE.md`
**Репозиторий:** https://github.com/1Momori1/Sella-bot.git 