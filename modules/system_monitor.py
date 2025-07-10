import psutil
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

class SystemMonitor:
    """Модуль системного мониторинга"""
    
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
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Temperature (если доступно)
            temperature = await self._get_temperature()
            
            system_info = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                    "threshold": self.monitoring_config.get("cpu_threshold", 80)
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "threshold": self.monitoring_config.get("memory_threshold", 85)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "threshold": self.monitoring_config.get("disk_threshold", 90)
                },
                "network": {
                    "bytes_sent_mb": round(network.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(network.bytes_recv / (1024**2), 2),
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "temperature": {
                    "current": temperature,
                    "threshold": self.monitoring_config.get("temperature_threshold", 45)
                },
                "uptime": {
                    "seconds": int(psutil.boot_time()),
                    "formatted": self._format_uptime(psutil.boot_time())
                }
            }
            
            self.last_check = system_info
            return system_info
            
        except Exception as e:
            self.logger.error(f"Ошибка получения системной информации: {e}")
            return None
    
    async def _get_temperature(self) -> Optional[float]:
        """Получение температуры системы"""
        try:
            # Попытка получить температуру через psutil (Linux)
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current > 0:
                                return entry.current
        except:
            pass
            
        # Windows - попытка через WMI
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = w.Sensor()
            for sensor in temperature_infos:
                if sensor.SensorType == 'Temperature':
                    return float(sensor.Value)
        except:
            pass
            
        return None
    
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
        
        status = f"""🖥️ **Системный статус**

📊 **CPU**: {system_info['cpu']['usage_percent']}% ({system_info['cpu']['count']} ядер)
💾 **RAM**: {system_info['memory']['usage_percent']}% ({system_info['memory']['used_gb']}GB / {system_info['memory']['total_gb']}GB)
💿 **Диск**: {system_info['disk']['usage_percent']}% ({system_info['disk']['used_gb']}GB / {system_info['disk']['total_gb']}GB)

🌡️ **Температура**: {system_info['temperature']['current']}°C (если доступно)
⏰ **Время работы**: {system_info['uptime']['formatted']}

📡 **Сеть**:
   📤 Отправлено: {system_info['network']['bytes_sent_mb']}MB
   📥 Получено: {system_info['network']['bytes_recv_mb']}MB

⚠️ **Алерты**: {alert_count} активных"""

        if alerts:
            status += "\n\n🔴 **Активные алерты:**"
            for alert in alerts:
                emoji = "🔴" if alert["level"] == "critical" else "🟡"
                status += f"\n{emoji} {alert['message']}"
        
        return status
    
    async def get_processes_info(self, user_id: int, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Получение информации о процессах"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return None
            
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": round(proc_info['cpu_percent'], 1),
                            "memory_percent": round(proc_info['memory_percent'], 1),
                            "status": proc_info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортировка по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о процессах: {e}")
            return None 