import asyncio
import subprocess
import psutil
import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class MinecraftServer:
    """Модуль управления Minecraft сервером"""
    
    def __init__(self, config: dict, role_manager):
        self.config = config.get("minecraft", {})
        self.role_manager = role_manager
        self.logger = logging.getLogger(__name__)
        
        # Настройки сервера
        self.enabled = self.config.get("enabled", False)
        self.jar_path = self.config.get("jar_path", "")
        self.max_ram = self.config.get("max_ram", "2G")
        self.min_ram = self.config.get("min_ram", "1G")
        self.port = self.config.get("port", 25565)
        self.auto_restart = self.config.get("auto_restart", True)
        self.backup_enabled = self.config.get("backup_enabled", True)
        self.backup_interval = self.config.get("backup_interval", 3600)
        
        # Состояние сервера
        self.process = None
        self.start_time = None
        self.last_backup = None
        self.backup_path = "storage/minecraft_backups/"
        
        # Создание директории для бэкапов
        os.makedirs(self.backup_path, exist_ok=True)
    
    async def get_server_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение статуса Minecraft сервера"""
        if not await self.role_manager.check_permission(user_id, "server", "view"):
            return None
        
        if not self.enabled:
            return {"status": "disabled", "message": "Minecraft сервер отключен в конфигурации"}
        
        try:
            # Поиск процесса Minecraft сервера
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline', [])
                    
                    # Проверка по команде запуска
                    if any('java' in cmd and 'minecraft' in ' '.join(cmd).lower() for cmd in cmdline if cmd):
                        uptime_seconds = int(time.time() - proc_info['create_time'])
                        
                        return {
                            "status": "running",
                            "pid": proc_info['pid'],
                            "uptime": self._format_uptime(uptime_seconds),
                            "memory_mb": round(proc_info['memory_info'].rss / (1024**2), 1),
                            "cpu_percent": round(proc_info['cpu_percent'], 1),
                            "port": self.port,
                            "max_ram": self.max_ram,
                            "min_ram": self.min_ram
                        }
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"status": "stopped", "message": "Сервер не запущен"}
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса сервера: {e}")
            return {"status": "error", "message": f"Ошибка: {str(e)}"}
    
    async def start_server(self, user_id: int) -> Dict[str, Any]:
        """Запуск Minecraft сервера"""
        if not await self.role_manager.check_permission(user_id, "server", "manage"):
            return {"success": False, "message": "❌ Нет прав для управления сервером"}
        
        if not self.enabled:
            return {"success": False, "message": "❌ Minecraft сервер отключен в конфигурации"}
        
        try:
            # Проверка, не запущен ли уже
            current_status = await self.get_server_status(user_id)
            if current_status and current_status["status"] == "running":
                return {"success": False, "message": "✅ Сервер уже запущен"}
            
            # Проверка существования JAR файла
            if not self.jar_path or not os.path.exists(self.jar_path):
                return {"success": False, "message": f"❌ JAR файл не найден: {self.jar_path}"}
            
            # Команда запуска сервера
            cmd = [
                "java",
                f"-Xmx{self.max_ram}",
                f"-Xms{self.min_ram}",
                "-jar", self.jar_path,
                "nogui"
            ]
            
            # Запуск процесса
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(self.jar_path)
            )
            
            self.start_time = datetime.now()
            
            self.logger.info(f"Minecraft сервер запущен пользователем {user_id} (PID: {self.process.pid})")
            return {"success": True, "message": f"✅ Minecraft сервер запущен (PID: {self.process.pid})"}
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска сервера: {e}")
            return {"success": False, "message": f"❌ Ошибка запуска сервера: {str(e)}"}
    
    async def stop_server(self, user_id: int) -> Dict[str, Any]:
        """Остановка Minecraft сервера"""
        if not await self.role_manager.check_permission(user_id, "server", "manage"):
            return {"success": False, "message": "❌ Нет прав для управления сервером"}
        
        try:
            # Поиск процесса сервера
            current_status = await self.get_server_status(user_id)
            
            if not current_status or current_status["status"] != "running":
                return {"success": False, "message": "❌ Сервер не запущен"}
            
            # Остановка процесса
            pid = current_status["pid"]
            if pid:
                process = psutil.Process(pid)
                
                # Отправка команды остановки через RCON (если настроен)
                # await self.send_rcon_command("stop")
                
                # Ожидание корректного завершения
                try:
                    process.terminate()
                    process.wait(timeout=30)
                except psutil.TimeoutExpired:
                    process.kill()  # Принудительное завершение
                
                self.process = None
                self.start_time = None
                
                self.logger.info(f"Minecraft сервер остановлен пользователем {user_id}")
                return {"success": True, "message": "✅ Сервер остановлен"}
            
            return {"success": False, "message": "❌ Не удалось найти процесс сервера"}
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки сервера: {e}")
            return {"success": False, "message": f"❌ Ошибка остановки сервера: {str(e)}"}
    
    async def restart_server(self, user_id: int) -> Dict[str, Any]:
        """Перезапуск Minecraft сервера"""
        if not await self.role_manager.check_permission(user_id, "server", "manage"):
            return {"success": False, "message": "❌ Нет прав для управления сервером"}
        
        # Сначала останавливаем
        stop_result = await self.stop_server(user_id)
        if not stop_result["success"] and "не запущен" not in stop_result["message"]:
            return stop_result
        
        # Ждем немного
        await asyncio.sleep(5)
        
        # Затем запускаем
        start_result = await self.start_server(user_id)
        if start_result["success"]:
            return {"success": True, "message": "✅ Сервер успешно перезапущен"}
        else:
            return {"success": False, "message": f"❌ Ошибка перезапуска: {start_result['message']}"}
    
    async def create_backup(self, user_id: int) -> Dict[str, Any]:
        """Создание бэкапа сервера"""
        if not await self.role_manager.check_permission(user_id, "server", "backup"):
            return {"success": False, "message": "❌ Нет прав для создания бэкапов"}
        
        if not self.backup_enabled:
            return {"success": False, "message": "❌ Бэкапы отключены в конфигурации"}
        
        try:
            # Проверка статуса сервера
            server_status = await self.get_server_status(user_id)
            if not server_status or server_status["status"] != "running":
                return {"success": False, "message": "❌ Сервер должен быть запущен для создания бэкапа"}
            
            # Создание имени файла бэкапа
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"minecraft_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_path, backup_filename)
            
            # Команда создания бэкапа (пример)
            world_path = os.path.join(os.path.dirname(self.jar_path), "world")
            if os.path.exists(world_path):
                import zipfile
                
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(world_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, world_path)
                            zipf.write(file_path, arcname)
                
                self.last_backup = datetime.now()
                
                self.logger.info(f"Бэкап сервера создан пользователем {user_id}: {backup_filename}")
                return {"success": True, "message": f"✅ Бэкап создан: {backup_filename}"}
            else:
                return {"success": False, "message": "❌ Папка мира не найдена"}
                
        except Exception as e:
            self.logger.error(f"Ошибка создания бэкапа: {e}")
            return {"success": False, "message": f"❌ Ошибка создания бэкапа: {str(e)}"}
    
    async def get_server_info(self, user_id: int) -> str:
        """Получение информации о сервере в текстовом виде"""
        if not await self.role_manager.check_permission(user_id, "server", "view"):
            return "❌ Нет доступа к информации о сервере"
        
        if not self.enabled:
            return "⛏️ **Minecraft сервер**\n\n❌ Сервер отключен в конфигурации"
        
        server_status = await self.get_server_status(user_id)
        if not server_status:
            return "❌ Ошибка получения статуса сервера"
        
        info = f"""⛏️ **Minecraft сервер**

📊 **Статус**: {server_status['status']}
🔧 **Порт**: {self.port}
💾 **RAM**: {self.min_ram} - {self.max_ram}
🔄 **Автоперезапуск**: {'✅' if self.auto_restart else '❌'}
💾 **Бэкапы**: {'✅' if self.backup_enabled else '❌'}"""

        if server_status["status"] == "running":
            info += f"""
🆔 **PID**: {server_status['pid']}
⏰ **Время работы**: {server_status['uptime']}
💾 **Использование RAM**: {server_status['memory_mb']}MB
🖥️ **CPU**: {server_status['cpu_percent']}%"""

        if server_status["status"] == "error":
            info += f"\n❌ **Ошибка**: {server_status['message']}"
        
        return info
    
    async def get_players_list(self, user_id: int) -> Optional[List[str]]:
        """Получение списка игроков (заглушка)"""
        if not await self.role_manager.check_permission(user_id, "server", "view"):
            return None
        
        # В реальной реализации здесь был бы RCON запрос
        # Пока возвращаем заглушку
        return ["Игрок1", "Игрок2"]  # Пример
    
    def _format_uptime(self, seconds: int) -> str:
        """Форматирование времени работы"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    
    async def send_rcon_command(self, command: str) -> Optional[str]:
        """Отправка команды через RCON (заглушка)"""
        # В реальной реализации здесь был бы RCON клиент
        # Пока возвращаем заглушку
        self.logger.info(f"RCON команда: {command}")
        return "OK" 