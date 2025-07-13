from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class CallbackHandlers:
    """Обработчики callback-запросов для интерактивных кнопок"""
    
    def __init__(self, role_manager, system_monitor, process_manager, cloud_storage, notification_manager, analytics=None):
        self.role_manager = role_manager
        self.system_monitor = system_monitor
        self.process_manager = process_manager
        self.cloud_storage = cloud_storage
        self.notification_manager = notification_manager
        self.analytics = analytics
        # Словарь для отслеживания активных мониторингов
        self.active_monitors = {}
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной обработчик callback-запросов"""
        query = update.callback_query
        if not query or not query.from_user or not query.data:
            return
        
        user_id = query.from_user.id
        callback_data = query.data
        
        try:
            # Обработка различных типов callback
            if callback_data == "main_menu":
                await self.show_main_menu(update, context, user_id)
            # Разделы
            elif callback_data == "section_system":
                await self.show_system_section(update, context, user_id)
            elif callback_data == "section_server":
                await self.show_server_section(update, context, user_id)
            elif callback_data == "section_storage":
                await self.show_storage_section(update, context, user_id)
            elif callback_data == "section_admin":
                await self.show_admin_section(update, context, user_id)
            # Система
            elif callback_data == "system_monitor":
                await self.start_system_monitor(update, context, user_id)
            elif callback_data == "system_monitor_stop":
                await self.stop_system_monitor(update, context, user_id)
            elif callback_data == "system_settings":
                await self.show_system_settings(update, context, user_id)
            elif callback_data == "notifications_settings":
                await self.show_notifications_settings(update, context, user_id)
            # Аналитика
            elif callback_data == "analytics_dashboard":
                await self.show_analytics_dashboard(update, context, user_id)
            elif callback_data == "analytics_summary":
                await self.create_system_summary(update, context, user_id)
            elif callback_data == "analytics_bot_events":
                await self.show_bot_events(update, context, user_id)
            elif callback_data == "analytics_users":
                await self.show_user_activity(update, context, user_id)
            elif callback_data == "analytics_full_report":
                await self.show_full_report(update, context, user_id)
            # Сервер
            elif callback_data == "server_status":
                await self.show_server_status(update, context, user_id)
            elif callback_data == "server_restart":
                await self.restart_bot(update, context, user_id)
            elif callback_data == "server_restart_confirm":
                await self.confirm_restart(update, context, user_id)
            elif callback_data == "server_processes":
                await self.show_processes(update, context, user_id)
            elif callback_data == "server_backup":
                await self.create_backup(update, context, user_id)
            elif callback_data.startswith("backup_download_"):
                backup_name = callback_data.replace("backup_download_", "")
                await self.download_backup(update, context, user_id, backup_name)
            elif callback_data.startswith("backup_delete_"):
                backup_name = callback_data.replace("backup_delete_", "")
                await self.delete_backup(update, context, user_id, backup_name)
            # Хранилище
            elif callback_data == "storage_list":
                await self.show_storage_list(update, context, user_id)
            elif callback_data == "storage_upload":
                await self.show_storage_upload(update, context, user_id)
            elif callback_data == "storage_download":
                await self.show_storage_download(update, context, user_id)
            elif callback_data == "storage_delete":
                await self.show_storage_delete(update, context, user_id)
            elif callback_data == "storage_search":
                await self.show_storage_search(update, context, user_id)
            elif callback_data == "storage_refresh":
                await self.show_storage_list(update, context, user_id)
            # Админка
            elif callback_data == "admin_users":
                await self.show_admin_users(update, context, user_id)
            elif callback_data == "admin_add_user":
                await self.add_user(update, context, user_id)
            elif callback_data == "admin_add_user_id":
                await self.show_add_user_form(update, context, user_id)
            elif callback_data.startswith("admin_role_"):
                await self.set_user_role(update, context, user_id)
            elif callback_data == "admin_delete_user":
                await self.delete_user(update, context, user_id)
            elif callback_data.startswith("admin_delete_confirm_"):
                await self.confirm_delete_user(update, context, user_id)
            elif callback_data.startswith("admin_delete_final_"):
                await self.final_delete_user(update, context, user_id)
            elif callback_data == "admin_permissions":
                await self.show_admin_permissions(update, context, user_id)
            elif callback_data == "admin_logs":
                await self.show_logs(update, context, user_id)
            elif callback_data == "admin_full_log":
                await self.show_full_log(update, context, user_id)
            elif callback_data == "admin_config":
                await self.show_admin_config(update, context, user_id)
            # Общие
            elif callback_data == "refresh":
                await self.refresh_current_menu(update, context, user_id)
            elif callback_data == "close":
                await self.close_menu(update, context)
            elif callback_data == "no_action":
                await query.answer()  # Просто убираем часы загрузки
            elif callback_data == "cancel":
                await self.show_main_menu(update, context, user_id)
            elif callback_data == "help":
                await self.show_help(update, context, user_id)
            elif callback_data == "help_setup_guide":
                await self.show_setup_guide(update, context, user_id)
            elif callback_data == "help_troubleshooting":
                await self.show_troubleshooting(update, context, user_id)
            # Детальная информация
            elif callback_data.startswith("file_info_"):
                file_id = callback_data.replace("file_info_", "")
                await self.show_file_info(update, context, user_id, file_id)
            elif callback_data.startswith("file_download_"):
                file_id = callback_data.replace("file_download_", "")
                await self.download_file(update, context, user_id, file_id)
            elif callback_data.startswith("file_delete_"):
                file_id = callback_data.replace("file_delete_", "")
                await self.delete_file(update, context, user_id, file_id)
            elif callback_data.startswith("confirm_"):
                await self.handle_confirmation(update, context, user_id, callback_data)
            else:
                await query.answer("Функция в разработке")
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback {callback_data}: {e}")
            await query.answer("Произошла ошибка")
    
    async def start_system_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Запустить динамический мониторинг системы"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            await query.answer("❌ Нет доступа к системной информации")
            return
        
        # Останавливаем предыдущий мониторинг если есть
        await self.stop_system_monitor(update, context, user_id)
        
        # Создаем кнопки управления мониторингом
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Остановить мониторинг", callback_data="system_monitor_stop")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_system")]
        ])
        
        # Показываем начальный статус
        system_status = await self.system_monitor.get_system_status(user_id)
        await query.edit_message_text(
            text=f"{system_status}\n\n🔄 **Автообновление каждые 2 секунды**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # Запускаем фоновую задачу мониторинга
        self.active_monitors[user_id] = True
        asyncio.create_task(self.monitor_system_loop(update, context, user_id))
        
        await query.answer("🔄 Мониторинг запущен")
    
    async def stop_system_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Остановить динамический мониторинг системы"""
        # Останавливаем мониторинг
        self.active_monitors[user_id] = False
        
        # Показываем финальный статус
        query = update.callback_query
        system_status = await self.system_monitor.get_system_status(user_id)
        
        # Создаем кнопки для перезапуска
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Запустить мониторинг", callback_data="system_monitor")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_system")]
        ])
        
        await query.edit_message_text(
            text=f"{system_status}\n\n⏹️ **Мониторинг остановлен**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        await query.answer("⏹️ Мониторинг остановлен")
    
    async def monitor_system_loop(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Цикл автообновления мониторинга системы"""
        query = update.callback_query
        
        while self.active_monitors.get(user_id, False):
            try:
                # Получаем новый статус
                system_status = await self.system_monitor.get_system_status(user_id)
                
                # Создаем кнопки управления мониторингом
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏹️ Остановить мониторинг", callback_data="system_monitor_stop")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="section_system")]
                ])
                
                # Обновляем сообщение
                await query.edit_message_text(
                    text=f"{system_status}\n\n🔄 **Автообновление каждые 2 секунды**",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                # Ждем 2 секунды
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга для пользователя {user_id}: {e}")
                break
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать главное меню"""
        query = update.callback_query
        
        # Останавливаем мониторинг при выходе из раздела
        if user_id in self.active_monitors:
            self.active_monitors[user_id] = False
        
        # Получение прав пользователя
        user_menu = await self.role_manager.get_user_menu(user_id)
        user_info = await self.role_manager.get_user_info(user_id)
        user_name = user_info["name"] if user_info else "Гость"
        user_role = user_info["role"] if user_info else "guest"
        
        # Создание меню
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_main_menu(user_menu)
        
        message_text = f"""🤖 **Селла - Главное меню**

👤 **Пользователь:** {user_name} ({user_role})

Выберите раздел для управления:"""
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    # Разделы
    async def show_system_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать раздел системы"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            await query.answer("❌ Нет доступа к системной информации")
            return
        
        user_menu = await self.role_manager.get_user_menu(user_id)
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_system_menu(user_menu)
        
        message_text = """🖥️ **Раздел: Система**

Выберите действие:"""
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_server_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать раздел сервера"""
        query = update.callback_query
        
        # Останавливаем мониторинг при переходе в другой раздел
        if user_id in self.active_monitors:
            self.active_monitors[user_id] = False
        
        if not await self.role_manager.check_permission(user_id, "server", "view"):
            await query.answer("❌ Нет доступа к серверу")
            return
        
        user_menu = await self.role_manager.get_user_menu(user_id)
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_server_menu(user_menu)
        
        message_text = """⛏️ **Раздел: Сервер**

Выберите действие:"""
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать раздел хранилища"""
        query = update.callback_query
        
        # Останавливаем мониторинг при переходе в другой раздел
        if user_id in self.active_monitors:
            self.active_monitors[user_id] = False
        
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            await query.answer("❌ Нет доступа к хранилищу")
            return
        
        user_menu = await self.role_manager.get_user_menu(user_id)
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_storage_menu(user_menu)
        
        message_text = """☁️ **Раздел: Хранилище**

Выберите действие:"""
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_admin_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать админский раздел"""
        query = update.callback_query
        
        # Останавливаем мониторинг при переходе в другой раздел
        if user_id in self.active_monitors:
            self.active_monitors[user_id] = False
        
        if not await self.role_manager.is_admin(user_id):
            await query.answer("❌ Только для администраторов")
            return
        
        user_menu = await self.role_manager.get_user_menu(user_id)
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_admin_menu(user_menu)
        
        message_text = """👑 **Раздел: Админка**

Выберите действие:"""
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать список файлов в хранилище"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            await query.answer("❌ Нет доступа к хранилищу")
            return
        
        # Получаем список файлов
        is_admin = await self.role_manager.is_admin(user_id)
        files = await self.cloud_storage.list_files(user_id, is_admin)
        storage_usage = await self.cloud_storage.get_storage_usage(user_id)
        
        if not files:
            message_text = "☁️ **Облачное хранилище**\n\n📁 Файлы не найдены."
        else:
            message_text = "☁️ **Облачное хранилище**\n\n"
            if storage_usage:
                message_text += f"📊 **Статистика:**\n"
                message_text += f"   Файлов: {storage_usage['total_files']}\n"
                message_text += f"   Размер: {storage_usage['total_size_formatted']} / {storage_usage['max_size_formatted']}\n"
                message_text += f"   Использовано: {storage_usage['usage_percent']:.1f}%\n\n"
            
            message_text += "📁 **Ваши файлы:**\n"
            for file_info in files[:10]:  # Показываем первые 10
                message_text += f"📄 {file_info['original_name']} ({file_info['size_formatted']})\n"
            
            if len(files) > 10:
                message_text += f"\n... и еще {len(files) - 10} файлов"
        
        # Создание меню файлов
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_storage_files_menu(files)
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать инструкции по загрузке файлов"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            await query.answer("❌ Нет прав для загрузки файлов")
            return
        
        message_text = """📤 **Загрузка файлов**

Чтобы загрузить файл в облачное хранилище:

1. **Отправьте файл** боту (документ, фото, видео, аудио)
2. **Файл автоматически** сохранится в вашем хранилище
3. **Получите уведомление** об успешной загрузке

**Поддерживаемые типы:**
📄 Документы (PDF, DOC, TXT и др.)
🖼️ Фотографии (JPG, PNG, GIF)
🎥 Видео (MP4, AVI, MOV)
🎵 Аудио (MP3, WAV, OGG)
🎤 Голосовые сообщения

**Ограничения:**
📏 Максимальный размер файла: 50MB
💾 Общий лимит хранилища: 1GB

**Запрещенные файлы:**
❌ Исполняемые файлы (.exe, .bat, .cmd)
❌ Скрипты (.vbs, .js, .com)"""
        
        # Создание кнопок
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Список файлов", callback_data="storage_list")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_storage")]
        ])
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать список файлов для скачивания"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "download"):
            await query.answer("❌ Нет прав для скачивания файлов")
            return
        
        # Получаем список файлов
        is_admin = await self.role_manager.is_admin(user_id)
        files = await self.cloud_storage.list_files(user_id, is_admin)
        
        if not files:
            message_text = "📥 **Скачивание файлов**\n\n📁 У вас нет файлов для скачивания."
        else:
            message_text = "📥 **Скачивание файлов**\n\n"
            message_text += "Выберите файл для скачивания:\n\n"
            
            for i, file_info in enumerate(files[:10], 1):
                message_text += f"{i}. 📄 **{file_info['original_name']}**\n"
                message_text += f"   📏 {file_info['size_formatted']} | 📅 {file_info['upload_time'][:19]}\n\n"
            
            if len(files) > 10:
                message_text += f"... и еще {len(files) - 10} файлов"
        
        # Создание меню для скачивания
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_storage_download_menu(files)
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать список файлов для удаления"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "delete"):
            await query.answer("❌ Нет прав для удаления файлов")
            return
        
        # Получаем список файлов
        is_admin = await self.role_manager.is_admin(user_id)
        files = await self.cloud_storage.list_files(user_id, is_admin)
        
        if not files:
            message_text = "🗑️ **Удаление файлов**\n\n📁 У вас нет файлов для удаления."
        else:
            message_text = "🗑️ **Удаление файлов**\n\n"
            message_text += "⚠️ **Внимание!** Удаление необратимо.\n\n"
            message_text += "Выберите файл для удаления:\n\n"
            
            for i, file_info in enumerate(files[:10], 1):
                message_text += f"{i}. 📄 **{file_info['original_name']}**\n"
                message_text += f"   📏 {file_info['size_formatted']} | 📅 {file_info['upload_time'][:19]}\n\n"
            
            if len(files) > 10:
                message_text += f"... и еще {len(files) - 10} файлов"
        
        # Создание меню для удаления
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_storage_delete_menu(files)
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_storage_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать интерфейс поиска файлов"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            await query.answer("❌ Нет доступа к хранилищу")
            return
        
        message_text = """🔍 **Поиск файлов**

Для поиска файлов в хранилище:

1. **Отправьте сообщение** с текстом поиска
2. **Используйте формат:** 🔍 название файла
3. **Или просто:** поиск название файла

**Примеры:**
🔍 документ
🔍 фото
поиск отчет
🔍 .pdf

**Результаты поиска** покажут все файлы, содержащие указанный текст в названии."""
        
        # Создание кнопок
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Список файлов", callback_data="storage_list")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_storage")]
        ])
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать список пользователей (админка)"""
        query = update.callback_query
        
        if not await self.role_manager.is_admin(user_id):
            await query.answer("❌ Только для администраторов")
            return
        
        users = await self.role_manager.list_users(user_id)
        
        if not users:
            message_text = "👥 **Пользователи**\n\nСписок пользователей пуст."
        else:
            message_text = "👥 **Пользователи**\n\n"
            for user in users:
                message_text += f"👤 **{user['name']}** (ID: {user['id']})\n"
                message_text += f"   Роль: {user['role']}\n"
                message_text += f"   Создан: {user['created_at']}\n\n"
        
        # Создание админского меню
        from handlers.menu_buttons import MenuButtons
        keyboard = await MenuButtons.create_admin_menu({"admin": ["users"]})
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def show_file_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, file_id: str):
        """Показать информацию о файле"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            await query.answer("❌ Нет доступа к хранилищу")
            return
        
        file_info = await self.cloud_storage.get_file_info(file_id, user_id)
        
        if not file_info:
            await query.answer("❌ Файл не найден")
            return
        
        # Создание меню управления файлом
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = []
        if await self.role_manager.check_permission(user_id, "storage", "download"):
            keyboard_buttons.append(InlineKeyboardButton("📥 Скачать", callback_data=f"file_download_{file_id}"))
        
        if await self.role_manager.check_permission(user_id, "storage", "delete"):
            keyboard_buttons.append(InlineKeyboardButton("🗑️ Удалить", callback_data=f"file_delete_{file_id}"))
        
        keyboard_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data="storage_list"))
        
        keyboard = InlineKeyboardMarkup([keyboard_buttons])
        
        message_text = f"""📄 **Информация о файле**

📛 **Имя:** {file_info['name']}
📏 **Размер:** {file_info['size_formatted']}
📁 **Тип:** {file_info['extension']}
📅 **Загружен:** {file_info['upload_time']}"""

        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, callback_data: str):
        """Обработка подтверждений действий"""
        query = update.callback_query
        
        # Парсинг callback_data
        parts = callback_data.split("_")
        if len(parts) < 2:
            await query.answer("❌ Неверный формат команды")
            return
        
        action = parts[1]
        item_id = parts[2] if len(parts) > 2 else None
        
        if action == "delete" and item_id:
            # Подтверждение удаления файла
            if await self.role_manager.check_permission(user_id, "storage", "delete"):
                result = await self.cloud_storage.delete_file(item_id, user_id)
                if result["success"]:
                    await query.answer("✅ Файл удален")
                    await self.show_storage_list(update, context, user_id)
                else:
                    await query.answer(f"❌ {result['message']}")
            else:
                await query.answer("❌ Нет прав для удаления")
        else:
            await query.answer("Функция в разработке")
    
    async def refresh_current_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обновить текущее меню"""
        query = update.callback_query
        await query.answer("🔄 Обновление...")
        # Здесь можно добавить логику определения текущего меню и его обновления
        await self.show_main_menu(update, context, user_id)
    
    async def close_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Закрыть меню"""
        query = update.callback_query
        
        # Останавливаем все активные мониторинги
        for user_id in list(self.active_monitors.keys()):
            self.active_monitors[user_id] = False
        
        await query.edit_message_text("👋 Меню закрыто")
    
    # Системные настройки
    async def show_system_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать настройки системы"""
        query = update.callback_query
        await query.answer("⚙️ Настройки системы в разработке")
        await self.show_system_section(update, context, user_id)
    
    # Управление сервером
    async def show_server_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать статус сервера"""
        query = update.callback_query
        await query.answer("⛏️ Статус сервера в разработке")
        await self.show_server_section(update, context, user_id)
    
    async def start_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Запустить сервер"""
        query = update.callback_query
        await query.answer("🟢 Запуск сервера в разработке")
        await self.show_server_section(update, context, user_id)
    
    async def stop_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Остановить сервер"""
        query = update.callback_query
        await query.answer("🔴 Остановка сервера в разработке")
        await self.show_server_section(update, context, user_id)
    
    async def create_server_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать бэкап сервера"""
        query = update.callback_query
        await query.answer("💾 Создание бэкапа в разработке")
        await self.show_server_section(update, context, user_id)
    
    # Хранилище
    async def download_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, file_id: str):
        """Скачивание файла"""
        query = update.callback_query
        
        try:
            # Получаем информацию о файле
            file_info = await self.cloud_storage.get_file_info(file_id, user_id)
            if not file_info:
                await query.answer("❌ Файл не найден или нет доступа")
                return
            
            # Проверяем существование файла
            if not os.path.exists(file_info["path"]):
                await query.answer("❌ Файл не найден на диске")
                return
            
            # Отправляем файл пользователю
            await query.answer("📥 Отправляю файл...")
            
            with open(file_info["path"], 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename=file_info["original_name"],
                    caption=f"📄 {file_info['original_name']}\n📏 {file_info['size_formatted']}\n📅 {file_info['upload_time'][:19]}"
                )
            
            await query.answer("✅ Файл отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка скачивания файла: {e}")
            await query.answer("❌ Ошибка при скачивании файла")
    
    async def delete_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, file_id: str):
        """Удаление файла"""
        query = update.callback_query
        
        try:
            # Получаем информацию о файле
            file_info = await self.cloud_storage.get_file_info(file_id, user_id)
            if not file_info:
                await query.answer("❌ Файл не найден или нет доступа")
                return
            
            # Удаляем файл
            result = await self.cloud_storage.delete_file(file_id, user_id)
            
            if result["success"]:
                await query.answer("✅ Файл удален")
                # Обновляем список файлов
                await self.show_storage_list(update, context, user_id)
            else:
                await query.answer(f"❌ {result['message']}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
            await query.answer("❌ Ошибка при удалении файла")
    
    async def handle_file_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, callback_data: str):
        """Обработка действий с файлами"""
        try:
            # Парсим callback_data
            parts = callback_data.split("_")
            if len(parts) < 3:
                await update.callback_query.answer("❌ Неверный формат команды")
                return
            
            action = parts[1]
            file_id = parts[2]
            
            if action == "download":
                await self.download_file(update, context, user_id, file_id)
            elif action == "delete":
                await self.delete_file(update, context, user_id, file_id)
            elif action == "info":
                await self.show_file_info(update, context, user_id, file_id)
            else:
                await update.callback_query.answer("❌ Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Ошибка обработки действия с файлом: {e}")
            await update.callback_query.answer("❌ Произошла ошибка")
    
    # Уведомления
    async def show_notifications_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать настройки уведомлений"""
        query = update.callback_query
        await query.answer("⚠️ Настройки уведомлений в разработке")
        await self.show_system_section(update, context, user_id)
    
    # Админка
    async def show_admin_permissions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать управление правами"""
        query = update.callback_query
        await query.answer("🔐 Управление правами в разработке")
        await self.show_admin_section(update, context, user_id)
    
    async def show_admin_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать логи"""
        query = update.callback_query
        await query.answer("📝 Просмотр логов в разработке")
        await self.show_admin_section(update, context, user_id)
    
    async def show_admin_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать настройки админки"""
        query = update.callback_query
        await query.answer("Функция в разработке")
    
    # Методы аналитики
    async def show_analytics_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать дашборд аналитики"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            await query.answer("❌ Нет доступа к аналитике")
            return
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Системная статистика", callback_data="analytics_summary")],
            [InlineKeyboardButton("🤖 События бота", callback_data="analytics_bot_events")],
            [InlineKeyboardButton("👥 Активность пользователей", callback_data="analytics_users")],
            [InlineKeyboardButton("📈 Полный отчет", callback_data="analytics_full_report")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_system")]
        ])
        
        await query.edit_message_text(
            text="📊 **Аналитика системы**\n\nВыберите тип отчета:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def create_system_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать системную статистику"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Получаю статистику...")
        
        try:
            # Записываем текущую статистику
            self.analytics.record_system_stats()
            
            # Получаем текстовый отчет
            summary = self.analytics.get_system_summary()
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="analytics_summary")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text=summary,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await query.answer("❌ Ошибка получения статистики")
    
    async def show_bot_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать события бота"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("🤖 Получаю события бота...")
        
        try:
            # Получаем события за последние 24 часа
            events_summary = self.analytics.get_bot_events_summary(hours=24)
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="analytics_bot_events")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text=events_summary,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения событий бота: {e}")
            await query.answer("❌ Ошибка получения событий")
    
    async def show_user_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать активность пользователей"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("👥 Получаю активность пользователей...")
        
        try:
            # Получаем активность пользователей
            activity_summary = self.analytics.get_user_activity_summary()
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="analytics_users")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text=activity_summary,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения активности пользователей: {e}")
            await query.answer("❌ Ошибка получения активности")
    
    async def show_full_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать полный отчет о производительности"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📈 Генерирую полный отчет...")
        
        try:
            # Записываем текущую статистику
            self.analytics.record_system_stats()
            
            # Получаем полный отчет
            full_report = self.analytics.get_performance_report()
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="analytics_full_report")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text=full_report,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации полного отчета: {e}")
            await query.answer("❌ Ошибка генерации отчета")
    
    # Методы сервера
    async def restart_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Перезапустить бота"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "manage"):
            await query.answer("❌ У вас нет прав для перезапуска бота")
            return
        
        try:
            await query.answer("🔄 Перезапуск бота...")
            
            # Создаем кнопку для подтверждения
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, перезапустить", callback_data="server_restart_confirm")],
                [InlineKeyboardButton("❌ Отмена", callback_data="server_status")]
            ])
            
            await query.edit_message_text(
                "⚠️ **Перезапуск бота**\n\n"
                "Бот будет перезапущен. Это может занять несколько секунд.\n"
                "Вы уверены, что хотите продолжить?",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def confirm_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Подтверждение перезапуска"""
        query = update.callback_query
        
        try:
            await query.answer("🔄 Перезапуск...")
            
            await query.edit_message_text(
                "🔄 **Перезапуск бота**\n\n"
                "Бот перезапускается...\n"
                "Попробуйте отправить /start через несколько секунд."
            )
            
            # Запускаем перезапуск в отдельном потоке
            import asyncio
            asyncio.create_task(self.perform_restart())
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def perform_restart(self):
        """Выполнить перезапуск бота"""
        try:
            # Ждем немного, чтобы сообщение отправилось
            await asyncio.sleep(2)
            
            # Перезапускаем процесс
            import os
            import sys
            python = sys.executable
            os.execl(python, python, *sys.argv)
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска: {e}")

    async def show_processes(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать процессы Python"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "view"):
            await query.answer("❌ У вас нет прав для просмотра процессов")
            return
        
        try:
            await query.answer("📊 Получение процессов...")
            
            import psutil
            
            # Находим все процессы Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    if 'python' in proc.info['name'].lower():
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline'][:3]) if proc.info['cmdline'] else '',
                            'memory': memory_mb
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if python_processes:
                # Сортируем по использованию памяти
                python_processes.sort(key=lambda x: x['memory'], reverse=True)
                
                processes_text = "🐍 **Процессы Python**\n\n"
                for i, proc in enumerate(python_processes[:10], 1):  # Показываем топ 10
                    processes_text += f"{i}. **PID {proc['pid']}**\n"
                    processes_text += f"   Память: {proc['memory']:.1f} МБ\n"
                    processes_text += f"   Команда: {proc['cmdline'][:50]}...\n\n"
            else:
                processes_text = "🐍 **Процессы Python**\n\nНе найдено процессов Python."
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data="server_processes")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="server_status")]
            ])
            
            await query.edit_message_text(
                processes_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def create_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать резервную копию данных"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "manage"):
            await query.answer("❌ У вас нет прав для создания бэкапа")
            return
        
        try:
            await query.answer("💾 Создание бэкапа...")
            
            import os
            from datetime import datetime
            import tarfile
            
            # Создаем папку для бэкапов если её нет
            backup_dir = "storage/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Имя файла бэкапа
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Создаем архив
            with tarfile.open(backup_path, "w:gz") as tar:
                # Добавляем папки для бэкапа
                folders_to_backup = ["storage", "logs", "config.json"]
                for folder in folders_to_backup:
                    if os.path.exists(folder):
                        tar.add(folder, arcname=os.path.basename(folder))
            
            # Получаем размер файла
            file_size = os.path.getsize(backup_path) / 1024 / 1024  # МБ
            
            backup_text = f"""
💾 **Бэкап создан!**

**Файл:** {backup_name}
**Размер:** {file_size:.2f} МБ
**Путь:** {backup_path}
**Время:** {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

✅ Резервная копия успешно создана!
            """
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📁 Скачать бэкап", callback_data=f"backup_download_{backup_name}")],
                [InlineKeyboardButton("🗑️ Удалить бэкап", callback_data=f"backup_delete_{backup_name}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="server_status")]
            ])
            
            await query.edit_message_text(
                backup_text.strip(),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка создания бэкапа: {str(e)}")

    async def download_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, backup_name: str):
        """Скачать бэкап"""
        query = update.callback_query
        
        try:
            await query.answer("📁 Отправка бэкапа...")
            
            import os
            backup_path = os.path.join("storage/backups", backup_name)
            
            if os.path.exists(backup_path):
                with open(backup_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        filename=backup_name,
                        caption=f"💾 Резервная копия: {backup_name}"
                    )
                await query.answer("✅ Бэкап отправлен в чат")
            else:
                await query.answer("❌ Файл бэкапа не найден")
                
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def delete_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, backup_name: str):
        """Удалить бэкап"""
        query = update.callback_query
        
        try:
            import os
            backup_path = os.path.join("storage/backups", backup_name)
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                await query.answer("✅ Бэкап удален")
                
                # Возвращаемся к статусу сервера
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить статус", callback_data="server_status")]
                ])
                
                await query.edit_message_text(
                    f"✅ **Бэкап удален!**\n\nФайл {backup_name} был удален.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await query.answer("❌ Файл бэкапа не найден")
                
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    # Методы админки
    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Добавить нового пользователя"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "manage"):
            await query.answer("❌ У вас нет прав для добавления пользователей.")
            return
        
        try:
            await query.answer("➕ Добавление пользователя...")
            
            # Создаем форму для добавления пользователя
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Ввести ID пользователя", callback_data="admin_add_user_id")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                "➕ **Добавление пользователя**\n\n"
                "Для добавления нового пользователя:\n"
                "1. Попросите пользователя отправить боту команду /start\n"
                "2. Скопируйте его Telegram ID\n"
                "3. Введите ID и выберите роль\n\n"
                "Или нажмите кнопку ниже для ввода ID:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def show_add_user_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать форму добавления пользователя"""
        query = update.callback_query
        
        try:
            await query.answer("📝 Форма добавления...")
            
            # Сохраняем состояние в контексте
            context.user_data['adding_user'] = True
            
            # Создаем кнопки с ролями
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Пользователь", callback_data="admin_role_user")],
                [InlineKeyboardButton("🔧 Модератор", callback_data="admin_role_moderator")],
                [InlineKeyboardButton("👑 Администратор", callback_data="admin_role_admin")],
                [InlineKeyboardButton("❌ Отмена", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                "📝 **Добавление пользователя**\n\n"
                "Отправьте мне Telegram ID пользователя в следующем сообщении.\n"
                "Затем выберите роль для нового пользователя.\n\n"
                "**Как получить Telegram ID:**\n"
                "1. Попросите пользователя написать боту @userinfobot\n"
                "2. Скопируйте его ID из ответа\n"
                "3. Отправьте ID мне",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def set_user_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Установить роль для нового пользователя"""
        query = update.callback_query
        
        try:
            # Получаем роль из callback_data
            role = query.data.replace("admin_role_", "")
            role_names = {
                "user": "Пользователь",
                "moderator": "Модератор", 
                "admin": "Администратор"
            }
            
            # Получаем ID пользователя из контекста
            new_user_id = context.user_data.get('new_user_id')
            if not new_user_id:
                await query.answer("❌ ID пользователя не найден. Попробуйте еще раз.")
                return
            
            # Добавляем пользователя
            success = await self.role_manager.add_user(
                user_id=new_user_id,
                name=f"Пользователь {new_user_id}",
                role=role,
                added_by=user_id
            )
            
            if success:
                await query.answer(f"✅ Пользователь добавлен с ролью '{role_names[role]}'")
                
                # Очищаем контекст
                context.user_data.pop('adding_user', None)
                context.user_data.pop('new_user_id', None)
                
                # Возвращаемся к списку пользователей
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")],
                    [InlineKeyboardButton("🔄 Обновить список", callback_data="admin_users")]
                ])
                
                await query.edit_message_text(
                    f"✅ **Пользователь добавлен!**\n\n"
                    f"**ID:** {new_user_id}\n"
                    f"**Роль:** {role_names[role]}\n\n"
                    f"Пользователь может теперь использовать бота.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await query.answer("❌ Ошибка добавления пользователя")
                
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Удалить пользователя"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "manage"):
            await query.answer("❌ У вас нет прав для удаления пользователей.")
            return
        
        try:
            await query.answer("🗑️ Удаление пользователя...")
            
            # Получаем список пользователей для выбора
            users = await self.role_manager.list_users(user_id)
            
            if not users:
                await query.edit_message_text(
                    "❌ Нет пользователей для удаления.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
                    ])
                )
                return
            
            # Создаем кнопки с пользователями
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = []
            for user in users:
                if user['id'] != user_id:  # Нельзя удалить себя
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🗑️ {user['name']} ({user['role']})", 
                            callback_data=f"admin_delete_confirm_{user['id']}"
                        )
                    ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")])
            
            await query.edit_message_text(
                "🗑️ **Удаление пользователя**\n\n"
                "Выберите пользователя для удаления:\n"
                "(Вы не можете удалить себя)",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def confirm_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Подтвердить удаление пользователя"""
        query = update.callback_query
        
        try:
            # Получаем ID пользователя из callback_data
            target_user_id = int(query.data.replace("admin_delete_confirm_", ""))
            
            # Получаем информацию о пользователе
            user_info = await self.role_manager.get_user_info(target_user_id)
            
            if not user_info:
                await query.answer("❌ Пользователь не найден")
                return
            
            # Создаем кнопки подтверждения
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_delete_final_{target_user_id}")],
                [InlineKeyboardButton("❌ Отмена", callback_data="admin_delete_user")]
            ])
            
            await query.edit_message_text(
                f"⚠️ **Подтверждение удаления**\n\n"
                f"Вы действительно хотите удалить пользователя:\n"
                f"**{user_info['name']}** (ID: {target_user_id})\n"
                f"Роль: {user_info['role']}\n\n"
                f"Это действие нельзя отменить!",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def final_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Выполнить удаление пользователя"""
        query = update.callback_query
        
        try:
            # Получаем ID пользователя из callback_data
            target_user_id = int(query.data.replace("admin_delete_final_", ""))
            
            # Удаляем пользователя
            success = await self.role_manager.remove_user(target_user_id, user_id)
            
            if success:
                await query.answer("✅ Пользователь удален")
                
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить список", callback_data="admin_users")]
                ])
                
                await query.edit_message_text(
                    f"✅ **Пользователь удален!**\n\n"
                    f"Пользователь с ID {target_user_id} был удален из системы.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await query.answer("❌ Ошибка удаления пользователя")
                
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать логи бота"""
        query = update.callback_query
        
        if not await self.role_manager.check_permission(user_id, "admin", "view"):
            await query.answer("❌ У вас нет прав для просмотра логов.")
            return
        
        try:
            await query.answer("📋 Получение логов...")
            
            # Читаем последние строки из лог файла
            log_file = "logs/sella_bot.log"
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-20:] if len(lines) > 20 else lines  # Последние 20 строк
                    log_content = ''.join(last_lines)
            except FileNotFoundError:
                log_content = "Лог файл не найден."
            except Exception as e:
                log_content = f"Ошибка чтения лога: {str(e)}"
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить логи", callback_data="admin_logs")],
                [InlineKeyboardButton("📁 Полный лог", callback_data="admin_full_log")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                f"📋 **Последние логи бота**\n\n"
                f"```\n{log_content[-3000:]}\n```\n\n"
                f"Показано последних {len(last_lines) if 'last_lines' in locals() else 0} строк",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def show_full_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать полный лог"""
        query = update.callback_query
        
        try:
            await query.answer("📁 Получение полного лога...")
            
            # Читаем весь лог файл
            log_file = "logs/sella_bot.log"
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            except FileNotFoundError:
                log_content = "Лог файл не найден."
            except Exception as e:
                log_content = f"Ошибка чтения лога: {str(e)}"
            
            # Если лог слишком большой, отправляем как файл
            if len(log_content) > 4000:
                # Создаем временный файл
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
                    f.write(log_content)
                    temp_file = f.name
                
                # Отправляем файл
                with open(temp_file, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        filename="sella_bot_full.log",
                        caption="📁 Полный лог бота"
                    )
                
                # Удаляем временный файл
                import os
                os.unlink(temp_file)
                
                await query.answer("📁 Полный лог отправлен в чат")
            else:
                # Показываем в сообщении
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад", callback_data="admin_logs")]
                ])
                
                await query.edit_message_text(
                    f"📁 **Полный лог бота**\n\n"
                    f"```\n{log_content}\n```",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}") 

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать справку по боту"""
        query = update.callback_query
        
        try:
            await query.answer("ℹ️ Открываю справку...")
            
            help_text = """
🤖 **Селла - Универсальный бот-менеджер**

## 📋 Основные команды
• `/start` - Запуск бота и главное меню
• `/help` - Эта справка
• `/menu` - Главное меню
• `/status` - Статус системы

## 🖥️ Разделы бота

### 📊 Аналитика
• Системная статистика (CPU, память, диск)
• События бота
• Активность пользователей
• Полный отчет о производительности

### 🖥️ Система
• Мониторинг системы в реальном времени
• Настройки системы
• Уведомления

### ⚙️ Сервер
• Статус бота
• Перезапуск бота
• Просмотр процессов Python
• Создание резервных копий

### 💾 Хранилище
• Просмотр файлов
• Загрузка файлов
• Скачивание файлов
• Поиск файлов
• Удаление файлов

### 👤 Админка (только для администраторов)
• Управление пользователями
• Добавление/удаление пользователей
• Просмотр логов
• Управление правами

## 🔧 Управление пользователями

### Добавление пользователя:
1. Откройте раздел **👤 Админка**
2. Нажмите **"➕ Добавить пользователя"**
3. Попросите пользователя написать боту @userinfobot
4. Скопируйте его Telegram ID
5. Введите ID и выберите роль

### Роли пользователей:
• **👤 Пользователь** - базовый доступ
• **🔧 Модератор** - расширенные права
• **👑 Администратор** - полный доступ

## 🛠️ Устранение проблем

### Бот не отвечает:
1. Проверьте токен в `config.json`
2. Перезапустите бота через раздел **⚙️ Сервер**
3. Проверьте логи в разделе **👤 Админка**

### Нет доступа к функциям:
1. Убедитесь, что ваш ID добавлен в `admin_ids`
2. Проверьте, что у вас роль "Администратор"

## 📞 Поддержка

Для получения дополнительной помощи:
• Проверьте файл `BOT_SETUP_GUIDE.md`
• Посмотрите логи бота
• Обратитесь к администратору

---
**Версия:** 2.0 (Termux)
**Платформа:** Android/Termux
            """
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 Подробная инструкция", callback_data="help_setup_guide")],
                [InlineKeyboardButton("🔧 Устранение проблем", callback_data="help_troubleshooting")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
            ])
            
            await query.edit_message_text(
                help_text.strip(),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def show_setup_guide(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать подробную инструкцию по настройке"""
        query = update.callback_query
        
        try:
            await query.answer("📖 Открываю инструкцию...")
            
            setup_text = """
📖 **Подробная инструкция по настройке**

## 🆕 Создание бота в Telegram

### Шаг 1: Найти BotFather
1. Откройте Telegram
2. Найдите пользователя **@BotFather**
3. Нажмите **"Start"** или отправьте команду `/start`

### Шаг 2: Создать нового бота
1. Отправьте команду `/newbot`
2. Введите **имя бота** (например: "Селла - Универсальный менеджер")
3. Введите **username бота** (например: "sella_manager_bot")
   - Должен заканчиваться на `bot`
   - Может содержать только буквы, цифры и подчеркивания
   - Должен быть уникальным

### Шаг 3: Получить токен
BotFather отправит вам сообщение с токеном:
```
Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ ВАЖНО:** Сохраните этот токен!

## ⚙️ Настройка конфигурации

### Шаг 1: Открыть config.json
Откройте файл `config.json` в корне проекта

### Шаг 2: Вставить токен
Замените `"ВАШ_ТОКЕН_ЗДЕСЬ"` на ваш токен

### Шаг 3: Указать ID администратора
Замените `ВАШ_TELEGRAM_ID` на ваш Telegram ID

**Как узнать свой Telegram ID:**
1. Найдите бота @userinfobot в Telegram
2. Отправьте ему любое сообщение
3. Он ответит вашим ID

## 📱 Установка в Termux

### Шаг 1: Установить Termux
1. Скачайте Termux с F-Droid (НЕ из Google Play!)
2. Установите приложение
3. Откройте Termux

### Шаг 2: Обновить систему
```bash
pkg update -y && pkg upgrade -y
```

### Шаг 3: Установить необходимые пакеты
```bash
pkg install python python-pip git -y
```

### Шаг 4: Клонировать проект
```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd <ПАПКА_ПРОЕКТА>
```

### Шаг 5: Запустить автоматическую установку
```bash
chmod +x start_termux.sh
./start_termux.sh
```

## 🚀 Первый запуск

### Шаг 1: Найти бота
1. Откройте Telegram
2. Найдите вашего бота по username
3. Нажмите **"Start"** или отправьте `/start`

### Шаг 2: Проверить работу
Бот должен ответить приветственным сообщением

### Шаг 3: Проверить меню
Должны появиться кнопки всех разделов

---
**Подробнее:** См. файл `BOT_SETUP_GUIDE.md`
            """
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔧 Устранение проблем", callback_data="help_troubleshooting")],
                [InlineKeyboardButton("⬅️ Назад к справке", callback_data="help")]
            ])
            
            await query.edit_message_text(
                setup_text.strip(),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}")

    async def show_troubleshooting(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показать раздел устранения проблем"""
        query = update.callback_query
        
        try:
            await query.answer("🔧 Открываю раздел проблем...")
            
            troubleshooting_text = """
🔧 **Устранение проблем**

## ❌ Бот не отвечает

### Возможные причины:
1. **Неправильный токен** в `config.json`
2. **Нет интернет соединения**
3. **Бот остановлен**

### Решение:
1. Проверьте токен в `config.json`
2. Перезапустите бота:
   ```bash
   python main.py
   ```
3. Проверьте логи в разделе **👤 Админка**

## ❌ Ошибка "Module not found"

### Решение:
```bash
source venv/bin/activate
pip install -r requirements_termux.txt
```

## ❌ Ошибка "Permission denied"

### Решение:
```bash
chmod +x start_termux.sh
```

## ❌ Бот не запускается

### Проверьте:
1. **Логи:**
   ```bash
   tail -f logs/sella_bot.log
   ```

2. **Конфигурацию:**
   ```bash
   python -c "import json; print(json.load(open('config.json')))"
   ```

## ❌ Нет доступа к функциям

### Проверьте:
1. Ваш ID добавлен в `admin_ids` в `config.json`
2. У вас роль "Администратор"

### Как добавить себя в админы:
1. Откройте `config.json`
2. Найдите строку `"admin_ids": [ВАШ_ID]`
3. Замените `ВАШ_ID` на ваш Telegram ID

## ❌ Ошибки в Termux

### Проблема: "No space left"
```bash
pkg clean
rm -rf ~/.cache/pip
```

### Проблема: "Package not found"
```bash
pkg update -y
pkg install python python-pip -y
```

## 🔄 Автозапуск в Termux

Для автоматического запуска при перезагрузке:
```bash
# Установить cronie
pkg install cronie -y

# Открыть crontab
crontab -e

# Добавить строку
@reboot cd /path/to/bot && ./start_termux.sh
```

## 📞 Дополнительная помощь

### Полезные команды:
- `/start` - запуск бота
- `/help` - справка
- `/status` - статус системы
- `/menu` - главное меню

### Логи и отладка:
- Логи сохраняются в `logs/sella_bot.log`
- Для просмотра: `tail -f logs/sella_bot.log`
- Для очистки: `> logs/sella_bot.log`

---
**Если проблема не решена:** Обратитесь к администратору
            """
            
            # Создаем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 Инструкция по настройке", callback_data="help_setup_guide")],
                [InlineKeyboardButton("⬅️ Назад к справке", callback_data="help")]
            ])
            
            await query.edit_message_text(
                troubleshooting_text.strip(),
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}") 