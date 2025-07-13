import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class CloudStorage:
    """Облачное хранилище для работы на телефоне через Termux"""
    
    def __init__(self, storage_path: str = "storage", max_file_size: int = 50 * 1024 * 1024, max_total_size: int = 1024 * 1024 * 1024):
        self.storage_path = storage_path
        self.metadata_file = os.path.join(storage_path, "metadata.json")
        self.max_file_size = max_file_size  # 50MB по умолчанию
        self.max_total_size = max_total_size  # 1GB по умолчанию
        
        # Создаем структуру папок
        self.ensure_storage_exists()
        self.load_metadata()
    
    def ensure_storage_exists(self):
        """Создание структуры папок для хранения"""
        try:
            # Основная папка хранилища
            if not os.path.exists(self.storage_path):
                os.makedirs(self.storage_path)
                logger.info(f"Создана папка хранилища: {self.storage_path}")
            
            # Папка для временных файлов
            temp_path = os.path.join(self.storage_path, "temp")
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
            
            # Папка для общих файлов (для админов)
            shared_path = os.path.join(self.storage_path, "shared")
            if not os.path.exists(shared_path):
                os.makedirs(shared_path)
                
        except Exception as e:
            logger.error(f"Ошибка создания структуры хранилища: {e}")
    
    def load_metadata(self):
        """Загрузка метаданных файлов"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "files": {},
                    "users": {},
                    "statistics": {
                        "total_files": 0,
                        "total_size": 0,
                        "last_updated": datetime.now().isoformat()
                    }
                }
                self.save_metadata()
        except Exception as e:
            logger.error(f"Ошибка загрузки метаданных: {e}")
            self.metadata = {"files": {}, "users": {}, "statistics": {"total_files": 0, "total_size": 0}}
    
    def save_metadata(self):
        """Сохранение метаданных файлов"""
        try:
            self.metadata["statistics"]["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")
    
    def get_user_storage_path(self, user_id: int) -> str:
        """Получение пути к папке пользователя"""
        return os.path.join(self.storage_path, str(user_id))
    
    def ensure_user_storage_exists(self, user_id: int):
        """Создание папки пользователя"""
        user_path = self.get_user_storage_path(user_id)
        if not os.path.exists(user_path):
            os.makedirs(user_path)
            logger.info(f"Создана папка пользователя {user_id}: {user_path}")
    
    def generate_file_id(self, user_id: int, filename: str) -> str:
        """Генерация уникального ID файла"""
        timestamp = datetime.now().isoformat()
        content = f"{user_id}_{filename}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def format_file_size(self, size_bytes: int) -> str:
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def get_file_extension(self, filename: str) -> str:
        """Получение расширения файла"""
        return os.path.splitext(filename)[1].lower()
    
    def is_allowed_file_type(self, filename: str) -> bool:
        """Проверка разрешенного типа файла"""
        # Список запрещенных расширений
        forbidden_extensions = {'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js'}
        extension = self.get_file_extension(filename)
        return extension not in forbidden_extensions
    
    async def check_storage_limits(self, user_id: int, file_size: int) -> Dict[str, Any]:
        """Проверка лимитов хранилища"""
        try:
            # Проверка размера файла
            if file_size > self.max_file_size:
                return {
                    "allowed": False,
                    "message": f"Файл слишком большой. Максимум: {self.format_file_size(self.max_file_size)}"
                }
            
            # Получаем статистику пользователя
            user_stats = await self.get_storage_usage(user_id)
            total_size = user_stats["total_size"] + file_size
            
            # Проверка общего размера
            if total_size > self.max_total_size:
                return {
                    "allowed": False,
                    "message": f"Превышен лимит хранилища. Максимум: {self.format_file_size(self.max_total_size)}"
                }
            
            return {"allowed": True, "message": "OK"}
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов: {e}")
            return {"allowed": False, "message": "Ошибка проверки лимитов"}
    
    async def save_file(self, user_id: int, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Сохранение файла в хранилище"""
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                return {"success": False, "message": "Файл не найден"}
            
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            
            # Проверяем лимиты
            limits_check = await self.check_storage_limits(user_id, file_size)
            if not limits_check["allowed"]:
                return {"success": False, "message": limits_check["message"]}
            
            # Проверяем тип файла
            if not self.is_allowed_file_type(original_filename):
                return {"success": False, "message": "Тип файла не разрешен"}
            
            # Создаем папку пользователя
            self.ensure_user_storage_exists(user_id)
            
            # Генерируем уникальное имя файла
            file_id = self.generate_file_id(user_id, original_filename)
            file_extension = self.get_file_extension(original_filename)
            storage_filename = f"{file_id}{file_extension}"
            
            # Путь для сохранения
            user_storage_path = self.get_user_storage_path(user_id)
            storage_file_path = os.path.join(user_storage_path, storage_filename)
            
            # Копируем файл
            shutil.copy2(file_path, storage_file_path)
            
            # Добавляем в метаданные
            file_info = {
                "id": file_id,
                "original_name": original_filename,
                "storage_name": storage_filename,
                "size": file_size,
                "size_formatted": self.format_file_size(file_size),
                "extension": file_extension,
                "user_id": user_id,
                "upload_time": datetime.now().isoformat(),
                "path": storage_file_path
            }
            
            self.metadata["files"][file_id] = file_info
            
            # Обновляем статистику пользователя
            if str(user_id) not in self.metadata["users"]:
                self.metadata["users"][str(user_id)] = {
                    "total_files": 0,
                    "total_size": 0,
                    "created_at": datetime.now().isoformat()
                }
            
            self.metadata["users"][str(user_id)]["total_files"] += 1
            self.metadata["users"][str(user_id)]["total_size"] += file_size
            
            # Обновляем общую статистику
            self.metadata["statistics"]["total_files"] += 1
            self.metadata["statistics"]["total_size"] += file_size
            
            # Сохраняем метаданные
            self.save_metadata()
            
            logger.info(f"Файл сохранен: {original_filename} -> {storage_filename}")
            
            return {
                "success": True,
                "message": "Файл успешно сохранен",
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            return {"success": False, "message": f"Ошибка сохранения: {str(e)}"}
    
    async def get_file_info(self, file_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о файле"""
        try:
            if file_id not in self.metadata["files"]:
                return None
            
            file_info = self.metadata["files"][file_id]
            
            # Проверяем права доступа
            if not await self.can_access_file(user_id, file_id):
                return None
            
            # Проверяем существование файла
            if not os.path.exists(file_info["path"]):
                return None
            
            return file_info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о файле: {e}")
            return None
    
    async def can_access_file(self, user_id: int, file_id: str) -> bool:
        """Проверка прав доступа к файлу"""
        try:
            if file_id not in self.metadata["files"]:
                return False
            
            file_info = self.metadata["files"][file_id]
            
            # Владелец файла может получить доступ
            if file_info["user_id"] == user_id:
                return True
            
            # Админы могут получить доступ ко всем файлам
            # (это будет проверяться в role_manager)
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки прав доступа: {e}")
            return False
    
    async def list_files(self, user_id: int, is_admin: bool = False) -> List[Dict[str, Any]]:
        """Получение списка файлов пользователя"""
        try:
            files = []
            
            for file_id, file_info in self.metadata["files"].items():
                # Проверяем права доступа
                if file_info["user_id"] == user_id or is_admin:
                    # Проверяем существование файла
                    if os.path.exists(file_info["path"]):
                        files.append(file_info)
                    else:
                        # Удаляем несуществующий файл из метаданных
                        await self.delete_file_metadata(file_id)
            
            # Сортируем по дате загрузки (новые сначала)
            files.sort(key=lambda x: x["upload_time"], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов: {e}")
            return []
    
    async def delete_file(self, file_id: str, user_id: int) -> Dict[str, Any]:
        """Удаление файла"""
        try:
            # Получаем информацию о файле
            file_info = await self.get_file_info(file_id, user_id)
            if not file_info:
                return {"success": False, "message": "Файл не найден или нет доступа"}
            
            # Удаляем физический файл
            if os.path.exists(file_info["path"]):
                os.remove(file_info["path"])
            
            # Удаляем из метаданных
            await self.delete_file_metadata(file_id)
            
            logger.info(f"Файл удален: {file_info['original_name']}")
            
            return {"success": True, "message": "Файл успешно удален"}
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
            return {"success": False, "message": f"Ошибка удаления: {str(e)}"}
    
    async def delete_file_metadata(self, file_id: str):
        """Удаление файла из метаданных"""
        try:
            if file_id in self.metadata["files"]:
                file_info = self.metadata["files"][file_id]
                user_id = file_info["user_id"]
                
                # Обновляем статистику пользователя
                if str(user_id) in self.metadata["users"]:
                    self.metadata["users"][str(user_id)]["total_files"] -= 1
                    self.metadata["users"][str(user_id)]["total_size"] -= file_info["size"]
                
                # Обновляем общую статистику
                self.metadata["statistics"]["total_files"] -= 1
                self.metadata["statistics"]["total_size"] -= file_info["size"]
                
                # Удаляем файл из метаданных
                del self.metadata["files"][file_id]
                
                # Сохраняем метаданные
                self.save_metadata()
                
        except Exception as e:
            logger.error(f"Ошибка удаления метаданных файла: {e}")
    
    async def search_files(self, user_id: int, query: str, is_admin: bool = False) -> List[Dict[str, Any]]:
        """Поиск файлов по имени"""
        try:
            all_files = await self.list_files(user_id, is_admin)
            query_lower = query.lower()
            
            # Фильтруем файлы по запросу
            matching_files = []
            for file_info in all_files:
                if query_lower in file_info["original_name"].lower():
                    matching_files.append(file_info)
            
            return matching_files
            
        except Exception as e:
            logger.error(f"Ошибка поиска файлов: {e}")
            return []
    
    async def get_storage_usage(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики использования хранилища"""
        try:
            if str(user_id) not in self.metadata["users"]:
                return {
                    "total_files": 0,
                    "total_size": 0,
                    "total_size_formatted": "0B",
                    "max_size": self.max_total_size,
                    "max_size_formatted": self.format_file_size(self.max_total_size),
                    "usage_percent": 0
                }
            
            user_stats = self.metadata["users"][str(user_id)]
            usage_percent = (user_stats["total_size"] / self.max_total_size) * 100
            
            return {
                "total_files": user_stats["total_files"],
                "total_size": user_stats["total_size"],
                "total_size_formatted": self.format_file_size(user_stats["total_size"]),
                "max_size": self.max_total_size,
                "max_size_formatted": self.format_file_size(self.max_total_size),
                "usage_percent": usage_percent
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики хранилища: {e}")
            return {
                "total_files": 0,
                "total_size": 0,
                "total_size_formatted": "0B",
                "max_size": self.max_total_size,
                "max_size_formatted": self.format_file_size(self.max_total_size),
                "usage_percent": 0
            }
    
    async def get_global_storage_stats(self) -> Dict[str, Any]:
        """Получение глобальной статистики хранилища"""
        try:
            stats = self.metadata["statistics"]
            return {
                "total_files": stats["total_files"],
                "total_size": stats["total_size"],
                "total_size_formatted": self.format_file_size(stats["total_size"]),
                "total_users": len(self.metadata["users"]),
                "last_updated": stats["last_updated"]
            }
        except Exception as e:
            logger.error(f"Ошибка получения глобальной статистики: {e}")
            return {"total_files": 0, "total_size": 0, "total_size_formatted": "0B"}
    
    def cleanup_temp_files(self):
        """Очистка временных файлов"""
        try:
            temp_path = os.path.join(self.storage_path, "temp")
            if os.path.exists(temp_path):
                for filename in os.listdir(temp_path):
                    file_path = os.path.join(temp_path, filename)
                    if os.path.isfile(file_path):
                        # Удаляем файлы старше 1 часа
                        if time.time() - os.path.getmtime(file_path) > 3600:
                            os.remove(file_path)
                            logger.info(f"Удален временный файл: {filename}")
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")
    
    async def validate_storage_integrity(self):
        """Проверка целостности хранилища"""
        try:
            files_to_remove = []
            
            for file_id, file_info in self.metadata["files"].items():
                if not os.path.exists(file_info["path"]):
                    files_to_remove.append(file_id)
                    logger.warning(f"Файл не найден: {file_info['original_name']}")
            
            # Удаляем несуществующие файлы
            for file_id in files_to_remove:
                await self.delete_file_metadata(file_id)
            
            logger.info(f"Проверка целостности завершена. Удалено {len(files_to_remove)} несуществующих файлов")
            
        except Exception as e:
            logger.error(f"Ошибка проверки целостности хранилища: {e}") 