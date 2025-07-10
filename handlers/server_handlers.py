from telegram import Update
from telegram.ext import ContextTypes

async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Статус сервера: функция в разработке.") 