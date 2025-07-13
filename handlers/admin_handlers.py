import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Показать список пользователей"""
    user_id = update.effective_user.id
    
    if not role_manager:
        await update.message.reply_text("❌ Модуль ролей не инициализирован.")
        return
    
    # Проверяем права администратора
    if not await role_manager.check_permission(user_id, "admin", "view"):
        await update.message.reply_text("❌ У вас нет прав для просмотра пользователей.")
        return
    
    try:
        users = await role_manager.list_users(user_id)
        
        if users:
            users_text = "👥 **Список пользователей**\n\n"
            
            for i, user in enumerate(users, 1):
                last_seen = user.get('last_seen', 'Никогда')
                if isinstance(last_seen, str) and last_seen != 'Никогда':
                    try:
                        last_seen = datetime.fromisoformat(last_seen).strftime("%d.%m.%Y %H:%M")
                    except:
                        pass
                
                users_text += f"{i}. **{user['name']}** (ID: {user['id']})\n"
                users_text += f"   Роль: {user['role']}\n"
                users_text += f"   Последний раз: {last_seen}\n\n"
            
            # Создаем кнопки управления
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")],
                [InlineKeyboardButton("✏️ Изменить права", callback_data="admin_edit_permissions")],
                [InlineKeyboardButton("🗑️ Удалить пользователя", callback_data="admin_delete_user")],
                [InlineKeyboardButton("🔄 Обновить список", callback_data="admin_users")]
            ])
            
            await update.message.reply_text(
                users_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("👥 Пользователи не найдены.")
            
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        await update.message.reply_text("❌ Ошибка получения списка пользователей.")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Добавить нового пользователя"""
    query = update.callback_query
    
    if not role_manager:
        await query.answer("❌ Модуль ролей не инициализирован.")
        return
    
    # Проверяем права администратора
    if not await role_manager.check_permission(query.from_user.id, "admin", "manage"):
        await query.answer("❌ У вас нет прав для добавления пользователей.")
        return
    
    try:
        await query.answer("➕ Добавление пользователя...")
        
        # Создаем форму для добавления пользователя
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Ввести ID пользователя", callback_data="admin_add_user_id")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
        ])
        
        await query.edit_message_text(
            "➕ **Добавление пользователя**\n\n"
            "Для добавления нового пользователя:\n"
            "1. Попросите пользователя отправить боту команду /start\n"
            "2. Скопируйте его Telegram ID\n"
            "3. Введите ID и выберите роль\n\n"
            "Или нажмите кнопку ниже для ввода ID:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def show_add_user_form(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Показать форму добавления пользователя"""
    query = update.callback_query
    
    try:
        await query.answer("📝 Форма добавления...")
        
        # Сохраняем состояние в контексте
        context.user_data['adding_user'] = True
        
        # Создаем кнопки с ролями
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Пользователь", callback_data="admin_role_user")],
            [InlineKeyboardButton("🔧 Модератор", callback_data="admin_role_moderator")],
            [InlineKeyboardButton("👑 Администратор", callback_data="admin_role_admin")],
            [InlineKeyboardButton("❌ Отмена", callback_data="admin_users")]
        ])
        
        await query.edit_message_text(
            "📝 **Добавление пользователя**\n\n"
            "Отправьте мне Telegram ID пользователя в следующем сообщении.\n"
            "Затем выберите роль для нового пользователя.\n\n"
            "**Как получить Telegram ID:**\n"
            "1. Попросите пользователя написать боту @userinfobot\n"
            "2. Скопируйте его ID из ответа\n"
            "3. Отправьте ID мне",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def handle_user_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Обработать ввод ID пользователя"""
    if not context.user_data.get('adding_user'):
        return
    
    try:
        user_id_text = update.message.text.strip()
        
        # Проверяем, что это число
        try:
            user_id = int(user_id_text)
        except ValueError:
            await update.message.reply_text(
                "❌ **Ошибка!**\n\n"
                "ID пользователя должен быть числом.\n"
                "Попробуйте еще раз или нажмите 'Отмена' в меню.",
                parse_mode='Markdown'
            )
            return
        
        # Сохраняем ID в контексте
        context.user_data['new_user_id'] = user_id
        
        # Создаем кнопки для выбора роли
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Пользователь", callback_data="admin_role_user")],
            [InlineKeyboardButton("🔧 Модератор", callback_data="admin_role_moderator")],
            [InlineKeyboardButton("👑 Администратор", callback_data="admin_role_admin")],
            [InlineKeyboardButton("❌ Отмена", callback_data="admin_users")]
        ])
        
        await update.message.reply_text(
            f"✅ **ID пользователя принят:** {user_id}\n\n"
            "Теперь выберите роль для нового пользователя:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка обработки ID: {str(e)}")

async def set_user_role(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Установить роль для нового пользователя"""
    query = update.callback_query
    
    if not role_manager:
        await query.answer("❌ Модуль ролей не инициализирован.")
        return
    
    try:
        # Получаем роль из callback_data
        role = query.data.replace("admin_role_", "")
        role_names = {
            "user": "Пользователь",
            "moderator": "Модератор", 
            "admin": "Администратор"
        }
        
        # Получаем ID пользователя из контекста
        user_id = context.user_data.get('new_user_id')
        if not user_id:
            await query.answer("❌ ID пользователя не найден. Попробуйте еще раз.")
            return
        
        # Добавляем пользователя
        success = await role_manager.add_user(
            user_id=user_id,
            name=f"Пользователь {user_id}",
            role=role,
            added_by=query.from_user.id
        )
        
        if success:
            await query.answer(f"✅ Пользователь добавлен с ролью '{role_names[role]}'")
            
            # Очищаем контекст
            context.user_data.pop('adding_user', None)
            context.user_data.pop('new_user_id', None)
            
            # Возвращаемся к списку пользователей
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")],
                [InlineKeyboardButton("🔄 Обновить список", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                f"✅ **Пользователь добавлен!**\n\n"
                f"**ID:** {user_id}\n"
                f"**Роль:** {role_names[role]}\n\n"
                f"Пользователь может теперь использовать бота.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ Ошибка добавления пользователя")
            
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Удалить пользователя"""
    query = update.callback_query
    
    if not role_manager:
        await query.answer("❌ Модуль ролей не инициализирован.")
        return
    
    # Проверяем права администратора
    if not await role_manager.check_permission(query.from_user.id, "admin", "manage"):
        await query.answer("❌ У вас нет прав для удаления пользователей.")
        return
    
    try:
        await query.answer("🗑️ Удаление пользователя...")
        
        # Получаем список пользователей для выбора
        users = await role_manager.list_users(query.from_user.id)
        
        if not users:
            await query.edit_message_text(
                "❌ Нет пользователей для удаления.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
                ])
            )
            return
        
        # Создаем кнопки с пользователями
        keyboard = []
        for user in users:
            if user['id'] != query.from_user.id:  # Нельзя удалить себя
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑️ {user['name']} ({user['role']})", 
                        callback_data=f"admin_delete_confirm_{user['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")])
        
        await query.edit_message_text(
            "🗑️ **Удаление пользователя**\n\n"
            "Выберите пользователя для удаления:\n"
            "(Вы не можете удалить себя)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Подтвердить удаление пользователя"""
    query = update.callback_query
    
    try:
        # Получаем ID пользователя из callback_data
        user_id = int(query.data.replace("admin_delete_confirm_", ""))
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        
        if not user_info:
            await query.answer("❌ Пользователь не найден")
            return
        
        # Создаем кнопки подтверждения
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_delete_final_{user_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="admin_delete_user")]
        ])
        
        await query.edit_message_text(
            f"⚠️ **Подтверждение удаления**\n\n"
            f"Вы действительно хотите удалить пользователя:\n"
            f"**{user_info['name']}** (ID: {user_id})\n"
            f"Роль: {user_info['role']}\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def final_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Выполнить удаление пользователя"""
    query = update.callback_query
    
    try:
        # Получаем ID пользователя из callback_data
        user_id = int(query.data.replace("admin_delete_final_", ""))
        
        # Удаляем пользователя
        success = await role_manager.remove_user(user_id, query.from_user.id)
        
        if success:
            await query.answer("✅ Пользователь удален")
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить список", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                f"✅ **Пользователь удален!**\n\n"
                f"Пользователь с ID {user_id} был удален из системы.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ Ошибка удаления пользователя")
            
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Показать логи бота"""
    query = update.callback_query
    
    if not role_manager:
        await query.answer("❌ Модуль ролей не инициализирован.")
        return
    
    # Проверяем права администратора
    if not await role_manager.check_permission(query.from_user.id, "admin", "view"):
        await query.answer("❌ У вас нет прав для просмотра логов.")
        return
    
    try:
        await query.answer("📋 Получение логов...")
        
        # Читаем последние строки из лог файла
        log_file = "logs/sella_bot.log"
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-20:] if len(lines) > 20 else lines  # Последние 20 строк
                log_content = ''.join(last_lines)
        except FileNotFoundError:
            log_content = "Лог файл не найден."
        except Exception as e:
            log_content = f"Ошибка чтения лога: {str(e)}"
        
        # Создаем кнопки
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить логи", callback_data="admin_logs")],
            [InlineKeyboardButton("📁 Полный лог", callback_data="admin_full_log")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_users")]
        ])
        
        await query.edit_message_text(
            f"📋 **Последние логи бота**\n\n"
            f"```\n{log_content[-3000:]}\n```\n\n"
            f"Показано последних {len(last_lines) if 'last_lines' in locals() else 0} строк",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}")

async def show_full_log(update: Update, context: ContextTypes.DEFAULT_TYPE, role_manager=None):
    """Показать полный лог"""
    query = update.callback_query
    
    try:
        await query.answer("📁 Получение полного лога...")
        
        # Читаем весь лог файл
        log_file = "logs/sella_bot.log"
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except FileNotFoundError:
            log_content = "Лог файл не найден."
        except Exception as e:
            log_content = f"Ошибка чтения лога: {str(e)}"
        
        # Если лог слишком большой, отправляем как файл
        if len(log_content) > 4000:
            # Создаем временный файл
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
                f.write(log_content)
                temp_file = f.name
            
            # Отправляем файл
            with open(temp_file, 'rb') as f:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=f,
                    filename="sella_bot_full.log",
                    caption="📁 Полный лог бота"
                )
            
            # Удаляем временный файл
            import os
            os.unlink(temp_file)
            
            await query.answer("📁 Полный лог отправлен в чат")
        else:
            # Показываем в сообщении
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_logs")]
            ])
            
            await query.edit_message_text(
                f"📁 **Полный лог бота**\n\n"
                f"```\n{log_content}\n```",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}") 