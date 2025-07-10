from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, List, Any

class MenuButtons:
    """Класс для создания интерактивных кнопок и меню"""
    
    @staticmethod
    async def create_main_menu(user_permissions: Dict[str, List[str]]) -> InlineKeyboardMarkup:
        """Создание главного меню с разделами"""
        keyboard = []
        
        # Основные разделы
        main_sections = []
        
        # Система
        if "system" in user_permissions and "view" in user_permissions["system"]:
            main_sections.append(InlineKeyboardButton("🖥️ Система", callback_data="section_system"))
        
        # Сервер
        if "server" in user_permissions and "view" in user_permissions["server"]:
            main_sections.append(InlineKeyboardButton("⛏️ Сервер", callback_data="section_server"))
        
        # Хранилище
        if "storage" in user_permissions and "view" in user_permissions["storage"]:
            main_sections.append(InlineKeyboardButton("☁️ Хранилище", callback_data="section_storage"))
        
        # Админка
        if "admin" in user_permissions:
            main_sections.append(InlineKeyboardButton("👑 Админка", callback_data="section_admin"))
        
        # Размещаем кнопки по 2 в ряд
        for i in range(0, len(main_sections), 2):
            row = [main_sections[i]]
            if i + 1 < len(main_sections):
                row.append(main_sections[i + 1])
            keyboard.append(row)
        
        # Дополнительные кнопки
        keyboard.append([
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh"),
            InlineKeyboardButton("❌ Закрыть", callback_data="close")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_system_menu(user_permissions: Dict[str, List[str]]) -> InlineKeyboardMarkup:
        """Создание меню системы"""
        keyboard = []
        
        # Мониторинг
        if "system" in user_permissions and "view" in user_permissions["system"]:
            keyboard.append([InlineKeyboardButton("📊 Мониторинг системы", callback_data="system_monitor")])
        
        # Настройки
        if "system" in user_permissions and "settings" in user_permissions["system"]:
            keyboard.append([InlineKeyboardButton("⚙️ Настройки системы", callback_data="system_settings")])
        
        # Уведомления
        if "notifications" in user_permissions and "view" in user_permissions["notifications"]:
            keyboard.append([InlineKeyboardButton("⚠️ Настройки уведомлений", callback_data="notifications_settings")])
        
        # Кнопки навигации
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_server_menu(user_permissions: Dict[str, List[str]]) -> InlineKeyboardMarkup:
        """Создание меню сервера"""
        keyboard = []
        
        # Статус сервера
        if "server" in user_permissions and "view" in user_permissions["server"]:
            keyboard.append([InlineKeyboardButton("📊 Статус сервера", callback_data="server_status")])
        
        # Управление сервером
        if "server" in user_permissions and "manage" in user_permissions["server"]:
            keyboard.append([
                InlineKeyboardButton("🟢 Запустить", callback_data="server_start"),
                InlineKeyboardButton("🔴 Остановить", callback_data="server_stop")
            ])
        
        # Бэкапы
        if "server" in user_permissions and "backup" in user_permissions["server"]:
            keyboard.append([InlineKeyboardButton("💾 Создать бэкап", callback_data="server_backup")])
        
        # Кнопки навигации
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_storage_menu(user_permissions: Dict[str, List[str]]) -> InlineKeyboardMarkup:
        """Создание меню хранилища"""
        keyboard = []
        
        # Просмотр файлов
        if "storage" in user_permissions and "view" in user_permissions["storage"]:
            keyboard.append([InlineKeyboardButton("📁 Мои файлы", callback_data="storage_list")])
        
        # Загрузка
        if "storage" in user_permissions and "upload" in user_permissions["storage"]:
            keyboard.append([InlineKeyboardButton("📤 Загрузить файл", callback_data="storage_upload")])
        
        # Скачивание
        if "storage" in user_permissions and "download" in user_permissions["storage"]:
            keyboard.append([InlineKeyboardButton("📥 Скачать файл", callback_data="storage_download")])
        
        # Поиск
        if "storage" in user_permissions and "view" in user_permissions["storage"]:
            keyboard.append([InlineKeyboardButton("🔍 Поиск файлов", callback_data="storage_search")])
        
        # Удаление
        if "storage" in user_permissions and "delete" in user_permissions["storage"]:
            keyboard.append([InlineKeyboardButton("🗑️ Удалить файл", callback_data="storage_delete")])
        
        # Кнопки навигации
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_admin_menu(user_permissions: Dict[str, List[str]]) -> InlineKeyboardMarkup:
        """Создание админского меню"""
        keyboard = []
        
        # Управление пользователями
        if "admin" in user_permissions:
            keyboard.append([InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")])
            keyboard.append([InlineKeyboardButton("🔐 Управление правами", callback_data="admin_permissions")])
            keyboard.append([InlineKeyboardButton("📝 Просмотр логов", callback_data="admin_logs")])
            keyboard.append([InlineKeyboardButton("⚙️ Конфигурация", callback_data="admin_config")])
        
        # Кнопки навигации
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_storage_files_menu(files: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Создание меню файлов хранилища"""
        buttons = []
        
        # Кнопки для каждого файла (первые 5)
        for i, file_info in enumerate(files[:5]):
            file_name = file_info['original_name']
            if len(file_name) > 20:
                file_name = file_name[:17] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    f"📄 {file_name}",
                    callback_data=f"file_info_{file_info['id']}"
                )
            ])
        
        # Кнопки действий
        action_buttons = []
        if files:
            action_buttons.extend([
                InlineKeyboardButton("📥 Скачать", callback_data="storage_download"),
                InlineKeyboardButton("🗑️ Удалить", callback_data="storage_delete")
            ])
        
        action_buttons.extend([
            InlineKeyboardButton("🔍 Поиск", callback_data="storage_search"),
            InlineKeyboardButton("🔄 Обновить", callback_data="storage_list")
        ])
        
        # Группируем кнопки действий по 2 в ряд
        for i in range(0, len(action_buttons), 2):
            if i + 1 < len(action_buttons):
                buttons.append([action_buttons[i], action_buttons[i + 1]])
            else:
                buttons.append([action_buttons[i]])
        
        # Кнопка возврата
        buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="section_storage")])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    async def create_storage_download_menu(files: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Создание меню для скачивания файлов"""
        buttons = []
        
        # Кнопки для каждого файла (первые 8)
        for i, file_info in enumerate(files[:8]):
            file_name = file_info['original_name']
            if len(file_name) > 25:
                file_name = file_name[:22] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    f"📥 {file_name}",
                    callback_data=f"file_download_{file_info['id']}"
                )
            ])
        
        # Кнопки навигации
        buttons.append([
            InlineKeyboardButton("📁 Список файлов", callback_data="storage_list"),
            InlineKeyboardButton("⬅️ Назад", callback_data="section_storage")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    async def create_storage_delete_menu(files: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Создание меню для удаления файлов"""
        buttons = []
        
        # Кнопки для каждого файла (первые 8)
        for i, file_info in enumerate(files[:8]):
            file_name = file_info['original_name']
            if len(file_name) > 25:
                file_name = file_name[:22] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    f"🗑️ {file_name}",
                    callback_data=f"file_delete_{file_info['id']}"
                )
            ])
        
        # Кнопки навигации
        buttons.append([
            InlineKeyboardButton("📁 Список файлов", callback_data="storage_list"),
            InlineKeyboardButton("⬅️ Назад", callback_data="section_storage")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    async def create_confirm_menu(action: str, item_id: str = None) -> InlineKeyboardMarkup:
        """Создание меню подтверждения действия"""
        callback_data = f"confirm_{action}"
        if item_id:
            callback_data += f"_{item_id}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data=callback_data),
                InlineKeyboardButton("❌ Нет", callback_data="cancel")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def create_pagination_menu(current_page: int, total_pages: int, base_callback: str) -> InlineKeyboardMarkup:
        """Создание меню пагинации"""
        keyboard = []
        
        # Кнопки навигации
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{base_callback}_page_{current_page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="no_action"))
        
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{base_callback}_page_{current_page+1}"))
        
        keyboard.append(nav_buttons)
        
        # Кнопка возврата
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard) 