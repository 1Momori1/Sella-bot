# ⚡ Запуск бота Селла ОДНОЙ КОМАНДОЙ

## 🚀 Быстрый старт

### 1️⃣ Откройте Termux и выполните:

```bash
curl -s https://raw.githubusercontent.com/1Momori1/Sella-bot/master/quick_start.sh | bash
```

**ИЛИ**

```bash
wget -O - https://raw.githubusercontent.com/1Momori1/Sella-bot/master/quick_start.sh | bash
```

---

## 📋 Что произойдет автоматически:

1. ✅ Клонирование репозитория
2. ✅ Установка системных пакетов
3. ✅ Создание виртуального окружения
4. ✅ Установка Python зависимостей
5. ✅ Проверка конфигурации
6. ✅ Запуск бота

---

## ⚙️ Настройка (если потребуется):

Если скрипт остановится на проверке конфигурации:

```bash
cd Sella-bot
nano config.json
```

Замените:
- `"ВАШ_ТОКЕН_ЗДЕСЬ"` → ваш токен от @BotFather
- `[ВАШ_TELEGRAM_ID]` → ваш ID от @userinfobot

Затем запустите снова:
```bash
./start_termux.sh
```

---

## 🔧 Альтернативный способ:

Если прямая загрузка не работает:

```bash
# Клонирование
git clone https://github.com/1Momori1/Sella-bot.git
cd Sella-bot

# Запуск
chmod +x start_termux.sh
./start_termux.sh
```

---

## ✅ Готово!

После успешного запуска:
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Проверьте все функции

**🎉 Бот работает в Termux!**

---

## 🛠️ Управление:

- **Остановка:** `Ctrl+C`
- **Перезапуск:** `./start_termux.sh`
- **Логи:** `tail -f logs/sella_bot.log`

---

**Репозиторий:** https://github.com/1Momori1/Sella-bot.git 