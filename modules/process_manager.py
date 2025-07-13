import asyncio
import subprocess
import psutil
import logging
import os
import signal
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ProcessManager:
    """Модуль управления процессами для Termux"""
    
    def __init__(self, config: dict, role_manager):
        self.config = config.get("bots", {})
        self.role_manager = role_manager
        self.logger = logging.getLogger(__name__)
        self.processes = {}  # {bot_name: process_info}
        self.process_logs = {}  # {bot_name: [log_entries]}
        
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
                "auto_restart": bot_config.get("auto_restart", False),
                "last_error": status.get("last_error"),
                "restart_count": status.get("restart_count", 0)
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
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent', 'status']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline', [])
                    
                    # Проверка по имени скрипта
                    if any(script_name in cmd for cmd in cmdline if cmd):
                        uptime_seconds = int(time.time() - proc_info['create_time'])
                        uptime_str = self._format_uptime(uptime_seconds)
                        
                        # Получаем дополнительную информацию о процессе
                        proc_obj = psutil.Process(proc_info['pid'])
                        memory_info = proc_obj.memory_info()
                        
                        return {
                            "status": "running",
                            "pid": proc_info['pid'],
                            "uptime": uptime_str,
                            "memory_mb": round(memory_info.rss / (1024**2), 1),
                            "cpu_percent": round(proc_info['cpu_percent'], 1),
                            "status_detail": proc_info['status'],
                            "num_threads": proc_obj.num_threads(),
                            "num_fds": proc_obj.num_fds() if hasattr(proc_obj, 'num_fds') else None,
                            "connections": len(proc_obj.connections()) if hasattr(proc_obj, 'connections') else 0
                        }
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"status": "stopped", "pid": None, "uptime": "0", "memory_mb": 0, "cpu_percent": 0}
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса бота {bot_name}: {e}")
            return {"status": "error", "pid": None, "uptime": "0", "memory_mb": 0, "cpu_percent": 0, "last_error": str(e)}
    
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
            
            # Создание лог-файла для бота
            log_dir = "logs/bots"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{bot_name}.log")
            
            # Запуск в фоновом режиме с перенаправлением вывода
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    ["python", process_path],
                    stdout=log,
                    stderr=log,
                    cwd=os.path.dirname(process_path),
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                )
            
            # Сохранение информации о процессе
            self.processes[bot_name] = {
                "pid": process.pid,
                "start_time": datetime.now(),
                "started_by": user_id,
                "log_file": log_file,
                "restart_count": self.processes.get(bot_name, {}).get("restart_count", 0) + 1
            }
            
            # Логирование запуска
            await self._log_bot_event(bot_name, "started", user_id, process.pid)
            
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
                
                # Попытка graceful shutdown
                process.terminate()
                
                # Ждем завершения
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Принудительное завершение
                    try:
                        process.kill()
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        # Последняя попытка - SIGKILL
                        os.kill(pid, signal.SIGKILL)
                
                # Удаление из списка процессов
                if bot_name in self.processes:
                    del self.processes[bot_name]
                
                # Логирование остановки
                await self._log_bot_event(bot_name, "stopped", user_id, pid)
                
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
            await self._log_bot_event(bot_name, "restarted", user_id)
            return {"success": True, "message": f"✅ Бот {bot_name} успешно перезапущен"}
        else:
            return {"success": False, "message": f"❌ Ошибка перезапуска бота {bot_name}: {start_result['message']}"}
    
    async def get_bot_logs(self, bot_name: str, user_id: int, lines: int = 50) -> Optional[str]:
        """Получение логов бота"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return None
            
        try:
            log_file = f"logs/bots/{bot_name}.log"
            if not os.path.exists(log_file):
                return f"📝 Логи для бота {bot_name} не найдены"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Берем последние строки
            recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
            
            if not recent_logs:
                return f"📝 Логи для бота {bot_name} пусты"
            
            return f"📝 **Логи бота {bot_name}** (последние {len(recent_logs)} строк):\n\n```\n{''.join(recent_logs)}```"
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения логов бота {bot_name}: {e}")
            return f"❌ Ошибка чтения логов: {str(e)}"
    
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
            status_text += f"   📊 Статус: {bot['status']}\n"
            
            if bot["pid"]:
                status_text += f"   🔢 PID: {bot['pid']}\n"
                status_text += f"   ⏰ Время работы: {bot['uptime']}\n"
                status_text += f"   💾 Память: {bot['memory_mb']}MB\n"
                status_text += f"   📈 CPU: {bot['cpu_percent']}%\n"
            
            if bot["restart_count"] > 0:
                status_text += f"   🔄 Перезапусков: {bot['restart_count']}\n"
            
            if bot.get("last_error"):
                status_text += f"   ⚠️ Последняя ошибка: {bot['last_error'][:50]}...\n"
            
            status_text += f"   {auto_restart_emoji} Автоперезапуск: {'Включен' if bot['auto_restart'] else 'Отключен'}\n\n"
        
        return status_text
    
    async def get_all_processes(self, user_id: int, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Получение информации о всех процессах"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return None
            
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time', 'username']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                        proc_obj = psutil.Process(proc_info['pid'])
                        memory_info = proc_obj.memory_info()
                        
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': round(proc_info['cpu_percent'], 1),
                            'memory_percent': round(proc_info['memory_percent'], 1),
                            'memory_mb': round(memory_info.rss / (1024**2), 1),
                            'status': proc_info['status'],
                            'username': proc_info.get('username', 'unknown'),
                            'create_time': datetime.fromtimestamp(proc_info['create_time']).strftime('%H:%M:%S'),
                            'num_threads': proc_obj.num_threads(),
                            'connections': len(proc_obj.connections()) if hasattr(proc_obj, 'connections') else 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортируем по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о процессах: {e}")
            return None
    
    async def kill_process(self, user_id: int, pid: int) -> bool:
        """Завершение процесса"""
        if not await self.role_manager.check_permission(user_id, "processes", "manage"):
            return False
            
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                process.kill()
            
            self.logger.info(f"Процесс {pid} завершен пользователем {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения процесса {pid}: {e}")
            return False
    
    async def _log_bot_event(self, bot_name: str, event: str, user_id: int, pid: Optional[int] = None):
        """Логирование событий бота"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "bot_name": bot_name,
                "event": event,
                "user_id": user_id,
                "pid": pid
            }
            
            if bot_name not in self.process_logs:
                self.process_logs[bot_name] = []
            
            self.process_logs[bot_name].append(log_entry)
            
            # Ограничиваем количество записей
            if len(self.process_logs[bot_name]) > 100:
                self.process_logs[bot_name] = self.process_logs[bot_name][-50:]
            
            # Сохраняем в файл
            log_file = f"logs/bot_events.json"
            os.makedirs("logs", exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.process_logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Ошибка логирования события бота: {e}")
    
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
    
    async def get_system_processes_summary(self, user_id: int) -> str:
        """Получение сводки по процессам системы"""
        if not await self.role_manager.check_permission(user_id, "processes", "view"):
            return "❌ Нет доступа к информации о процессах"
        
        try:
            total_processes = len(psutil.pids())
            running_processes = 0
            sleeping_processes = 0
            stopped_processes = 0
            
            for proc in psutil.process_iter(['status']):
                try:
                    status = proc.info['status']
                    if status == 'running':
                        running_processes += 1
                    elif status == 'sleeping':
                        sleeping_processes += 1
                    elif status == 'stopped':
                        stopped_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            summary = f"""📊 **Сводка процессов системы**

🔢 Всего процессов: {total_processes}
🟢 Запущено: {running_processes}
😴 Спящих: {sleeping_processes}
⏸️ Остановлено: {stopped_processes}

💾 Использование памяти процессами:
   📈 Топ-5 по памяти:"""
            
            # Топ-5 процессов по памяти
            memory_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    proc_info = proc.info
                    memory_mb = round(proc_info['memory_info'].rss / (1024**2), 1)
                    memory_processes.append({
                        'name': proc_info['name'],
                        'pid': proc_info['pid'],
                        'memory_mb': memory_mb
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            memory_processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            for i, proc in enumerate(memory_processes[:5], 1):
                summary += f"\n   {i}. {proc['name']} (PID: {proc['pid']}): {proc['memory_mb']}MB"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки процессов: {e}")
            return f"❌ Ошибка получения сводки процессов: {str(e)}" 