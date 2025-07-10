import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class NotificationManager:
    """Модуль управления уведомлениями"""
    
    def __init__(self, config: dict, role_manager, bot):
        self.config = config.get("notifications", {})
        self.role_manager = role_manager
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
        # Настройки уведомлений
        self.enabled = self.config.get("enabled", True)
        self.cooldown = self.config.get("cooldown_seconds", 300)  # 5 минут
        self.alert_levels = self.config.get("alert_levels", ["warning", "critical"])
        self.last_notifications = {}  # {alert_type: timestamp}
        self.admin_ids = config.get("admin_ids", [])
        
    async def send_alert(self, alert_type: str, message: str, level: str = "warning", user_ids: Optional[List[int]] = None) -> bool:
        """Отправка алерта пользователям"""
        if not self.enabled:
            return False
            
        if level not in self.alert_levels:
            return False
        
        # Проверка cooldown
        if not await self._check_cooldown(alert_type):
            return False
        
        try:
            # Определение получателей
            if user_ids is None:
                # По умолчанию отправляем админам
                user_ids = self.admin_ids.copy()
                
                # Добавляем пользователей с правами на уведомления
                for user_id_str, user_data in self.role_manager.users.items():
                    user_id = int(user_id_str)
                    if await self.role_manager.check_permission(user_id, "notifications", "view"):
                        if user_id not in user_ids:
                            user_ids.append(user_id)
            else:
                user_ids = user_ids.copy()
                
            # Форматирование сообщения
            emoji = "🔴" if level == "critical" else "🟡"
            formatted_message = f"{emoji} **Алерт: {alert_type.upper()}**\n\n{message}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            # Отправка уведомлений
            success_count = 0
            if user_ids:
                for user_id in user_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=formatted_message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
                
                # Обновление времени последнего уведомления
                self.last_notifications[alert_type] = datetime.now()
                
                self.logger.info(f"Алерт {alert_type} отправлен {success_count} пользователям")
                return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки алерта {alert_type}: {e}")
            return False
    
    async def send_system_alert(self, system_info: Dict[str, Any], user_ids: Optional[List[int]] = None) -> bool:
        """Отправка системного алерта"""
        alerts = []
        
        # CPU alert
        if system_info["cpu"]["usage_percent"] > system_info["cpu"]["threshold"]:
            level = "critical" if system_info["cpu"]["usage_percent"] > 95 else "warning"
            alerts.append(f"CPU: {system_info['cpu']['usage_percent']}% (порог: {system_info['cpu']['threshold']}%)")
        
        # Memory alert
        if system_info["memory"]["usage_percent"] > system_info["memory"]["threshold"]:
            level = "critical" if system_info["memory"]["usage_percent"] > 95 else "warning"
            alerts.append(f"RAM: {system_info['memory']['usage_percent']}% (порог: {system_info['memory']['threshold']}%)")
        
        # Disk alert
        if system_info["disk"]["usage_percent"] > system_info["disk"]["threshold"]:
            level = "critical" if system_info["disk"]["usage_percent"] > 95 else "warning"
            alerts.append(f"Диск: {system_info['disk']['usage_percent']}% (порог: {system_info['disk']['threshold']}%)")
        
        # Temperature alert
        if system_info["temperature"]["current"] and system_info["temperature"]["current"] > system_info["temperature"]["threshold"]:
            level = "critical" if system_info["temperature"]["current"] > 60 else "warning"
            alerts.append(f"Температура: {system_info['temperature']['current']}°C (порог: {system_info['temperature']['threshold']}°C)")
        
        if alerts:
            message = "\n".join(alerts)
            return await self.send_alert("system", message, level, user_ids)
        
        return False
    
    async def send_bot_status_alert(self, bot_name: str, status: str, user_ids: Optional[List[int]] = None) -> bool:
        """Отправка алерта о статусе бота"""
        if status == "stopped":
            message = f"Бот {bot_name} остановлен"
            return await self.send_alert("bot_status", message, "warning", user_ids)
        elif status == "error":
            message = f"Ошибка в работе бота {bot_name}"
            return await self.send_alert("bot_status", message, "critical", user_ids)
        
        return False
    
    async def send_storage_alert(self, user_id: int, message: str, level: str = "warning") -> bool:
        """Отправка алерта о хранилище"""
        return await self.send_alert("storage", message, level, [user_id])
    
    async def send_custom_notification(self, message: str, user_ids: Optional[List[int]] = None, level: str = "info") -> bool:
        """Отправка кастомного уведомления"""
        if user_ids is None:
            user_ids = self.admin_ids.copy()
        
        try:
            emoji = "ℹ️" if level == "info" else "⚠️" if level == "warning" else "🔴"
            formatted_message = f"{emoji} **Уведомление**\n\n{message}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            success_count = 0
            if user_ids:
                for user_id in user_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=formatted_message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
                
                return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки кастомного уведомления: {e}")
            return False
    
    async def _check_cooldown(self, alert_type: str) -> bool:
        """Проверка cooldown для уведомлений"""
        if alert_type not in self.last_notifications:
            return True
        
        last_time = self.last_notifications[alert_type]
        if datetime.now() - last_time < timedelta(seconds=self.cooldown):
            return False
        
        return True
    
    async def get_notification_settings(self, user_id: int) -> Dict[str, Any]:
        """Получение настроек уведомлений пользователя"""
        if not await self.role_manager.check_permission(user_id, "notifications", "view"):
            return {}
        
        return {
            "enabled": self.enabled,
            "cooldown_seconds": self.cooldown,
            "alert_levels": self.alert_levels,
            "can_manage": await self.role_manager.check_permission(user_id, "notifications", "manage")
        }
    
    async def update_notification_settings(self, settings: Dict[str, Any], user_id: int) -> bool:
        """Обновление настроек уведомлений (только админы)"""
        if not await self.role_manager.is_admin(user_id):
            return False
        
        try:
            if "enabled" in settings:
                self.enabled = settings["enabled"]
            
            if "cooldown" in settings:
                self.cooldown = settings["cooldown"]
            
            if "alert_levels" in settings:
                self.alert_levels = settings["alert_levels"]
            
            # Обновление конфигурации
            self.config.update(settings)
            
            self.logger.info(f"Настройки уведомлений обновлены админом {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления настроек уведомлений: {e}")
            return False
    
    async def get_notification_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории уведомлений (только админы)"""
        if not await self.role_manager.is_admin(user_id):
            return []
        
        # В реальной реализации здесь была бы база данных
        # Пока возвращаем пустой список
        return []
    
    async def clear_notification_history(self, user_id: int) -> bool:
        """Очистка истории уведомлений (только админы)"""
        if not await self.role_manager.is_admin(user_id):
            return False
        
        try:
            self.last_notifications.clear()
            self.logger.info(f"История уведомлений очищена админом {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка очистки истории уведомлений: {e}")
            return False 