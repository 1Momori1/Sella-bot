# 📦 Установка зависимостей

## Быстрая установка

```bash
# Установка всех зависимостей
pip install -r requirements.txt

# Или установка по частям
pip install python-telegram-bot==20.7
pip install psutil==5.9.6
pip install aiofiles==23.2.1
pip install aiohttp==3.9.1
pip install matplotlib==3.8.2
pip install pyjwt==2.8.0
```

## Для Termux (Android)

```bash
# Обновление пакетов
pkg update && pkg upgrade

# Установка Python и pip
pkg install python

# Установка зависимостей
pip install -r requirements_termux.txt
```

## Проверка установки

```bash
# Тест основных модулей
python test_bot.py

# Тест новых возможностей
python test_new_features.py

# Тест для Termux
python test_termux_advanced.py
```

## Возможные проблемы

### Ошибка "Microsoft Visual C++ 14.0 is required"
- Установите Visual Studio Build Tools
- Или используйте предкомпилированные пакеты

### Ошибка "Permission denied"
```bash
# Windows
pip install --user -r requirements.txt

# Linux/Mac
sudo pip install -r requirements.txt
```

### Проблемы с matplotlib в Termux
```bash
# Установка дополнительных пакетов
pkg install libcairo-dev pkg-config
pip install matplotlib --no-cache-dir
``` 