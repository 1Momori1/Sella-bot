# ⚡ СУПЕР ПРОСТОЙ ЗАПУСК БОТА СЕЛЛА

## 🚀 ОДНА КОМАНДА ДЛЯ ВСЕГО!

### Откройте Termux и выполните:

```bash
curl -s https://raw.githubusercontent.com/1Momori1/Sella-bot/master/install.sh | bash
```

**ВСЁ!** Скрипт сам:
- ✅ Скачает автоустановщик
- ✅ Определит что нужно установить
- ✅ Установит все зависимости
- ✅ Настроит систему
- ✅ Запустит бота

---

## 📋 Что произойдет автоматически:

1. **🔍 Диагностика системы** - определение архитектуры и версий
2. **📦 Установка пакетов** - Python, pip, git и другие
3. **🐍 Настройка Python** - виртуальное окружение
4. **📚 Установка модулей** - telegram-bot, psutil и другие
5. **📁 Создание папок** - logs, storage, backups
6. **⚙️ Настройка конфига** - создание config.json
7. **🤖 Запуск бота** - автоматический старт

---

## ⚙️ Если потребуется настройка:

Если скрипт остановится на настройке конфигурации:

```bash
nano config.json
```

Замените:
- `"ВАШ_ТОКЕН_ЗДЕСЬ"` → токен от @BotFather
- `[ВАШ_TELEGRAM_ID]` → ваш ID от @userinfobot

Затем запустите:
```bash
./auto_install.sh
```

---

## 🛠️ Дополнительные команды:

```bash
# Диагностика проблем
./auto_install.sh diagnose

# Очистка временных файлов
./auto_install.sh clean

# Проверка готовности
./auto_install.sh check

# Справка
./auto_install.sh help
```

---

## 🔧 Альтернативные способы:

### Если curl не работает:
```bash
wget -O - https://raw.githubusercontent.com/1Momori1/Sella-bot/master/install.sh | bash
```

### Если прямая загрузка не работает:
```bash
# Клонирование
git clone https://github.com/1Momori1/Sella-bot.git
cd Sella-bot

# Запуск автоустановщика
chmod +x auto_install.sh
./auto_install.sh
```

---

## ✅ После запуска:

1. **Найдите бота в Telegram** по username
2. **Отправьте `/start`**
3. **Проверьте все функции** в меню

**🎉 Бот работает!**

---

## 🚨 Решение проблем:

### Если скрипт не запускается:
```bash
# Проверка прав
ls -la auto_install.sh

# Установка прав
chmod +x auto_install.sh

# Запуск с отладкой
bash -x auto_install.sh
```

### Если есть ошибки:
```bash
# Диагностика
./auto_install.sh diagnose

# Очистка и переустановка
./auto_install.sh clean
./auto_install.sh
```

---

## 📞 Поддержка:

- **Логи:** `tail -f logs/sella_bot.log`
- **Управление:** `Ctrl+C` для остановки
- **Перезапуск:** `./auto_install.sh`

---

**🎯 Цель достигнута: ОДНА КОМАНДА ДЛЯ ВСЕГО!**

**Репозиторий:** https://github.com/1Momori1/Sella-bot.git 