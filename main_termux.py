import logging
import json
import asyncio
import platform
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Импорт модулей для Termux
from modules.role_manager import RoleManager
from modules.system_monitor_termux import SystemMonitor
from modules.process_manager_termux import ProcessManager
from modules.cloud_storage import CloudStorage
from modules.notification import NotificationManager

# Импорт обработчиков команд
from handlers.main_menu import show_main_menu
from handlers.system_handlers import system_status
from handlers.process_handlers import bots_status
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
        logging.FileHandler(config.get('logging', {}).get('file', 'logs/sella_bot_termux.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SellaBotTermux')

# Инициализация модулей
role_manager = RoleManager(config)
system_monitor = SystemMonitor(config, role_manager)
process_manager = ProcessManager(config, role_manager)
cloud_storage = CloudStorage(config, role_manager)

# Основная функция запуска
async def main():
    logger.info(f"Запуск бота Селла на платформе: {platform.system()}")
    
    application = Application.builder().token(config['bot_token']).build()

    # Инициализация менеджера уведомлений (передаем application.bot)
    notification_manager = NotificationManager(config, role_manager, application.bot)

    # Инициализация обработчиков
    callback_handlers = CallbackHandlers(role_manager, system_monitor, process_manager, cloud_storage, notification_manager)
    file_handlers = FileHandlers(cloud_storage, role_manager)

    # Обработчик команды /start с интерактивным меню
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_info = await role_manager.get_user_info(user_id)
        name = user_info["name"] if user_info else "Гость"
        role = user_info["role"] if user_info else "guest"
        
        # Получение прав пользователя для меню
        user_menu = await role_manager.get_user_menu(user_id)
        
        # Создание интерактивного меню
        keyboard = await MenuButtons.create_main_menu(user_menu)
        
        await update.message.reply_text(
            f"👋 Привет, {name}!\n\nТы — {role}.\nДобро пожаловать в универсального бота-менеджера Селла!\n\n🖥️ Платформа: {platform.system()}\n\nВыберите раздел для управления:",
            reply_markup=keyboard
        )

    application.add_handler(CommandHandler("start", start))

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("menu", lambda u, c: show_main_menu(u, c, role_manager)))
    application.add_handler(CommandHandler("status", lambda u, c: system_status(u, c, system_monitor, role_manager)))
    application.add_handler(CommandHandler("bots", lambda u, c: bots_status(u, c, process_manager, role_manager)))
    application.add_handler(CommandHandler("server", lambda u, c: server_status(u, c)))
    application.add_handler(CommandHandler("storage", lambda u, c: list_files(u, c, cloud_storage, role_manager)))
    application.add_handler(CommandHandler("users", lambda u, c: list_users(u, c, role_manager)))

    # Дополнительные команды
    application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text(
        "🤖 **Селла - Команды**\n\n"
        "/start - Запуск бота\n"
        "/menu - Главное меню\n"
        "/status - Статус системы\n"
        "/bots - Статус ботов\n"
        "/server - Управление сервером\n"
        "/storage - Облачное хранилище\n"
        "/users - Список пользователей (админ)\n"
        "/help - Эта справка\n\n"
        f"🖥️ Платформа: {platform.system()}"
    )))

    # Обработчики callback-запросов (кнопки)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(lambda u, c: callback_handlers.handle_callback(u, c)))

    # Обработчики файлов
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.Document.ALL, lambda u, c: file_handlers.handle_document(u, c)))
    application.add_handler(MessageHandler(filters.PHOTO, lambda u, c: file_handlers.handle_photo(u, c)))
    application.add_handler(MessageHandler(filters.VIDEO, lambda u, c: file_handlers.handle_video(u, c)))
    application.add_handler(MessageHandler(filters.AUDIO, lambda u, c: file_handlers.handle_audio(u, c)))

    logger.info("Бот Селла запущен в Termux!")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main()) 