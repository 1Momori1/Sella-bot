import psutil
import platform
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Мониторинг системы с горизонтальными шкалами и сбором данных"""
    
    def __init__(self, storage_path: str = "data"):
        self.storage_path = storage_path
        self.memory_data_file = os.path.join(storage_path, "memory_history.json")
        self.ensure_storage_exists()
        self.load_memory_history()
    
    def ensure_storage_exists(self):
        """Создание папки для хранения данных"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            logger.info(f"Создана папка для данных: {self.storage_path}")
    
    def load_memory_history(self):
        """Загрузка истории данных о памяти"""
        try:
            if os.path.exists(self.memory_data_file):
                with open(self.memory_data_file, 'r', encoding='utf-8') as f:
                    self.memory_history = json.load(f)
            else:
                self.memory_history = []
                self.save_memory_history()
        except Exception as e:
            logger.error(f"Ошибка загрузки истории памяти: {e}")
            self.memory_history = []
    
    def save_memory_history(self):
        """Сохранение истории данных о памяти"""
        try:
            with open(self.memory_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории памяти: {e}")
    
    def create_progress_bar(self, value: float, max_value: float, width: int = 20) -> str:
        """Создание горизонтальной шкалы прогресса"""
        if max_value <= 0:
            return "█" * width
        
        percentage = min(value / max_value, 1.0)
        filled = int(percentage * width)
        empty = width - filled
        
        # Определяем цвет в зависимости от процента
        if percentage < 0.5:
            color = "🟢"  # Зеленый
        elif percentage < 0.8:
            color = "🟡"  # Желтый
        else:
            color = "🔴"  # Красный
        
        bar = "█" * filled + "░" * empty
        return f"{color} {bar} {percentage*100:.1f}%"
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """Получение информации о CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                "usage": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0,
                "bar": self.create_progress_bar(cpu_percent, 100)
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных CPU: {e}")
            return {"usage": 0, "count": 0, "frequency": 0, "bar": "❌ Ошибка"}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Получение информации о памяти"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Сохраняем данные для истории
            self.add_memory_data(memory.percent, memory.used, memory.total)
            
            return {
                "used": memory.used,
                "total": memory.total,
                "percent": memory.percent,
                "available": memory.available,
                "swap_used": swap.used,
                "swap_total": swap.total,
                "swap_percent": swap.percent,
                "bar": self.create_progress_bar(memory.used, memory.total),
                "swap_bar": self.create_progress_bar(swap.used, swap.total) if swap.total > 0 else "🟢 ██████████████████ 0.0%"
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных памяти: {e}")
            return {"used": 0, "total": 0, "percent": 0, "available": 0, "bar": "❌ Ошибка"}
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Получение информации о дисках"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                "used": disk_usage.used,
                "total": disk_usage.total,
                "free": disk_usage.free,
                "percent": disk_usage.percent,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "bar": self.create_progress_bar(disk_usage.used, disk_usage.total)
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных диска: {e}")
            return {"used": 0, "total": 0, "free": 0, "percent": 0, "bar": "❌ Ошибка"}
    
    def get_network_usage(self) -> Dict[str, Any]:
        """Получение информации о сети"""
        try:
            network_io = psutil.net_io_counters()
            
            # Получаем скорость сети (байт/сек)
            if hasattr(self, '_last_network_io'):
                time_diff = time.time() - self._last_network_time
                bytes_sent_diff = network_io.bytes_sent - self._last_network_io.bytes_sent
                bytes_recv_diff = network_io.bytes_recv - self._last_network_io.bytes_recv
                
                upload_speed = bytes_sent_diff / time_diff if time_diff > 0 else 0
                download_speed = bytes_recv_diff / time_diff if time_diff > 0 else 0
            else:
                upload_speed = 0
                download_speed = 0
            
            self._last_network_io = network_io
            self._last_network_time = time.time()
            
            return {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "upload_speed": upload_speed,
                "download_speed": download_speed,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных сети: {e}")
            return {"bytes_sent": 0, "bytes_recv": 0, "upload_speed": 0, "download_speed": 0}
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Получение информации о батарее"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                # Определяем статус батареи
                if battery.power_plugged:
                    status = "🔌 Заряжается"
                else:
                    if battery.percent > 20:
                        status = "🔋 Работает от батареи"
                    else:
                        status = "⚠️ Низкий заряд"
                
                # Расчет времени работы
                if battery.secsleft != -1:
                    hours = battery.secsleft // 3600
                    minutes = (battery.secsleft % 3600) // 60
                    time_left = f"{hours}ч {minutes}м"
                else:
                    time_left = "Неизвестно"
                
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left": time_left,
                    "status": status,
                    "bar": self.create_progress_bar(battery.percent, 100)
                }
            else:
                return {
                    "percent": 0,
                    "power_plugged": False,
                    "time_left": "Н/Д",
                    "status": "🔌 Нет батареи",
                    "bar": "🔌 ██████████████████ 0.0%"
                }
        except Exception as e:
            logger.error(f"Ошибка получения данных батареи: {e}")
            return {
                "percent": 0,
                "power_plugged": False,
                "time_left": "Ошибка",
                "status": "❌ Ошибка",
                "bar": "❌ ██████████████████ 0.0%"
            }
    
    def get_temperature(self) -> Dict[str, Any]:
        """Получение информации о температуре"""
        try:
            temperatures = psutil.sensors_temperatures()
            if temperatures:
                # Берем первую доступную температуру
                for name, entries in temperatures.items():
                    if entries:
                        temp = entries[0].current
                        return {
                            "temperature": temp,
                            "unit": "°C",
                            "status": "🌡️ Нормальная" if temp < 70 else "🌡️ Высокая"
                        }
            
            return {"temperature": 0, "unit": "°C", "status": "🌡️ Н/Д"}
        except Exception as e:
            logger.error(f"Ошибка получения температуры: {e}")
            return {"temperature": 0, "unit": "°C", "status": "❌ Ошибка"}
    
    def format_bytes(self, bytes_value: int) -> str:
        """Форматирование байтов в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"
    
    def add_memory_data(self, percent: float, used: int, total: int):
        """Добавление данных о памяти в историю"""
        try:
            timestamp = datetime.now().isoformat()
            data = {
                "timestamp": timestamp,
                "percent": percent,
                "used": used,
                "total": total,
                "used_formatted": self.format_bytes(used),
                "total_formatted": self.format_bytes(total)
            }
            
            self.memory_history.append(data)
            
            # Оставляем только данные за последние 24 часа
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.memory_history = [
                entry for entry in self.memory_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
            
            # Сохраняем каждые 10 записей
            if len(self.memory_history) % 10 == 0:
                self.save_memory_history()
                
        except Exception as e:
            logger.error(f"Ошибка добавления данных памяти: {e}")
    
    def get_memory_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получение истории использования памяти"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [
                entry for entry in self.memory_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
        except Exception as e:
            logger.error(f"Ошибка получения истории памяти: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики использования памяти"""
        try:
            history = self.get_memory_history(24)
            if not history:
                return {"avg_percent": 0, "max_percent": 0, "min_percent": 0}
            
            percents = [entry["percent"] for entry in history]
            return {
                "avg_percent": sum(percents) / len(percents),
                "max_percent": max(percents),
                "min_percent": min(percents),
                "data_points": len(history)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики памяти: {e}")
            return {"avg_percent": 0, "max_percent": 0, "min_percent": 0}
    
    async def get_system_status(self, user_id: int) -> str:
        """Получение полного статуса системы с горизонтальными шкалами"""
        try:
            # Получаем все данные
            cpu = self.get_cpu_usage()
            memory = self.get_memory_usage()
            disk = self.get_disk_usage()
            network = self.get_network_usage()
            battery = self.get_battery_info()
            temperature = self.get_temperature()
            
            # Форматируем данные
            status = "📊 **Статус системы**\n\n"
            
            # CPU
            status += f"🖥️ **CPU** ({cpu['count']} ядер)\n"
            status += f"   {cpu['bar']}\n"
            status += f"   Частота: {cpu['frequency']:.0f}MHz\n\n"
            
            # RAM
            status += f"💾 **RAM**\n"
            status += f"   {memory['bar']}\n"
            status += f"   {self.format_bytes(memory['used'])} / {self.format_bytes(memory['total'])}\n"
            
            # Swap (если есть)
            if memory.get('swap_total', 0) > 0:
                status += f"   Swap: {memory['swap_bar']}\n"
                status += f"   {self.format_bytes(memory['swap_used'])} / {self.format_bytes(memory['swap_total'])}\n"
            status += "\n"
            
            # Диск
            status += f"💿 **Диск**\n"
            status += f"   {disk['bar']}\n"
            status += f"   {self.format_bytes(disk['used'])} / {self.format_bytes(disk['total'])}\n"
            status += f"   Свободно: {self.format_bytes(disk['free'])}\n\n"
            
            # Сеть
            status += f"📡 **Сеть**\n"
            status += f"   ↑ {self.format_bytes(network['upload_speed'])}/s\n"
            status += f"   ↓ {self.format_bytes(network['download_speed'])}/s\n"
            status += f"   Всего: ↑ {self.format_bytes(network['bytes_sent'])} ↓ {self.format_bytes(network['bytes_recv'])}\n\n"
            
            # Батарея
            status += f"🔋 **Батарея**\n"
            status += f"   {battery['bar']}\n"
            status += f"   {battery['status']}\n"
            if battery['time_left'] != "Н/Д":
                status += f"   Время: {battery['time_left']}\n"
            status += "\n"
            
            # Температура
            if temperature['temperature'] > 0:
                status += f"🌡️ **Температура**\n"
                status += f"   {temperature['temperature']:.1f}°C - {temperature['status']}\n\n"
            
            # Статистика памяти за 24 часа
            memory_stats = self.get_memory_stats()
            if memory_stats['data_points'] > 0:
                status += f"📈 **Статистика памяти (24ч)**\n"
                status += f"   Среднее: {memory_stats['avg_percent']:.1f}%\n"
                status += f"   Максимум: {memory_stats['max_percent']:.1f}%\n"
                status += f"   Минимум: {memory_stats['min_percent']:.1f}%\n"
                status += f"   Записей: {memory_stats['data_points']}\n"
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return "❌ **Ошибка получения данных системы**"
    
    def cleanup_old_data(self):
        """Очистка старых данных (вызывать периодически)"""
        try:
            # Очищаем данные старше 7 дней
            cutoff_time = datetime.now() - timedelta(days=7)
            self.memory_history = [
                entry for entry in self.memory_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
            self.save_memory_history()
            logger.info("Очищены старые данные мониторинга")
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}") 