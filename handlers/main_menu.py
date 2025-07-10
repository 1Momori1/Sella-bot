from telegram import Update
from telegram.ext import ContextTypes

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    user_id = update.effective_user.id
    user_info = await role_manager.get_user_info(user_id) if role_manager else None
    name = user_info["name"] if user_info else "Гость"
    role = user_info["role"] if user_info else "guest"
    await update.message.reply_text(
        f"\U0001F4C8 Главное меню\n\nПользователь: {name} ({role})\n\nВыберите раздел в меню или используйте команды."
    ) 