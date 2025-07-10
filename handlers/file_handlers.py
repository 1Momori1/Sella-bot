import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional

logger = logging.getLogger(__name__)

class FileHandlers:
    """Обработчики файлов для облачного хранилища"""
    
    def __init__(self, cloud_storage, role_manager):
        self.cloud_storage = cloud_storage
        self.role_manager = role_manager
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного документа"""
        user_id = update.effective_user.id
        
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            await update.message.reply_text("❌ У вас нет прав для загрузки файлов")
            return
        
        try:
            # Получение информации о файле
            document = update.message.document
            file_name = document.file_name
            file_size = document.file_size
            
            # Проверка размера файла
            max_size = self.cloud_storage.max_file_size
            if file_size > max_size:
                await update.message.reply_text(
                    f"❌ Файл слишком большой ({file_size} байт). Максимальный размер: {max_size} байт"
                )
                return
            
            # Проверка расширения
            file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
            if self.cloud_storage.allowed_extensions and file_ext not in self.cloud_storage.allowed_extensions:
                await update.message.reply_text(f"❌ Расширение .{file_ext} не разрешено")
                return
            
            # Скачивание файла
            await update.message.reply_text("📥 Загружаю файл...")
            
            file = await context.bot.get_file(document.file_id)
            
            # Создание временного файла
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
                temp_path = temp_file.name
            
            # Скачивание во временный файл
            await file.download_to_drive(temp_path)
            
            # Загрузка в облачное хранилище
            result = await self.cloud_storage.upload_file(temp_path, user_id, file_name)
            
            # Удаление временного файла
            os.unlink(temp_path)
            
            if result["success"]:
                await update.message.reply_text(
                    f"✅ Файл **{file_name}** успешно загружен!\n"
                    f"📏 Размер: {result['size']} байт\n"
                    f"🆔 ID: `{result['file_id']}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ Ошибка загрузки: {result['message']}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке файла")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного фото"""
        user_id = update.effective_user.id
        
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            await update.message.reply_text("❌ У вас нет прав для загрузки файлов")
            return
        
        try:
            # Получение фото с максимальным размером
            photos = update.message.photo
            photo = photos[-1]  # Берем самое большое фото
            
            # Создание имени файла
            file_name = f"photo_{update.message.message_id}.jpg"
            
            # Проверка размера файла
            max_size = self.cloud_storage.max_file_size
            if photo.file_size > max_size:
                await update.message.reply_text(
                    f"❌ Фото слишком большое ({photo.file_size} байт). Максимальный размер: {max_size} байт"
                )
                return
            
            # Скачивание фото
            await update.message.reply_text("📥 Загружаю фото...")
            
            file = await context.bot.get_file(photo.file_id)
            
            # Создание временного файла
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_path = temp_file.name
            
            # Скачивание во временный файл
            await file.download_to_drive(temp_path)
            
            # Загрузка в облачное хранилище
            result = await self.cloud_storage.upload_file(temp_path, user_id, file_name)
            
            # Удаление временного файла
            os.unlink(temp_path)
            
            if result["success"]:
                await update.message.reply_text(
                    f"✅ Фото успешно загружено!\n"
                    f"📏 Размер: {result['size']} байт\n"
                    f"🆔 ID: `{result['file_id']}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ Ошибка загрузки: {result['message']}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке фото")
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного видео"""
        user_id = update.effective_user.id
        
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            await update.message.reply_text("❌ У вас нет прав для загрузки файлов")
            return
        
        try:
            video = update.message.video
            file_name = video.file_name or f"video_{update.message.message_id}.mp4"
            
            # Проверка размера файла
            max_size = self.cloud_storage.max_file_size
            if video.file_size > max_size:
                await update.message.reply_text(
                    f"❌ Видео слишком большое ({video.file_size} байт). Максимальный размер: {max_size} байт"
                )
                return
            
            # Скачивание видео
            await update.message.reply_text("📥 Загружаю видео...")
            
            file = await context.bot.get_file(video.file_id)
            
            # Создание временного файла
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_path = temp_file.name
            
            # Скачивание во временный файл
            await file.download_to_drive(temp_path)
            
            # Загрузка в облачное хранилище
            result = await self.cloud_storage.upload_file(temp_path, user_id, file_name)
            
            # Удаление временного файла
            os.unlink(temp_path)
            
            if result["success"]:
                await update.message.reply_text(
                    f"✅ Видео **{file_name}** успешно загружено!\n"
                    f"📏 Размер: {result['size']} байт\n"
                    f"🆔 ID: `{result['file_id']}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ Ошибка загрузки: {result['message']}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки видео: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке видео")
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного аудио"""
        user_id = update.effective_user.id
        
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            await update.message.reply_text("❌ У вас нет прав для загрузки файлов")
            return
        
        try:
            audio = update.message.audio
            file_name = audio.file_name or f"audio_{update.message.message_id}.mp3"
            
            # Проверка размера файла
            max_size = self.cloud_storage.max_file_size
            if audio.file_size > max_size:
                await update.message.reply_text(
                    f"❌ Аудио слишком большое ({audio.file_size} байт). Максимальный размер: {max_size} байт"
                )
                return
            
            # Скачивание аудио
            await update.message.reply_text("📥 Загружаю аудио...")
            
            file = await context.bot.get_file(audio.file_id)
            
            # Создание временного файла
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_path = temp_file.name
            
            # Скачивание во временный файл
            await file.download_to_drive(temp_path)
            
            # Загрузка в облачное хранилище
            result = await self.cloud_storage.upload_file(temp_path, user_id, file_name)
            
            # Удаление временного файла
            os.unlink(temp_path)
            
            if result["success"]:
                await update.message.reply_text(
                    f"✅ Аудио **{file_name}** успешно загружено!\n"
                    f"📏 Размер: {result['size']} байт\n"
                    f"🆔 ID: `{result['file_id']}`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ Ошибка загрузки: {result['message']}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки аудио: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке аудио")
    
    async def download_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
        """Скачивание файла из хранилища"""
        user_id = update.effective_user.id
        
        if not await self.role_manager.check_permission(user_id, "storage", "download"):
            await update.callback_query.answer("❌ У вас нет прав для скачивания файлов")
            return
        
        try:
            # Получение информации о файле
            file_info = await self.cloud_storage.get_file_info(file_id, user_id)
            if not file_info:
                await update.callback_query.answer("❌ Файл не найден")
                return
            
            # Скачивание файла
            file_data = await self.cloud_storage.download_file(file_id, user_id)
            if not file_data:
                await update.callback_query.answer("❌ Ошибка скачивания файла")
                return
            
            file_path, original_filename = file_data
            
            # Отправка файла пользователю
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename=original_filename,
                    caption=f"📥 Файл: {original_filename}"
                )
            
            await update.callback_query.answer("✅ Файл отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка скачивания файла: {e}")
            await update.callback_query.answer("❌ Ошибка при скачивании файла") 