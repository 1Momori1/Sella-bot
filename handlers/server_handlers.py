import os
import sys
import psutil
import asyncio
import subprocess
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус бота и системы"""
    try:
        # Получаем информацию о процессе бота
        current_pid = os.getpid()
        process = psutil.Process(current_pid)
        
        # Системная информация
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Время работы бота
        uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
        uptime_str = f"{uptime.days}д {uptime.seconds // 3600}ч {(uptime.seconds % 3600) // 60}м"
        
        # Статус бота
        bot_status = "🟢 Работает" if process.is_running() else "🔴 Остановлен"
        
        status_text = f"""
🤖 **СТАТУС БОТА**

**Бот:** {bot_status}
**PID:** {current_pid}
**Время работы:** {uptime_str}
**Использование памяти:** {process.memory_info().rss / 1024 / 1024:.1f} МБ

🖥️ **СИСТЕМА**
**CPU:** {cpu_percent:.1f}%
**Память:** {memory.percent:.1f}%
**Диск:** {disk.percent:.1f}%
**Версия Python:** {sys.version.split()[0]}
        """
        
        # Создаем кнопки управления
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Перезапустить бота", callback_data="server_restart")],
            [InlineKeyboardButton("📊 Процессы Python", callback_data="server_processes")],
            [InlineKeyboardButton("💾 Создать бэкап", callback_data="server_backup")],
            [InlineKeyboardButton("🔄 Обновить статус", callback_data="server_status")]
        ])
        
        await update.message.reply_text(
            status_text.strip(),
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статуса: {str(e)}")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапустить бота"""
    query = update.callback_query
    
    try:
        await query.answer("🔄 Перезапуск бота...")
        
        # Создаем кнопку для подтверждения
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

async def confirm_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        asyncio.create_task(perform_restart())
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def perform_restart():
    """Выполнить перезапуск бота"""
    try:
        # Ждем немного, чтобы сообщение отправилось
        await asyncio.sleep(2)
        
        # Перезапускаем процесс
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    except Exception as e:
        print(f"Ошибка перезапуска: {e}")

async def show_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать процессы Python"""
    query = update.callback_query
    
    try:
        await query.answer("📊 Получение процессов...")
        
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

async def create_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать резервную копию данных"""
    query = update.callback_query
    
    try:
        await query.answer("💾 Создание бэкапа...")
        
        # Создаем папку для бэкапов если её нет
        backup_dir = "storage/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Имя файла бэкапа
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Создаем архив
        import tarfile
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