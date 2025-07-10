import asyncio
import subprocess
import psutil
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

class ProcessManager:
    """Модуль управления процессами"""
    
    def __init__(self, config: dict, role_manager):
        self.config = config.get("bots", {})
        self.role_manager = role_manager
        self.logger = logging.getLogger(__name__)
        self.processes = {}  # {bot_name: process_info}
        
    async def get_bots_status(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Получение статуса всех ботов"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return None
            
        bots_status = []
        
        for bot_name, bot_config in self.config.items():
            if not bot_config.get("enabled", True):
                continue
                
            status = await self._get_bot_status(bot_name, bot_config)
            bots_status.append({
                "name": bot_name,
                "display_name": bot_config.get("name", bot_name),
                "status": status["status"],
                "pid": status["pid"],
                "uptime": status["uptime"],
                "memory_mb": status["memory_mb"],
                "cpu_percent": status["cpu_percent"],
                "path": bot_config.get("path", ""),
                "auto_restart": bot_config.get("auto_restart", False)
            })
            
        return bots_status
    
    async def _get_bot_status(self, bot_name: str, bot_config: dict) -> Dict[str, Any]:
        """Получение статуса конкретного бота"""
        try:
            # Поиск процесса по имени файла
            process_path = bot_config.get("path", "")
            if not process_path:
                return {"status": "unknown", "pid": None, "uptime": "0", "memory_mb": 0, "cpu_percent": 0}
            
            script_name = os.path.basename(process_path)
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline', [])
                    
                    # Проверка по имени скрипта
                    if any(script_name in cmd for cmd in cmdline if cmd):
                        uptime_seconds = int(time.time() - proc_info['create_time'])
                        uptime_str = self._format_uptime(uptime_seconds)
                        
                        return {
                            "status": "running",
                            "pid": proc_info['pid'],
                            "uptime": uptime_str,
                            "memory_mb": round(proc_info['memory_info'].rss / (1024**2), 1),
                            "cpu_percent": round(proc_info['cpu_percent'], 1)
                        }
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"status": "stopped", "pid": None, "uptime": "0", "memory_mb": 0, "cpu_percent": 0}
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса бота {bot_name}: {e}")
            return {"status": "error", "pid": None, "uptime": "0", "memory_mb": 0, "cpu_percent": 0}
    
    async def start_bot(self, bot_name: str, user_id: int) -> Dict[str, Any]:
        """Запуск бота"""
        if not await self.role_manager.check_permission(user_id, "processes", "manage"):
            return {"success": False, "message": "❌ Нет прав для управления процессами"}
            
        if bot_name not in self.config:
            return {"success": False, "message": f"❌ Бот {bot_name} не найден в конфигурации"}
            
        bot_config = self.config[bot_name]
        if not bot_config.get("enabled", True):
            return {"success": False, "message": f"❌ Бот {bot_name} отключен в конфигурации"}
            
        try:
            # Проверка, не запущен ли уже
            current_status = await self._get_bot_status(bot_name, bot_config)
            if current_status["status"] == "running":
                return {"success": False, "message": f"✅ Бот {bot_name} уже запущен"}
            
            # Запуск процесса
            process_path = bot_config.get("path")
            if not process_path or not os.path.exists(process_path):
                return {"success": False, "message": f"❌ Файл {process_path} не найден"}
            
            # Запуск в фоновом режиме
            process = subprocess.Popen(
                ["python", process_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(process_path)
            )
            
            # Сохранение информации о процессе
            self.processes[bot_name] = {
                "pid": process.pid,
                "start_time": datetime.now(),
                "started_by": user_id
            }
            
            self.logger.info(f"Бот {bot_name} запущен пользователем {user_id} (PID: {process.pid})")
            return {"success": True, "message": f"✅ Бот {bot_name} успешно запущен (PID: {process.pid})"}
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска бота {bot_name}: {e}")
            return {"success": False, "message": f"❌ Ошибка запуска бота {bot_name}: {str(e)}"}
    
    async def stop_bot(self, bot_name: str, user_id: int) -> Dict[str, Any]:
        """Остановка бота"""
        if not await self.role_manager.check_permission(user_id, "processes", "manage"):
            return {"success": False, "message": "❌ Нет прав для управления процессами"}
            
        try:
            # Поиск процесса
            bot_config = self.config.get(bot_name, {})
            current_status = await self._get_bot_status(bot_name, bot_config)
            
            if current_status["status"] != "running":
                return {"success": False, "message": f"❌ Бот {bot_name} не запущен"}
            
            # Остановка процесса
            pid = current_status["pid"]
            if pid:
                process = psutil.Process(pid)
                process.terminate()
                
                # Ждем завершения
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    process.kill()  # Принудительное завершение
                
                # Удаление из списка процессов
                if bot_name in self.processes:
                    del self.processes[bot_name]
                
                self.logger.info(f"Бот {bot_name} остановлен пользователем {user_id}")
                return {"success": True, "message": f"✅ Бот {bot_name} успешно остановлен"}
            
            return {"success": False, "message": f"❌ Не удалось найти процесс бота {bot_name}"}
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки бота {bot_name}: {e}")
            return {"success": False, "message": f"❌ Ошибка остановки бота {bot_name}: {str(e)}"}
    
    async def restart_bot(self, bot_name: str, user_id: int) -> Dict[str, Any]:
        """Перезапуск бота"""
        if not await self.role_manager.check_permission(user_id, "processes", "restart"):
            return {"success": False, "message": "❌ Нет прав для перезапуска процессов"}
            
        # Сначала останавливаем
        stop_result = await self.stop_bot(bot_name, user_id)
        if not stop_result["success"] and "не запущен" not in stop_result["message"]:
            return stop_result
        
        # Ждем немного
        await asyncio.sleep(2)
        
        # Затем запускаем
        start_result = await self.start_bot(bot_name, user_id)
        if start_result["success"]:
            return {"success": True, "message": f"✅ Бот {bot_name} успешно перезапущен"}
        else:
            return {"success": False, "message": f"❌ Ошибка перезапуска бота {bot_name}: {start_result['message']}"}
    
    async def get_bots_status_text(self, user_id: int) -> str:
        """Получение статуса ботов в текстовом виде"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return "❌ Нет доступа к информации о процессах"
            
        bots_status = await self.get_bots_status(user_id)
        if not bots_status:
            return "❌ Ошибка получения статуса ботов"
        
        status_text = "🤖 **Статус ботов**\n\n"
        
        for bot in bots_status:
            status_emoji = "🟢" if bot["status"] == "running" else "🔴"
            auto_restart_emoji = "🔄" if bot["auto_restart"] else "⏹️"
            
            status_text += f"{status_emoji} **{bot['display_name']}**\n"
            status_text += f"   Статус: {bot['status']}\n"
            
            if bot["status"] == "running":
                status_text += f"   PID: {bot['pid']}\n"
                status_text += f"   Время работы: {bot['uptime']}\n"
                status_text += f"   RAM: {bot['memory_mb']}MB\n"
                status_text += f"   CPU: {bot['cpu_percent']}%\n"
            
            status_text += f"   Автоперезапуск: {auto_restart_emoji}\n\n"
        
        return status_text
    
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
    
    async def get_all_processes(self, user_id: int, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Получение списка всех процессов"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return None
            
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_info'].rss > 1024*1024:  # > 1MB
                        uptime_seconds = int(time.time() - proc_info['create_time'])
                        
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": round(proc_info['cpu_percent'], 1),
                            "memory_mb": round(proc_info['memory_info'].rss / (1024**2), 1),
                            "uptime": self._format_uptime(uptime_seconds)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортировка по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения списка процессов: {e}")
            return None 