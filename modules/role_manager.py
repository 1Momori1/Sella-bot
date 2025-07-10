import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

class RoleManager:
    """Модуль управления ролями и правами доступа"""
    
    def __init__(self, config: dict):
        self.users = config.get("users", {})
        self.admin_ids = config.get("admin_ids", [])
        self.logger = logging.getLogger(__name__)
        
    async def check_permission(self, user_id: int, module: str, action: str) -> bool:
        """Проверка прав пользователя на выполнение действия"""
        user_id_str = str(user_id)
        
        # Админы имеют все права
        if user_id in self.admin_ids:
            return True
            
        # Проверка существования пользователя
        if user_id_str not in self.users:
            self.logger.warning(f"Попытка доступа от неавторизованного пользователя {user_id}")
            return False
            
        user = self.users[user_id_str]
        permissions = user.get("permissions", {})
        
        # Проверка прав на модуль
        if module not in permissions:
            return False
            
        # Проверка конкретного действия
        if action in permissions[module]:
            return True
            
        # Проверка wildcard прав
        if "*" in permissions[module]:
            return True
            
        return False
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            return self.users[user_id_str]
        return None
    
    async def add_user(self, user_id: int, name: str, permissions: dict, admin_id: int) -> bool:
        """Добавление нового пользователя (только админы)"""
        if not await self.is_admin(admin_id):
            self.logger.warning(f"Попытка добавления пользователя от не-админа {admin_id}")
            return False
            
        user_id_str = str(user_id)
        self.users[user_id_str] = {
            "name": name,
            "role": "user",
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "created_by": admin_id
        }
        
        self.logger.info(f"Пользователь {user_id} ({name}) добавлен админом {admin_id}")
        return True
    
    async def remove_user(self, user_id: int, admin_id: int) -> bool:
        """Удаление пользователя (только админы)"""
        if not await self.is_admin(admin_id):
            self.logger.warning(f"Попытка удаления пользователя от не-админа {admin_id}")
            return False
            
        user_id_str = str(user_id)
        if user_id_str in self.users:
            user_name = self.users[user_id_str].get("name", "Unknown")
            del self.users[user_id_str]
            self.logger.info(f"Пользователь {user_id} ({user_name}) удален админом {admin_id}")
            return True
        return False
    
    async def update_permissions(self, user_id: int, permissions: dict, admin_id: int) -> bool:
        """Обновление прав пользователя (только админы)"""
        if not await self.is_admin(admin_id):
            self.logger.warning(f"Попытка изменения прав от не-админа {admin_id}")
            return False
            
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]["permissions"] = permissions
            self.users[user_id_str]["updated_at"] = datetime.now().isoformat()
            self.users[user_id_str]["updated_by"] = admin_id
            
            self.logger.info(f"Права пользователя {user_id} обновлены админом {admin_id}")
            return True
        return False
    
    async def list_users(self, admin_id: int) -> List[Dict[str, Any]]:
        """Список всех пользователей (только админы)"""
        if not await self.is_admin(admin_id):
            return []
            
        users_list = []
        for user_id, user_data in self.users.items():
            users_list.append({
                "id": user_id,
                "name": user_data.get("name", "Unknown"),
                "role": user_data.get("role", "user"),
                "permissions": user_data.get("permissions", {}),
                "created_at": user_data.get("created_at", "Unknown")
            })
        return users_list
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь админом"""
        return user_id in self.admin_ids
    
    async def get_user_menu(self, user_id: int) -> Dict[str, List[str]]:
        """Получение доступного меню для пользователя"""
        user_id_str = str(user_id)
        
        if user_id in self.admin_ids:
            # Админы видят все
            return {
                "system": ["view", "monitor", "settings"],
                "processes": ["view", "manage", "restart"],
                "server": ["view", "manage", "backup"],
                "storage": ["view", "upload", "download", "delete", "manage"],
                "notifications": ["view", "manage"],
                "admin": ["users", "roles", "logs", "config"]
            }
        
        if user_id_str not in self.users:
            return {}
            
        return self.users[user_id_str].get("permissions", {})
    
    async def save_config(self, config_path: str = "config.json") -> bool:
        """Сохранение конфигурации с обновленными пользователями"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config["users"] = self.users
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Конфигурация пользователей сохранена")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    async def get_user_role_name(self, user_id: int) -> str:
        """Получение названия роли пользователя"""
        user_info = await self.get_user_info(user_id)
        if user_info:
            return user_info.get("name", "Неизвестный")
        return "Неавторизованный" 