from telegram import Update
from telegram.ext import ContextTypes

async def bots_status(update: Update, context: ContextTypes.DEFAULT_TYPE, process_manager=None, role_manager=None):
    user_id = update.effective_user.id
    if process_manager and role_manager:
        status = await process_manager.get_bots_status_text(user_id)
        await update.message.reply_text(status)
    else:
        await update.message.reply_text("Модуль управления процессами не инициализирован.") 