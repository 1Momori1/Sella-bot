import psutil
import logging
import asyncio
import platform
import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

class SystemMonitor:
    """Модуль системного мониторинга для Termux"""
    
    def __init__(self, config: dict, role_manager):
        self.config = config.get("system", {})
        self.monitoring_config = self.config.get("monitoring", {})
        self.role_manager = role_manager
        self.logger = logging.getLogger(__name__)
        self.last_check = None
        self.alerts = []
        
    async def get_system_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о системе"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return None
            
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk - используем текущую директорию
            try:
                disk = psutil.disk_usage('.')
            except:
                # Fallback на корневую директорию
                disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Расширенная информация о системе
            system_info_extended = await self._get_extended_system_info()
            
            # Temperature (улучшенное получение)
            temperature = await self._get_temperature_advanced()
            
            system_info = {
                "timestamp": datetime.now().isoformat(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                    "threshold": self.monitoring_config.get("cpu_threshold", 80),
                    "load_avg": await self._get_load_average()
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "threshold": self.monitoring_config.get("memory_threshold", 85),
                    "swap": await self._get_swap_info()
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "threshold": self.monitoring_config.get("disk_threshold", 90),
                    "io_stats": await self._get_disk_io_stats()
                },
                "network": {
                    "bytes_sent_mb": round(network.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(network.bytes_recv / (1024**2), 2),
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                    "interfaces": await self._get_network_interfaces()
                },
                "temperature": {
                    "current": temperature,
                    "threshold": self.monitoring_config.get("temperature_threshold", 45),
                    "sensors": await self._get_all_temperature_sensors()
                },
                "uptime": {
                    "seconds": int(psutil.boot_time()),
                    "formatted": self._format_uptime(psutil.boot_time())
                },
                "battery": await self._get_battery_info(),
                "system_load": system_info_extended
            }
            
            self.last_check = system_info
            return system_info
            
        except Exception as e:
            self.logger.error(f"Ошибка получения системной информации: {e}")
            return None
    
    async def _get_temperature_advanced(self) -> Optional[float]:
        """Расширенное получение температуры системы"""
        try:
            # Метод 1: psutil sensors
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current > 0:
                                return entry.current
            
            # Метод 2: Системные файлы (Android/Linux)
            temp_files = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/thermal/thermal_zone1/temp',
                '/sys/class/thermal/thermal_zone2/temp',
                '/sys/class/hwmon/hwmon0/temp1_input',
                '/sys/class/hwmon/hwmon1/temp1_input',
                '/sys/class/hwmon/hwmon2/temp1_input',
                '/proc/acpi/thermal_zone/THM0/temperature',
                '/proc/acpi/thermal_zone/THM1/temperature',
                '/sys/devices/virtual/thermal/thermal_zone0/temp',
                '/sys/devices/virtual/thermal/thermal_zone1/temp'
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        with open(temp_file, 'r') as f:
                            temp = float(f.read().strip())
                            if temp > 0:
                                return temp / 1000.0  # Конвертируем из миллиградусов
                    except:
                        continue
            
            # Метод 3: Команда sensors (если установлена)
            try:
                result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'temp' in line.lower() and '°c' in line.lower():
                            # Извлекаем температуру из строки
                            import re
                            match = re.search(r'(\d+(?:\.\d+)?)°C', line)
                            if match:
                                return float(match.group(1))
            except:
                pass
            
            # Метод 4: Android-specific файлы
            android_temp_files = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/devices/system/cpu/cpu0/cpufreq/cpu_temp',
                '/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq'
            ]
            
            for temp_file in android_temp_files:
                if os.path.exists(temp_file):
                    try:
                        with open(temp_file, 'r') as f:
                            temp = float(f.read().strip())
                            if temp > 0:
                                # Для CPU частоты используем приблизительную формулу
                                if 'cpufreq' in temp_file:
                                    return temp / 1000.0 + 20  # Приблизительная температура
                                return temp / 1000.0
                    except:
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения температуры: {e}")
            return None
    
    async def _get_all_temperature_sensors(self) -> Dict[str, float]:
        """Получение всех доступных датчиков температуры"""
        sensors = {}
        
        try:
            # Поиск всех thermal zones
            thermal_dir = '/sys/class/thermal'
            if os.path.exists(thermal_dir):
                for zone in os.listdir(thermal_dir):
                    if zone.startswith('thermal_zone'):
                        temp_file = os.path.join(thermal_dir, zone, 'temp')
                        type_file = os.path.join(thermal_dir, zone, 'type')
                        
                        if os.path.exists(temp_file):
                            try:
                                with open(temp_file, 'r') as f:
                                    temp = float(f.read().strip()) / 1000.0
                                
                                sensor_type = zone
                                if os.path.exists(type_file):
                                    with open(type_file, 'r') as f:
                                        sensor_type = f.read().strip()
                                
                                sensors[sensor_type] = temp
                            except:
                                continue
            
            # Поиск hwmon датчиков
            hwmon_dir = '/sys/class/hwmon'
            if os.path.exists(hwmon_dir):
                for hwmon in os.listdir(hwmon_dir):
                    hwmon_path = os.path.join(hwmon_dir, hwmon)
                    if os.path.isdir(hwmon_path):
                        for file in os.listdir(hwmon_path):
                            if file.startswith('temp') and file.endswith('_input'):
                                try:
                                    temp_file = os.path.join(hwmon_path, file)
                                    with open(temp_file, 'r') as f:
                                        temp = float(f.read().strip()) / 1000.0
                                    sensors[f"hwmon_{hwmon}_{file}"] = temp
                                except:
                                    continue
                                    
        except Exception as e:
            self.logger.error(f"Ошибка получения датчиков температуры: {e}")
        
        return sensors
    
    async def _get_load_average(self) -> Dict[str, float]:
        """Получение средней нагрузки системы"""
        try:
            if hasattr(os, 'getloadavg'):
                load1, load5, load15 = os.getloadavg()
                return {
                    "1min": round(load1, 2),
                    "5min": round(load5, 2),
                    "15min": round(load15, 2)
                }
        except:
            pass
        
        return {"1min": 0, "5min": 0, "15min": 0}
    
    async def _get_swap_info(self) -> Dict[str, Any]:
        """Получение информации о swap"""
        try:
            swap = psutil.swap_memory()
            return {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percent": swap.percent
            }
        except:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}
    
    async def _get_disk_io_stats(self) -> Dict[str, Any]:
        """Получение статистики ввода-вывода диска"""
        try:
            disk_io = psutil.disk_io_counters()
            return {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes_mb": round(disk_io.read_bytes / (1024**2), 2),
                "write_bytes_mb": round(disk_io.write_bytes / (1024**2), 2)
            }
        except:
            return {"read_count": 0, "write_count": 0, "read_bytes_mb": 0, "write_bytes_mb": 0}
    
    async def _get_network_interfaces(self) -> Dict[str, Any]:
        """Получение информации о сетевых интерфейсах"""
        try:
            interfaces = {}
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface, addrs in net_if_addrs.items():
                if interface in net_if_stats:
                    stats = net_if_stats[interface]
                    interfaces[interface] = {
                        "is_up": stats.isup,
                        "speed_mbps": stats.speed if stats.speed > 0 else None,
                        "addresses": [addr.address for addr in addrs if addr.family == 2]  # IPv4
                    }
            
            return interfaces
        except:
            return {}
    
    async def _get_battery_info(self) -> Dict[str, Any]:
        """Получение информации о батарее"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left_minutes": battery.secsleft // 60 if battery.secsleft > 0 else None
                }
        except:
            pass
        
        return {"percent": None, "power_plugged": None, "time_left_minutes": None}
    
    async def _get_extended_system_info(self) -> Dict[str, Any]:
        """Получение расширенной системной информации"""
        try:
            # Информация о системе
            uname = os.uname()
            
            # Информация о Python
            import sys
            python_info = {
                "version": sys.version,
                "executable": sys.executable,
                "platform": sys.platform
            }
            
            # Информация о пользователе
            user_info = {
                "current_user": os.getenv('USER', 'unknown'),
                "home_dir": os.getenv('HOME', 'unknown'),
                "current_dir": os.getcwd()
            }
            
            return {
                "system": {
                    "sysname": uname.sysname,
                    "nodename": uname.nodename,
                    "release": uname.release,
                    "version": uname.version,
                    "machine": uname.machine
                },
                "python": python_info,
                "user": user_info
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения расширенной информации: {e}")
            return {}
    
    def _format_uptime(self, boot_time: float) -> str:
        """Форматирование времени работы системы"""
        uptime_seconds = int(psutil.boot_time())
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    
    async def check_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Проверка алертов системы"""
        if not await self.role_manager.check_permission(user_id, "system", "monitor"):
            return []
            
        system_info = await self.get_system_info(user_id)
        if not system_info:
            return []
            
        alerts = []
        
        # CPU alert
        if system_info["cpu"]["usage_percent"] > system_info["cpu"]["threshold"]:
            alerts.append({
                "type": "cpu",
                "level": "warning" if system_info["cpu"]["usage_percent"] < 95 else "critical",
                "message": f"CPU: {system_info['cpu']['usage_percent']}% (порог: {system_info['cpu']['threshold']}%)",
                "value": system_info["cpu"]["usage_percent"]
            })
        
        # Memory alert
        if system_info["memory"]["usage_percent"] > system_info["memory"]["threshold"]:
            alerts.append({
                "type": "memory",
                "level": "warning" if system_info["memory"]["usage_percent"] < 95 else "critical",
                "message": f"RAM: {system_info['memory']['usage_percent']}% (порог: {system_info['memory']['threshold']}%)",
                "value": system_info["memory"]["usage_percent"]
            })
        
        # Disk alert
        if system_info["disk"]["usage_percent"] > system_info["disk"]["threshold"]:
            alerts.append({
                "type": "disk",
                "level": "warning" if system_info["disk"]["usage_percent"] < 95 else "critical",
                "message": f"Диск: {system_info['disk']['usage_percent']}% (порог: {system_info['disk']['threshold']}%)",
                "value": system_info["disk"]["usage_percent"]
            })
        
        # Temperature alert
        if system_info["temperature"]["current"] and system_info["temperature"]["current"] > system_info["temperature"]["threshold"]:
            alerts.append({
                "type": "temperature",
                "level": "warning" if system_info["temperature"]["current"] < 60 else "critical",
                "message": f"Температура: {system_info['temperature']['current']}°C (порог: {system_info['temperature']['threshold']}°C)",
                "value": system_info["temperature"]["current"]
            })
        
        # Battery alert (если доступно)
        if system_info["battery"]["percent"] is not None and system_info["battery"]["percent"] < 20:
            alerts.append({
                "type": "battery",
                "level": "warning" if system_info["battery"]["percent"] > 10 else "critical",
                "message": f"Батарея: {system_info['battery']['percent']}%",
                "value": system_info["battery"]["percent"]
            })
        
        self.alerts = alerts
        return alerts
    
    async def get_system_status(self, user_id: int) -> str:
        """Получение статуса системы в текстовом виде"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return "❌ Нет доступа к системной информации"
            
        system_info = await self.get_system_info(user_id)
        if not system_info:
            return "❌ Ошибка получения системной информации"
            
        alerts = await self.check_alerts(user_id)
        alert_count = len(alerts)
        
        # Формируем расширенный статус
        status = f"""🖥️ **Системный статус** ({system_info['platform']})

📊 **CPU**: {system_info['cpu']['usage_percent']}% ({system_info['cpu']['count']} ядер)
   📈 Нагрузка: {system_info['cpu']['load_avg']['1min']} (1м) / {system_info['cpu']['load_avg']['5min']} (5м) / {system_info['cpu']['load_avg']['15min']} (15м)

💾 **RAM**: {system_info['memory']['usage_percent']}% ({system_info['memory']['used_gb']}GB / {system_info['memory']['total_gb']}GB)
   💿 Swap: {system_info['memory']['swap']['percent']}% ({system_info['memory']['swap']['used_gb']}GB / {system_info['memory']['swap']['total_gb']}GB)

💿 **Диск**: {system_info['disk']['usage_percent']}% ({system_info['disk']['used_gb']}GB / {system_info['disk']['total_gb']}GB)
   📊 I/O: 📥 {system_info['disk']['io_stats']['read_bytes_mb']}MB / 📤 {system_info['disk']['io_stats']['write_bytes_mb']}MB

🌡️ **Температура**: {system_info['temperature']['current']}°C
   🔍 Датчики: {len(system_info['temperature']['sensors'])} доступно

⏰ **Время работы**: {system_info['uptime']['formatted']}

📡 **Сеть**:
   📤 Отправлено: {system_info['network']['bytes_sent_mb']}MB
   📥 Получено: {system_info['network']['bytes_recv_mb']}MB
   🌐 Интерфейсы: {len(system_info['network']['interfaces'])} активных"""

        # Добавляем информацию о батарее если доступна
        if system_info["battery"]["percent"] is not None:
            battery_emoji = "🔋" if system_info["battery"]["power_plugged"] else "🔌"
            status += f"\n\n{battery_emoji} **Батарея**: {system_info['battery']['percent']}%"
            if system_info["battery"]["time_left_minutes"]:
                status += f" (осталось ~{system_info['battery']['time_left_minutes']} мин)"

        status += f"\n\n🚨 **Алерты**: {alert_count} активных"

        if alerts:
            status += "\n\n⚠️ **Активные предупреждения**:\n"
            for alert in alerts[:3]:  # Показываем только первые 3
                emoji = "🔴" if alert["level"] == "critical" else "🟡"
                status += f"{emoji} {alert['message']}\n"
        
        return status
    
    async def get_processes_info(self, user_id: int, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Получение информации о процессах"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return None
            
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                        # Получаем дополнительную информацию
                        try:
                            proc_obj = psutil.Process(proc_info['pid'])
                            processes.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'cpu_percent': round(proc_info['cpu_percent'], 1),
                                'memory_percent': round(proc_info['memory_percent'], 1),
                                'status': proc_info['status'],
                                'create_time': datetime.fromtimestamp(proc_info['create_time']).strftime('%H:%M:%S'),
                                'memory_mb': round(proc_obj.memory_info().rss / (1024**2), 1),
                                'username': proc_obj.username() if hasattr(proc_obj, 'username') else 'unknown'
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
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
        if not await self.role_manager.check_permission(user_id, "system", "kill"):
            return False
            
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка завершения процесса {pid}: {e}")
            return False 