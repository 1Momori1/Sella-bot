import logging
import json
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Импорт модулей
from modules.role_manager import RoleManager
from modules.system_monitor import SystemMonitor
from modules.process_manager import ProcessManager
from modules.cloud_storage import CloudStorage
from modules.notification import NotificationManager
from modules.web_interface import WebInterface
from modules.ai_assistant import AIAssistant
from modules.security_monitor import SecurityMonitor
from modules.analytics import Analytics

# Импорт обработчиков команд
from handlers.main_menu import show_main_menu
from handlers.system_handlers import system_status
from handlers.server_handlers import server_status
from handlers.storage_handlers import list_files
from handlers.admin_handlers import list_users
from handlers.callback_handlers import CallbackHandlers
from handlers.file_handlers import FileHandlers
from handlers.menu_buttons import MenuButtons

CONFIG_PATH = 'config.json'

# Загрузка конфигурации
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.get('logging', {}).get('level', 'INFO')),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(config.get('logging', {}).get('file', 'logs/sella_bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SellaBot')

# Инициализация модулей
role_manager = RoleManager(config)
system_monitor = SystemMonitor(config, role_manager)
process_manager = ProcessManager(config, role_manager)
cloud_storage = CloudStorage(config, role_manager)

# Инициализация новых модулей
web_interface = WebInterface(config, role_manager, system_monitor, process_manager, cloud_storage)
ai_assistant = AIAssistant(config, role_manager, system_monitor, process_manager, None)  # notification_manager будет инициализирован позже
security_monitor = SecurityMonitor(config, role_manager, system_monitor, process_manager, None)  # notification_manager будет инициализирован позже
analytics = Analytics(config, role_manager, system_monitor, process_manager, cloud_storage)

# Основная функция запуска
def main():
    application = Application.builder().token(config['bot_token']).build()

    # Инициализация менеджера уведомлений (передаем application.bot)
    notification_manager = NotificationManager(config, role_manager, application.bot)
    
    # Обновление ссылок на notification_manager в новых модулях
    ai_assistant.notification_manager = notification_manager
    security_monitor.notification_manager = notification_manager

    # Инициализация обработчиков
    callback_handlers = CallbackHandlers(role_manager, system_monitor, process_manager, cloud_storage, notification_manager, analytics)
    file_handlers = FileHandlers(cloud_storage, role_manager)

    # Обработчик команды /start с интерактивным меню
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id
        user_info = await role_manager.get_user_info(user_id)
        name = user_info["name"] if user_info else "Гость"
        role = user_info["role"] if user_info else "guest"
        
        # Получение прав пользователя для меню
        user_menu = await role_manager.get_user_menu(user_id)
        
        # Создание интерактивного меню
        keyboard = await MenuButtons.create_main_menu(user_menu)
        
        await update.message.reply_text(
            f"👋 Привет, {name}!\n\nТы — {role}.\nДобро пожаловать в универсального бота-менеджера Селла!\n\nВыберите раздел для управления:",
            reply_markup=keyboard
        )

    application.add_handler(CommandHandler("start", start))

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("menu", lambda u, c: show_main_menu(u, c, role_manager)))
    application.add_handler(CommandHandler("status", lambda u, c: system_status(u, c, system_monitor, role_manager)))
    application.add_handler(CommandHandler("server", lambda u, c: server_status(u, c)))
    application.add_handler(CommandHandler("storage", lambda u, c: list_files(u, c, cloud_storage, role_manager)))
    application.add_handler(CommandHandler("users", lambda u, c: list_users(u, c, role_manager)))

    # Дополнительные команды
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        await update.message.reply_text(
            "🤖 **Селла - Команды**\n\n"
            "/start - Запуск бота\n"
            "/menu - Главное меню\n"
            "/status - Статус системы\n"
            "/server - Управление сервером\n"
            "/storage - Облачное хранилище\n"
            "/users - Список пользователей (админ)\n"
            "/help - Эта справка"
        )
    
    application.add_handler(CommandHandler("help", help_command))

    # Обработчики callback-запросов (кнопки)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(lambda u, c: callback_handlers.handle_callback(u, c)))

    # Обработчики файлов
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.Document.ALL, lambda u, c: file_handlers.handle_document(u, c)))
    application.add_handler(MessageHandler(filters.PHOTO, lambda u, c: file_handlers.handle_photo(u, c)))
    application.add_handler(MessageHandler(filters.VIDEO, lambda u, c: file_handlers.handle_video(u, c)))
    application.add_handler(MessageHandler(filters.AUDIO, lambda u, c: file_handlers.handle_audio(u, c)))

    # Фоновые задачи отключены для стабильности
    # Раскомментируйте для включения:
    # if web_interface.enabled:
    #     asyncio.create_task(web_interface.start_server())
    # if security_monitor.enabled:
    #     asyncio.create_task(security_monitor.start_security_monitoring())
    # if analytics.enabled:
    #     asyncio.create_task(analytics.start_analytics())
    
    logger.info("Бот Селла запущен!")
    application.run_polling()

if __name__ == "__main__":
    main() 