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
            elif callback_data == "analytics_cpu_memory":
                await self.create_cpu_memory_chart(update, context, user_id)
            elif callback_data == "analytics_disk":
                await self.create_disk_chart(update, context, user_id)
            elif callback_data == "analytics_network":
                await self.create_network_chart(update, context, user_id)
            elif callback_data == "analytics_processes":
                await self.create_processes_chart(update, context, user_id)
            elif callback_data == "analytics_summary":
                await self.create_system_summary(update, context, user_id)
            elif callback_data == "analytics_collect_data":
                await self.start_data_collection(update, context, user_id)
            # Сервер
            elif callback_data == "server_status":
                await self.show_server_status(update, context, user_id)
            elif callback_data == "server_start":
                await self.start_server(update, context, user_id)
            elif callback_data == "server_stop":
                await self.stop_server(update, context, user_id)
            elif callback_data == "server_backup":
                await self.create_server_backup(update, context, user_id)
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
            elif callback_data == "admin_permissions":
                await self.show_admin_permissions(update, context, user_id)
            elif callback_data == "admin_logs":
                await self.show_admin_logs(update, context, user_id)
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
            [InlineKeyboardButton("📊 Сводка системы", callback_data="analytics_summary")],
            [InlineKeyboardButton("🖥️ CPU и память", callback_data="analytics_cpu_memory")],
            [InlineKeyboardButton("💾 Использование диска", callback_data="analytics_disk")],
            [InlineKeyboardButton("🌐 Сетевая активность", callback_data="analytics_network")],
            [InlineKeyboardButton("⚙️ Топ процессов", callback_data="analytics_processes")],
            [InlineKeyboardButton("📈 Сбор данных (60 сек)", callback_data="analytics_collect_data")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="section_system")]
        ])
        
        await query.edit_message_text(
            text="📊 **Аналитика системы**\n\nВыберите тип графика для создания:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def create_system_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать сводный график системы"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Создаю сводный график...")
        
        try:
            chart_path = self.analytics.create_system_summary()
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="system_summary.html",
                    caption="📊 **Сводка системы**\n\nОткройте файл в браузере для просмотра интерактивного графика"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_summary")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **График создан!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания сводного графика: {e}")
            await query.answer("❌ Ошибка создания графика")
    
    async def create_cpu_memory_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать график CPU и памяти"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Создаю график CPU и памяти...")
        
        try:
            # Собираем данные за 30 секунд
            data_points = await self.analytics.collect_data_points(duration=30, interval=2)
            chart_path = self.analytics.create_cpu_memory_chart(data_points)
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="cpu_memory_chart.html",
                    caption="🖥️ **График CPU и памяти**\n\nДанные за 30 секунд"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_cpu_memory")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **График создан!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания графика CPU/памяти: {e}")
            await query.answer("❌ Ошибка создания графика")
    
    async def create_disk_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать график использования диска"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Создаю график диска...")
        
        try:
            chart_path = self.analytics.create_disk_usage_chart()
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="disk_usage.html",
                    caption="💾 **Использование диска**\n\nКруговая диаграмма"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_disk")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **График создан!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания графика диска: {e}")
            await query.answer("❌ Ошибка создания графика")
    
    async def create_network_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать график сетевой активности"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Создаю график сети...")
        
        try:
            # Собираем данные за 30 секунд
            data_points = await self.analytics.collect_data_points(duration=30, interval=2)
            chart_path = self.analytics.create_network_chart(data_points)
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="network_activity.html",
                    caption="🌐 **Сетевая активность**\n\nДанные за 30 секунд"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_network")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **График создан!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания сетевого графика: {e}")
            await query.answer("❌ Ошибка создания графика")
    
    async def create_processes_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Создать график топ процессов"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📊 Создаю график процессов...")
        
        try:
            chart_path = self.analytics.create_processes_chart(top_n=10)
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="top_processes.html",
                    caption="⚙️ **Топ 10 процессов**\n\nПо использованию CPU и памяти"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_processes")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **График создан!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания графика процессов: {e}")
            await query.answer("❌ Ошибка создания графика")
    
    async def start_data_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Запустить сбор данных для аналитики"""
        query = update.callback_query
        
        if not self.analytics:
            await query.answer("❌ Модуль аналитики недоступен")
            return
        
        await query.answer("📈 Начинаю сбор данных...")
        
        try:
            # Собираем данные за 60 секунд
            data_points = await self.analytics.collect_data_points(duration=60, interval=2)
            
            # Создаем комплексный график
            chart_path = self.analytics.create_cpu_memory_chart(data_points)
            
            # Отправляем файл
            with open(chart_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename="system_analysis.html",
                    caption="📈 **Анализ системы**\n\nДанные за 60 секунд"
                )
            
            # Показываем кнопки
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Создать еще", callback_data="analytics_collect_data")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="analytics_dashboard")]
            ])
            
            await query.edit_message_text(
                text="✅ **Анализ завершен!**\n\nФайл отправлен в чат. Откройте его в браузере для просмотра.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
            await query.answer("❌ Ошибка сбора данных") 