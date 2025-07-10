#!/usr/bin/env python3
"""
Скрипт настройки бота Селла перед первым запуском
"""

import json
import os

def setup_bot():
    print("🤖 Настройка бота Селла")
    print("=" * 40)
    
    # Загрузка текущей конфигурации
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Файл config.json не найден!")
        return
    
    print("\n📝 Текущие настройки:")
    print(f"Токен бота: {config.get('bot_token', 'НЕ УСТАНОВЛЕН')}")
    print(f"ID администратора: {config.get('admin_ids', [])}")
    
    # Запрос токена
    print("\n🔑 Для работы бота нужен токен Telegram бота.")
    print("1. Найдите @BotFather в Telegram")
    print("2. Отправьте /newbot")
    print("3. Следуйте инструкциям")
    print("4. Скопируйте полученный токен")
    
    token = input("\nВведите токен бота (или нажмите Enter для пропуска): ").strip()
    
    if token and token != "YOUR_BOT_TOKEN":
        config['bot_token'] = token
        print("✅ Токен обновлен!")
    else:
        print("⚠️ Токен не изменен. Бот не сможет работать без валидного токена!")
    
    # Запрос ID администратора
    print("\n👤 Для получения вашего Telegram ID:")
    print("1. Найдите @userinfobot в Telegram")
    print("2. Отправьте любое сообщение")
    print("3. Скопируйте ваш ID")
    
    admin_id = input("\nВведите ваш Telegram ID (или нажмите Enter для пропуска): ").strip()
    
    if admin_id and admin_id.isdigit():
        config['admin_ids'] = [int(admin_id)]
        print("✅ ID администратора обновлен!")
    else:
        print("⚠️ ID администратора не изменен.")
    
    # Сохранение конфигурации
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("\n✅ Конфигурация сохранена!")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return
    
    # Проверка готовности
    print("\n🔍 Проверка готовности:")
    
    if config.get('bot_token') and config['bot_token'] != "YOUR_BOT_TOKEN":
        print("✅ Токен бота настроен")
    else:
        print("❌ Токен бота НЕ настроен")
    
    if config.get('admin_ids'):
        print("✅ ID администратора настроен")
    else:
        print("❌ ID администратора НЕ настроен")
    
    print("\n📋 Следующие шаги:")
    print("1. Убедитесь, что токен и ID настроены")
    print("2. Запустите бота: python main.py")
    print("3. Найдите вашего бота в Telegram и отправьте /start")
    
    if config.get('bot_token') and config['bot_token'] != "YOUR_BOT_TOKEN" and config.get('admin_ids'):
        print("\n🎉 Бот готов к запуску!")
    else:
        print("\n⚠️ Настройте токен и ID перед запуском!")

if __name__ == "__main__":
    setup_bot() 