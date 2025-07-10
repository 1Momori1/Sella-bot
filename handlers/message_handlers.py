from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

class MessageHandlers:
    """Обработчики текстовых сообщений и файлов"""
    
    def __init__(self, role_manager, cloud_storage, notification_manager):
        self.role_manager = role_manager
        self.cloud_storage = cloud_storage
        self.notification_manager = notification_manager
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной обработчик сообщений"""
        if not update.message or not update.message.from_user:
            return
        
        user_id = update.message.from_user.id
        message_text = update.message.text or ""
        
        try:
            # Обработка команд
            if message_text.startswith('/'):
                await self.handle_command(update, context, user_id, message_text)
            else:
                await self.handle_text_message(update, context, user_id, message_text)
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке сообщения")
    
    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик файлов для загрузки в хранилище"""
        if not update.message or not update.message.from_user:
            return
        
        user_id = update.message.from_user.id
        
        try:
            # Проверяем права на загрузку
            if not await self.role_manager.check_permission(user_id, "storage", "upload"):
                await update.message.reply_text("❌ У вас нет прав для загрузки файлов")
                return
            
            # Получаем информацию о файле
            file_info = None
            original_filename = ""
            
            if update.message.document:
                file_info = update.message.document
                original_filename = file_info.file_name or "document"
            elif update.message.photo:
                file_info = update.message.photo[-1]  # Берем самое большое фото
                original_filename = f"photo_{file_info.file_id}.jpg"
            elif update.message.video:
                file_info = update.message.video
                original_filename = file_info.file_name or f"video_{file_info.file_id}.mp4"
            elif update.message.audio:
                file_info = update.message.audio
                original_filename = file_info.file_name or f"audio_{file_info.file_id}.mp3"
            elif update.message.voice:
                file_info = update.message.voice
                original_filename = f"voice_{file_info.file_id}.ogg"
            else:
                await update.message.reply_text("❌ Неподдерживаемый тип файла")
                return
            
            # Скачиваем файл во временную папку
            await update.message.reply_text("📥 Загружаю файл...")
            
            temp_file = await context.bot.get_file(file_info.file_id)
            temp_path = os.path.join(tempfile.gettempdir(), f"temp_{file_info.file_id}")
            
            await temp_file.download_to_drive(temp_path)
            
            # Сохраняем в хранилище
            result = await self.cloud_storage.save_file(user_id, temp_path, original_filename)
            
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if result["success"]:
                file_info = result["file_info"]
                message = f"✅ **Файл успешно загружен!**\n\n"
                message += f"📄 **Имя:** {file_info['original_name']}\n"
                message += f"📏 **Размер:** {file_info['size_formatted']}\n"
                message += f"📁 **Тип:** {file_info['extension']}\n"
                message += f"📅 **Загружен:** {file_info['upload_time'][:19]}\n\n"
                message += f"💾 Файл сохранен в вашем облачном хранилище"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
                # Отправляем уведомление
                await self.notification_manager.send_notification(
                    user_id, 
                    "file_uploaded", 
                    f"Файл {file_info['original_name']} успешно загружен"
                )
            else:
                await update.message.reply_text(f"❌ **Ошибка загрузки:** {result['message']}", parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке файла")
    
    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, command: str):
        """Обработка команд"""
        try:
            if command == "/start":
                await self.handle_start_command(update, context, user_id)
            elif command == "/help":
                await self.handle_help_command(update, context, user_id)
            elif command == "/menu":
                await self.handle_menu_command(update, context, user_id)
            else:
                await update.message.reply_text("❓ Неизвестная команда. Используйте /help для справки")
                
        except Exception as e:
            logger.error(f"Ошибка обработки команды {command}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при выполнении команды")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message_text: str):
        """Обработка текстовых сообщений"""
        try:
            # Проверяем, не является ли это поисковым запросом для хранилища
            if message_text.startswith("🔍") or message_text.startswith("поиск"):
                await self.handle_storage_search(update, context, user_id, message_text)
            else:
                # Обычное текстовое сообщение
                await update.message.reply_text(
                    "💬 Используйте меню для навигации или отправьте файл для загрузки в хранилище"
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки текстового сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке сообщения")
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обработка команды /start"""
        try:
            welcome_message = """🤖 **Добро пожаловать в Селла!**

Я универсальный бот для управления серверами и облачными ресурсами.

**Основные возможности:**
🖥️ Мониторинг системы (с автообновлением)
⛏️ Управление сервером
☁️ Облачное хранилище файлов
👑 Админ-панель
⚠️ Система уведомлений

**Как использовать:**
• Отправьте файл для загрузки в хранилище
• Используйте /menu для доступа к функциям
• Используйте /help для справки

Начните работу прямо сейчас! 🚀"""

            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды start: {e}")
            await update.message.reply_text("❌ Произошла ошибка при запуске")
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обработка команды /help"""
        try:
            help_message = """📚 **Справка по использованию Селла**

**Команды:**
/start - Запуск бота
/help - Эта справка
/menu - Главное меню

**Разделы:**
🖥️ **Система** - мониторинг и настройки
⛏️ **Сервер** - управление серверными процессами
☁️ **Хранилище** - загрузка и управление файлами
👑 **Админка** - управление пользователями и правами

**Загрузка файлов:**
Просто отправьте любой файл боту, и он будет сохранен в вашем облачном хранилище.

**Мониторинг:**
В разделе "Система" доступен динамический мониторинг с автообновлением каждые 2 секунды.

**Поддержка:**
При возникновении проблем обратитесь к администратору."""

            await update.message.reply_text(help_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды help: {e}")
            await update.message.reply_text("❌ Произошла ошибка при показе справки")
    
    async def handle_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обработка команды /menu"""
        try:
            # Получаем меню пользователя
            user_menu = await self.role_manager.get_user_menu(user_id)
            user_info = await self.role_manager.get_user_info(user_id)
            user_name = user_info["name"] if user_info else "Гость"
            user_role = user_info["role"] if user_info else "guest"
            
            # Создаем главное меню
            from handlers.menu_buttons import MenuButtons
            keyboard = await MenuButtons.create_main_menu(user_menu)
            
            message_text = f"""🤖 **Селла - Главное меню**

👤 **Пользователь:** {user_name} ({user_role})

Выберите раздел для управления:"""
            
            await update.message.reply_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки команды menu: {e}")
            await update.message.reply_text("❌ Произошла ошибка при показе меню")
    
    async def handle_storage_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message_text: str):
        """Обработка поиска в хранилище"""
        try:
            # Проверяем права на поиск
            if not await self.role_manager.check_permission(user_id, "storage", "view"):
                await update.message.reply_text("❌ У вас нет прав для поиска файлов")
                return
            
            # Извлекаем поисковый запрос
            query = message_text.replace("🔍", "").replace("поиск", "").strip()
            if not query:
                await update.message.reply_text("❌ Укажите что искать. Например: 🔍 документ")
                return
            
            # Выполняем поиск
            is_admin = await self.role_manager.is_admin(user_id)
            files = await self.cloud_storage.search_files(user_id, query, is_admin)
            
            if not files:
                await update.message.reply_text(f"🔍 По запросу '{query}' ничего не найдено")
                return
            
            # Формируем результат поиска
            result_message = f"🔍 **Результаты поиска: '{query}'**\n\n"
            
            for i, file_info in enumerate(files[:10], 1):  # Показываем первые 10
                result_message += f"{i}. 📄 **{file_info['original_name']}**\n"
                result_message += f"   📏 {file_info['size_formatted']} | 📅 {file_info['upload_time'][:19]}\n\n"
            
            if len(files) > 10:
                result_message += f"... и еще {len(files) - 10} файлов"
            
            await update.message.reply_text(result_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка поиска в хранилище: {e}")
            await update.message.reply_text("❌ Произошла ошибка при поиске файлов") 