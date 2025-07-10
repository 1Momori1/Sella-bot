from telegram import Update
from telegram.ext import ContextTypes

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE, cloud_storage=None, role_manager=None):
    user_id = update.effective_user.id
    if cloud_storage and role_manager:
        files = await cloud_storage.list_files(user_id)
        if files:
            msg = '\n'.join([f"{f['name']} ({f['size']} байт)" for f in files])
            await update.message.reply_text(f"\U00002601 Ваши файлы:\n" + msg)
        else:
            await update.message.reply_text("\U00002601 Нет файлов.")
    else:
        await update.message.reply_text("Модуль хранилища не инициализирован.") 