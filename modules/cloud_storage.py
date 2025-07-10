import os
import shutil
import hashlib
import json
import logging
import aiofiles
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

class CloudStorage:
    """Модуль облачного хранилища"""
    
    def __init__(self, config: dict, role_manager):
        self.config = config.get("storage", {})
        self.role_manager = role_manager
        self.logger = logging.getLogger(__name__)
        
        # Пути к директориям
        self.storage_path = Path(self.config.get("path", "storage/"))
        self.uploads_path = self.storage_path / "uploads"
        self.downloads_path = self.storage_path / "downloads"
        self.temp_path = self.storage_path / "temp"
        
        # Создание директорий если не существуют
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Настройки
        self.max_files_per_user = self.config.get("max_files_per_user", 1000)
        self.max_file_size = self.config.get("max_file_size", 52428800)  # 50MB
        self.allowed_extensions = self.config.get("allowed_extensions", [])
        
        # Файл с метаданными
        self.metadata_file = self.storage_path / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Загрузка метаданных файлов"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки метаданных: {e}")
        return {"files": {}, "users": {}}
    
    def _save_metadata(self):
        """Сохранение метаданных файлов"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метаданных: {e}")
    
    async def upload_file(self, file_path: str, user_id: int, original_filename: str = None) -> Dict[str, Any]:
        """Загрузка файла в хранилище"""
        if not await self.role_manager.check_permission(user_id, "storage", "upload"):
            return {"success": False, "message": "❌ Нет прав для загрузки файлов"}
        
        try:
            # Проверка размера файла
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {"success": False, "message": f"❌ Файл слишком большой ({file_size} байт). Максимум: {self.max_file_size} байт"}
            
            # Проверка расширения
            file_ext = Path(original_filename or file_path).suffix.lower().lstrip('.')
            if self.allowed_extensions and file_ext not in self.allowed_extensions:
                return {"success": False, "message": f"❌ Расширение .{file_ext} не разрешено"}
            
            # Проверка лимита файлов пользователя
            user_files = await self.get_user_files(user_id)
            if len(user_files) >= self.max_files_per_user:
                return {"success": False, "message": f"❌ Достигнут лимит файлов ({self.max_files_per_user})"}
            
            # Генерация уникального имени файла
            file_hash = hashlib.md5(f"{user_id}_{original_filename}_{datetime.now().isoformat()}".encode()).hexdigest()
            file_ext = Path(original_filename or file_path).suffix
            storage_filename = f"{file_hash}{file_ext}"
            storage_path = self.uploads_path / storage_filename
            
            # Копирование файла
            shutil.copy2(file_path, storage_path)
            
            # Сохранение метаданных
            file_id = file_hash
            self.metadata["files"][file_id] = {
                "filename": original_filename or os.path.basename(file_path),
                "storage_filename": storage_filename,
                "user_id": user_id,
                "size": file_size,
                "extension": file_ext,
                "upload_time": datetime.now().isoformat(),
                "path": str(storage_path)
            }
            
            # Обновление статистики пользователя
            user_id_str = str(user_id)
            if user_id_str not in self.metadata["users"]:
                self.metadata["users"][user_id_str] = {"files": [], "total_size": 0}
            
            self.metadata["users"][user_id_str]["files"].append(file_id)
            self.metadata["users"][user_id_str]["total_size"] += file_size
            
            self._save_metadata()
            
            self.logger.info(f"Файл {original_filename} загружен пользователем {user_id} (ID: {file_id})")
            return {
                "success": True,
                "message": f"✅ Файл {original_filename} успешно загружен",
                "file_id": file_id,
                "size": file_size
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла: {e}")
            return {"success": False, "message": f"❌ Ошибка загрузки файла: {str(e)}"}
    
    async def download_file(self, file_id: str, user_id: int) -> Optional[Tuple[str, str]]:
        """Скачивание файла из хранилища"""
        if not await self.role_manager.check_permission(user_id, "storage", "download"):
            return None
        
        try:
            if file_id not in self.metadata["files"]:
                return None
            
            file_info = self.metadata["files"][file_id]
            
            # Проверка прав доступа (пользователь может скачивать только свои файлы или админ)
            if file_info["user_id"] != user_id and not await self.role_manager.is_admin(user_id):
                return None
            
            file_path = file_info["path"]
            if not os.path.exists(file_path):
                return None
            
            return (file_path, file_info["filename"])
            
        except Exception as e:
            self.logger.error(f"Ошибка скачивания файла {file_id}: {e}")
            return None
    
    async def list_files(self, user_id: int, path: str = "/") -> List[Dict[str, Any]]:
        """Список файлов пользователя"""
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            return []
        
        try:
            files = []
            user_id_str = str(user_id)
            
            # Если админ - показываем все файлы
            if await self.role_manager.is_admin(user_id):
                for file_id, file_info in self.metadata["files"].items():
                    files.append({
                        "id": file_id,
                        "name": file_info["filename"],
                        "size": file_info["size"],
                        "extension": file_info["extension"],
                        "upload_time": file_info["upload_time"],
                        "owner": file_info["user_id"]
                    })
            else:
                # Показываем только файлы пользователя
                if user_id_str in self.metadata["users"]:
                    for file_id in self.metadata["users"][user_id_str]["files"]:
                        if file_id in self.metadata["files"]:
                            file_info = self.metadata["files"][file_id]
                            files.append({
                                "id": file_id,
                                "name": file_info["filename"],
                                "size": file_info["size"],
                                "extension": file_info["extension"],
                                "upload_time": file_info["upload_time"],
                                "owner": file_info["user_id"]
                            })
            
            # Сортировка по времени загрузки
            files.sort(key=lambda x: x["upload_time"], reverse=True)
            return files
            
        except Exception as e:
            self.logger.error(f"Ошибка получения списка файлов: {e}")
            return []
    
    async def delete_file(self, file_id: str, user_id: int) -> Dict[str, Any]:
        """Удаление файла"""
        if not await self.role_manager.check_permission(user_id, "storage", "delete"):
            return {"success": False, "message": "❌ Нет прав для удаления файлов"}
        
        try:
            if file_id not in self.metadata["files"]:
                return {"success": False, "message": "❌ Файл не найден"}
            
            file_info = self.metadata["files"][file_id]
            
            # Проверка прав доступа
            if file_info["user_id"] != user_id and not await self.role_manager.is_admin(user_id):
                return {"success": False, "message": "❌ Нет прав для удаления этого файла"}
            
            # Удаление физического файла
            file_path = file_info["path"]
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Обновление метаданных
            owner_id_str = str(file_info["user_id"])
            if owner_id_str in self.metadata["users"]:
                if file_id in self.metadata["users"][owner_id_str]["files"]:
                    self.metadata["users"][owner_id_str]["files"].remove(file_id)
                self.metadata["users"][owner_id_str]["total_size"] -= file_info["size"]
            
            del self.metadata["files"][file_id]
            self._save_metadata()
            
            self.logger.info(f"Файл {file_info['filename']} удален пользователем {user_id}")
            return {"success": True, "message": f"✅ Файл {file_info['filename']} успешно удален"}
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления файла {file_id}: {e}")
            return {"success": False, "message": f"❌ Ошибка удаления файла: {str(e)}"}
    
    async def get_file_info(self, file_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о файле"""
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            return None
        
        try:
            if file_id not in self.metadata["files"]:
                return None
            
            file_info = self.metadata["files"][file_id]
            
            # Проверка прав доступа
            if file_info["user_id"] != user_id and not await self.role_manager.is_admin(user_id):
                return None
            
            return {
                "id": file_id,
                "name": file_info["filename"],
                "size": file_info["size"],
                "size_formatted": self._format_file_size(file_info["size"]),
                "extension": file_info["extension"],
                "upload_time": file_info["upload_time"],
                "owner": file_info["user_id"]
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о файле {file_id}: {e}")
            return None
    
    async def search_files(self, query: str, user_id: int) -> List[Dict[str, Any]]:
        """Поиск файлов"""
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            return []
        
        try:
            files = await self.list_files(user_id)
            results = []
            
            query_lower = query.lower()
            for file_info in files:
                if query_lower in file_info["name"].lower():
                    results.append(file_info)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска файлов: {e}")
            return []
    
    async def get_storage_usage(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики использования хранилища"""
        if not await self.role_manager.check_permission(user_id, "storage", "view"):
            return {}
        
        try:
            user_id_str = str(user_id)
            
            if await self.role_manager.is_admin(user_id):
                # Статистика для админа - общая
                total_files = len(self.metadata["files"])
                total_size = sum(file_info["size"] for file_info in self.metadata["files"].values())
                total_users = len(self.metadata["users"])
                
                return {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_formatted": self._format_file_size(total_size),
                    "total_users": total_users,
                    "max_files_per_user": self.max_files_per_user,
                    "max_file_size": self.max_file_size,
                    "max_file_size_formatted": self._format_file_size(self.max_file_size)
                }
            else:
                # Статистика для пользователя
                if user_id_str in self.metadata["users"]:
                    user_data = self.metadata["users"][user_id_str]
                    return {
                        "files_count": len(user_data["files"]),
                        "total_size": user_data["total_size"],
                        "total_size_formatted": self._format_file_size(user_data["total_size"]),
                        "max_files": self.max_files_per_user,
                        "max_file_size": self.max_file_size,
                        "max_file_size_formatted": self._format_file_size(self.max_file_size)
                    }
                else:
                    return {
                        "files_count": 0,
                        "total_size": 0,
                        "total_size_formatted": "0 B",
                        "max_files": self.max_files_per_user,
                        "max_file_size": self.max_file_size,
                        "max_file_size_formatted": self._format_file_size(self.max_file_size)
                    }
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики хранилища: {e}")
            return {}
    
    async def get_user_files(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение файлов конкретного пользователя"""
        return await self.list_files(user_id)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}" 