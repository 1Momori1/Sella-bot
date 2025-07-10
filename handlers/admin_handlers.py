from telegram import Update
from telegram.ext import ContextTypes

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    user_id = update.effective_user.id
    if role_manager:
        users = await role_manager.list_users(user_id)
        if users:
            msg = '\n'.join([f"{u['id']} — {u['name']} ({u['role']})" for u in users])
            await update.message.reply_text(f"\U0001F465 Пользователи:\n" + msg)
        else:
            await update.message.reply_text("Нет доступа или нет пользователей.")
    else:
        await update.message.reply_text("Модуль ролей не инициализирован.") 