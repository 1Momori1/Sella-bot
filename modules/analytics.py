import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import statistics
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64

class Analytics:
    """Модуль аналитики и генерации отчетов"""
    
    def __init__(self, config: dict, role_manager, system_monitor, process_manager, cloud_storage):
        self.config = config.get("analytics", {})
        self.role_manager = role_manager
        self.system_monitor = system_monitor
        self.process_manager = process_manager
        self.cloud_storage = cloud_storage
        self.logger = logging.getLogger(__name__)
        
        # Настройки аналитики
        self.enabled = self.config.get("enabled", True)
        self.data_retention_days = self.config.get("data_retention_days", 30)
        self.auto_reports = self.config.get("auto_reports", True)
        self.report_interval = self.config.get("report_interval", 86400)  # 24 часа
        
        # Хранилище данных
        self.metrics_history = {
            "system": [],
            "processes": [],
            "storage": [],
            "users": []
        }
        
        # Настройка matplotlib для работы без GUI
        plt.switch_backend('Agg')
        
    async def start_analytics(self):
        """Запуск системы аналитики"""
        if not self.enabled:
            return
        
        self.logger.info("Запуск системы аналитики")
        
        # Создание директории для данных
        Path("analytics").mkdir(exist_ok=True)
        
        # Запуск фоновых задач
        asyncio.create_task(self._data_collection_loop())
        asyncio.create_task(self._auto_report_generation())
        
    async def _data_collection_loop(self):
        """Цикл сбора данных"""
        while self.enabled:
            try:
                await self._collect_system_metrics()
                await self._collect_process_metrics()
                await self._collect_storage_metrics()
                await self._collect_user_metrics()
                
                # Сохранение данных
                await self._save_metrics_data()
                
                # Очистка старых данных
                await self._cleanup_old_data()
                
                await asyncio.sleep(300)  # Сбор каждые 5 минут
                
            except Exception as e:
                self.logger.error(f"Ошибка сбора данных: {e}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # Получение системной информации
            system_info = await self.system_monitor.get_system_info(123456789)  # Используем админа
            if not system_info:
                return
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": system_info["cpu"]["usage_percent"],
                "memory_usage": system_info["memory"]["usage_percent"],
                "disk_usage": system_info["disk"]["usage_percent"],
                "temperature": system_info["temperature"]["current"],
                "network_rx": system_info["network"]["bytes_recv"],
                "network_tx": system_info["network"]["bytes_sent"],
                "load_average": system_info["cpu"]["load_average"]
            }
            
            self.metrics_history["system"].append(metric)
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора системных метрик: {e}")
    
    async def _collect_process_metrics(self):
        """Сбор метрик процессов"""
        try:
            processes = await self.process_manager.get_bots_status(123456789)
            if not processes:
                return
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "total_processes": len(processes),
                "running_processes": len([p for p in processes if p["status"] == "running"]),
                "stopped_processes": len([p for p in processes if p["status"] == "stopped"]),
                "total_cpu_usage": sum(p.get("cpu_percent", 0) for p in processes),
                "total_memory_usage": sum(p.get("memory_mb", 0) for p in processes),
                "process_details": [
                    {
                        "name": p["name"],
                        "status": p["status"],
                        "cpu_percent": p.get("cpu_percent", 0),
                        "memory_mb": p.get("memory_mb", 0)
                    }
                    for p in processes
                ]
            }
            
            self.metrics_history["processes"].append(metric)
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора метрик процессов: {e}")
    
    async def _collect_storage_metrics(self):
        """Сбор метрик хранилища"""
        try:
            storage_info = await self.cloud_storage.get_storage_usage(123456789)
            if not storage_info:
                return
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "total_files": storage_info.get("total_files", 0),
                "total_size_mb": storage_info.get("total_size_mb", 0),
                "users_count": storage_info.get("users_count", 0),
                "file_types": storage_info.get("file_types", {}),
                "recent_uploads": storage_info.get("recent_uploads", 0)
            }
            
            self.metrics_history["storage"].append(metric)
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора метрик хранилища: {e}")
    
    async def _collect_user_metrics(self):
        """Сбор метрик пользователей"""
        try:
            metric = {
                "timestamp": datetime.now().isoformat(),
                "total_users": len(self.role_manager.users),
                "active_users": 0,  # В реальной реализации отслеживались бы активные пользователи
                "users_by_role": {},
                "recent_activity": []
            }
            
            # Подсчет пользователей по ролям
            for user_info in self.role_manager.users.values():
                role = user_info.get("role", "unknown")
                if role not in metric["users_by_role"]:
                    metric["users_by_role"][role] = 0
                metric["users_by_role"][role] += 1
            
            self.metrics_history["users"].append(metric)
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора метрик пользователей: {e}")
    
    async def _save_metrics_data(self):
        """Сохранение собранных данных"""
        try:
            data_file = Path("analytics/metrics_data.json")
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics_history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
            
            for metric_type in self.metrics_history:
                self.metrics_history[metric_type] = [
                    metric for metric in self.metrics_history[metric_type]
                    if datetime.fromisoformat(metric["timestamp"]) > cutoff_date
                ]
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых данных: {e}")
    
    async def generate_system_report(self, user_id: int, period: str = "24h") -> Dict[str, Any]:
        """Генерация отчета по системе"""
        if not await self.role_manager.check_permission(user_id, "analytics", "view"):
            return {"error": "Нет доступа к аналитике"}
        
        try:
            # Определение периода
            if period == "24h":
                start_time = datetime.now() - timedelta(hours=24)
            elif period == "7d":
                start_time = datetime.now() - timedelta(days=7)
            elif period == "30d":
                start_time = datetime.now() - timedelta(days=30)
            else:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Фильтрация данных по периоду
            system_data = [
                metric for metric in self.metrics_history["system"]
                if datetime.fromisoformat(metric["timestamp"]) > start_time
            ]
            
            if not system_data:
                return {"error": "Нет данных за указанный период"}
            
            # Анализ данных
            report = {
                "period": period,
                "data_points": len(system_data),
                "timestamp": datetime.now().isoformat(),
                "cpu": await self._analyze_cpu_metrics(system_data),
                "memory": await self._analyze_memory_metrics(system_data),
                "disk": await self._analyze_disk_metrics(system_data),
                "temperature": await self._analyze_temperature_metrics(system_data),
                "network": await self._analyze_network_metrics(system_data),
                "summary": await self._generate_system_summary(system_data)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации системного отчета: {e}")
            return {"error": f"Ошибка генерации отчета: {str(e)}"}
    
    async def _analyze_cpu_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ метрик CPU"""
        cpu_values = [metric["cpu_usage"] for metric in data if "cpu_usage" in metric]
        
        if not cpu_values:
            return {"error": "Нет данных CPU"}
        
        return {
            "current": cpu_values[-1],
            "average": statistics.mean(cpu_values),
            "max": max(cpu_values),
            "min": min(cpu_values),
            "median": statistics.median(cpu_values),
            "std_dev": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
            "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing" if cpu_values[-1] < cpu_values[0] else "stable"
        }
    
    async def _analyze_memory_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ метрик памяти"""
        memory_values = [metric["memory_usage"] for metric in data if "memory_usage" in metric]
        
        if not memory_values:
            return {"error": "Нет данных памяти"}
        
        return {
            "current": memory_values[-1],
            "average": statistics.mean(memory_values),
            "max": max(memory_values),
            "min": min(memory_values),
            "median": statistics.median(memory_values),
            "std_dev": statistics.stdev(memory_values) if len(memory_values) > 1 else 0,
            "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing" if memory_values[-1] < memory_values[0] else "stable"
        }
    
    async def _analyze_disk_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ метрик диска"""
        disk_values = [metric["disk_usage"] for metric in data if "disk_usage" in metric]
        
        if not disk_values:
            return {"error": "Нет данных диска"}
        
        return {
            "current": disk_values[-1],
            "average": statistics.mean(disk_values),
            "max": max(disk_values),
            "min": min(disk_values),
            "median": statistics.median(disk_values),
            "std_dev": statistics.stdev(disk_values) if len(disk_values) > 1 else 0,
            "trend": "increasing" if disk_values[-1] > disk_values[0] else "decreasing" if disk_values[-1] < disk_values[0] else "stable"
        }
    
    async def _analyze_temperature_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ метрик температуры"""
        temp_values = [metric["temperature"] for metric in data if metric.get("temperature")]
        
        if not temp_values:
            return {"error": "Нет данных температуры"}
        
        return {
            "current": temp_values[-1],
            "average": statistics.mean(temp_values),
            "max": max(temp_values),
            "min": min(temp_values),
            "median": statistics.median(temp_values),
            "std_dev": statistics.stdev(temp_values) if len(temp_values) > 1 else 0,
            "trend": "increasing" if temp_values[-1] > temp_values[0] else "decreasing" if temp_values[-1] < temp_values[0] else "stable"
        }
    
    async def _analyze_network_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ сетевых метрик"""
        rx_values = [metric["network_rx"] for metric in data if "network_rx" in metric]
        tx_values = [metric["network_tx"] for metric in data if "network_tx" in metric]
        
        if not rx_values or not tx_values:
            return {"error": "Нет сетевых данных"}
        
        return {
            "rx": {
                "current": rx_values[-1],
                "total": sum(rx_values),
                "average": statistics.mean(rx_values),
                "max": max(rx_values)
            },
            "tx": {
                "current": tx_values[-1],
                "total": sum(tx_values),
                "average": statistics.mean(tx_values),
                "max": max(tx_values)
            }
        }
    
    async def _generate_system_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерация сводки по системе"""
        try:
            # Определение состояния системы
            current_cpu = data[-1]["cpu_usage"]
            current_memory = data[-1]["memory_usage"]
            current_disk = data[-1]["disk_usage"]
            
            # Оценка состояния
            cpu_status = "critical" if current_cpu > 90 else "warning" if current_cpu > 80 else "good"
            memory_status = "critical" if current_memory > 95 else "warning" if current_memory > 85 else "good"
            disk_status = "critical" if current_disk > 95 else "warning" if current_disk > 90 else "good"
            
            # Общее состояние
            if any(status == "critical" for status in [cpu_status, memory_status, disk_status]):
                overall_status = "critical"
            elif any(status == "warning" for status in [cpu_status, memory_status, disk_status]):
                overall_status = "warning"
            else:
                overall_status = "good"
            
            return {
                "overall_status": overall_status,
                "cpu_status": cpu_status,
                "memory_status": memory_status,
                "disk_status": disk_status,
                "recommendations": await self._generate_recommendations(data)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации сводки: {e}")
            return {"error": "Ошибка генерации сводки"}
    
    async def _generate_recommendations(self, data: List[Dict[str, Any]]) -> List[str]:
        """Генерация рекомендаций на основе данных"""
        recommendations = []
        
        try:
            current_cpu = data[-1]["cpu_usage"]
            current_memory = data[-1]["memory_usage"]
            current_disk = data[-1]["disk_usage"]
            
            if current_cpu > 90:
                recommendations.append("Критическая нагрузка на CPU - проверьте процессы")
            elif current_cpu > 80:
                recommendations.append("Высокая нагрузка на CPU - рассмотрите оптимизацию")
            
            if current_memory > 95:
                recommendations.append("Критическое использование памяти - освободите память")
            elif current_memory > 85:
                recommendations.append("Высокое использование памяти - проверьте процессы")
            
            if current_disk > 95:
                recommendations.append("Критическое заполнение диска - очистите место")
            elif current_disk > 90:
                recommendations.append("Высокое заполнение диска - удалите ненужные файлы")
            
            if not recommendations:
                recommendations.append("Система работает стабильно")
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации рекомендаций: {e}")
            recommendations.append("Ошибка анализа данных")
        
        return recommendations
    
    async def generate_process_report(self, user_id: int, period: str = "24h") -> Dict[str, Any]:
        """Генерация отчета по процессам"""
        if not await self.role_manager.check_permission(user_id, "analytics", "view"):
            return {"error": "Нет доступа к аналитике"}
        
        try:
            # Определение периода
            if period == "24h":
                start_time = datetime.now() - timedelta(hours=24)
            elif period == "7d":
                start_time = datetime.now() - timedelta(days=7)
            else:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Фильтрация данных
            process_data = [
                metric for metric in self.metrics_history["processes"]
                if datetime.fromisoformat(metric["timestamp"]) > start_time
            ]
            
            if not process_data:
                return {"error": "Нет данных о процессах за указанный период"}
            
            # Анализ данных
            report = {
                "period": period,
                "data_points": len(process_data),
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_processes": process_data[-1]["total_processes"],
                    "running_processes": process_data[-1]["running_processes"],
                    "stopped_processes": process_data[-1]["stopped_processes"],
                    "uptime_percentage": (process_data[-1]["running_processes"] / process_data[-1]["total_processes"] * 100) if process_data[-1]["total_processes"] > 0 else 0
                },
                "resource_usage": {
                    "total_cpu": process_data[-1]["total_cpu_usage"],
                    "total_memory": process_data[-1]["total_memory_usage"],
                    "average_cpu": statistics.mean([p["total_cpu_usage"] for p in process_data]),
                    "average_memory": statistics.mean([p["total_memory_usage"] for p in process_data])
                },
                "top_processes": await self._get_top_processes(process_data[-1]["process_details"])
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета процессов: {e}")
            return {"error": f"Ошибка генерации отчета: {str(e)}"}
    
    async def _get_top_processes(self, process_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Получение топ процессов по потреблению ресурсов"""
        try:
            # Сортировка по CPU
            top_cpu = sorted(process_details, key=lambda x: x.get("cpu_percent", 0), reverse=True)[:5]
            
            # Сортировка по памяти
            top_memory = sorted(process_details, key=lambda x: x.get("memory_mb", 0), reverse=True)[:5]
            
            return {
                "by_cpu": top_cpu,
                "by_memory": top_memory
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения топ процессов: {e}")
            return {"by_cpu": [], "by_memory": []}
    
    async def generate_storage_report(self, user_id: int, period: str = "24h") -> Dict[str, Any]:
        """Генерация отчета по хранилищу"""
        if not await self.role_manager.check_permission(user_id, "analytics", "view"):
            return {"error": "Нет доступа к аналитике"}
        
        try:
            # Определение периода
            if period == "24h":
                start_time = datetime.now() - timedelta(hours=24)
            elif period == "7d":
                start_time = datetime.now() - timedelta(days=7)
            else:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Фильтрация данных
            storage_data = [
                metric for metric in self.metrics_history["storage"]
                if datetime.fromisoformat(metric["timestamp"]) > start_time
            ]
            
            if not storage_data:
                return {"error": "Нет данных о хранилище за указанный период"}
            
            # Анализ данных
            report = {
                "period": period,
                "data_points": len(storage_data),
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_files": storage_data[-1]["total_files"],
                    "total_size_mb": storage_data[-1]["total_size_mb"],
                    "users_count": storage_data[-1]["users_count"],
                    "recent_uploads": storage_data[-1]["recent_uploads"]
                },
                "file_types": storage_data[-1]["file_types"],
                "growth": {
                    "files_growth": storage_data[-1]["total_files"] - storage_data[0]["total_files"],
                    "size_growth_mb": storage_data[-1]["total_size_mb"] - storage_data[0]["total_size_mb"]
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета хранилища: {e}")
            return {"error": f"Ошибка генерации отчета: {str(e)}"}
    
    async def create_performance_chart(self, user_id: int, metric_type: str = "system", period: str = "24h") -> Optional[str]:
        """Создание графика производительности"""
        if not await self.role_manager.check_permission(user_id, "analytics", "view"):
            return None
        
        try:
            # Определение периода
            if period == "24h":
                start_time = datetime.now() - timedelta(hours=24)
            elif period == "7d":
                start_time = datetime.now() - timedelta(days=7)
            else:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Фильтрация данных
            data = [
                metric for metric in self.metrics_history[metric_type]
                if datetime.fromisoformat(metric["timestamp"]) > start_time
            ]
            
            if not data:
                return None
            
            # Создание графика
            fig, ax = plt.subplots(figsize=(12, 8))
            
            timestamps = [datetime.fromisoformat(metric["timestamp"]) for metric in data]
            
            if metric_type == "system":
                # График системных метрик
                ax.plot(timestamps, [metric["cpu_usage"] for metric in data], label="CPU %", linewidth=2)
                ax.plot(timestamps, [metric["memory_usage"] for metric in data], label="Memory %", linewidth=2)
                ax.plot(timestamps, [metric["disk_usage"] for metric in data], label="Disk %", linewidth=2)
                
                ax.set_ylabel("Usage %")
                ax.set_title("System Performance Metrics")
                
            elif metric_type == "processes":
                # График процессов
                ax.plot(timestamps, [metric["total_cpu_usage"] for metric in data], label="Total CPU %", linewidth=2)
                ax.plot(timestamps, [metric["total_memory_usage"] for metric in data], label="Total Memory (MB)", linewidth=2)
                
                ax.set_ylabel("Usage")
                ax.set_title("Process Performance Metrics")
            
            ax.set_xlabel("Time")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Форматирование оси времени
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Сохранение в байты
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # Кодирование в base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика: {e}")
            return None
    
    async def _auto_report_generation(self):
        """Автоматическая генерация отчетов"""
        while self.enabled and self.auto_reports:
            try:
                # Генерация ежедневного отчета
                await self._generate_daily_report()
                await asyncio.sleep(self.report_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка автоматической генерации отчетов: {e}")
                await asyncio.sleep(3600)  # Пауза 1 час при ошибке
    
    async def _generate_daily_report(self):
        """Генерация ежедневного отчета"""
        try:
            # Получение отчетов
            system_report = await self.generate_system_report(123456789, "24h")
            process_report = await self.generate_process_report(123456789, "24h")
            storage_report = await self.generate_storage_report(123456789, "24h")
            
            # Создание сводного отчета
            daily_report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat(),
                "system": system_report,
                "processes": process_report,
                "storage": storage_report
            }
            
            # Сохранение отчета
            report_file = Path(f"analytics/daily_report_{datetime.now().strftime('%Y%m%d')}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(daily_report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Создан ежедневный отчет: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ежедневного отчета: {e}")
    
    async def get_analytics_summary(self, user_id: int) -> Dict[str, Any]:
        """Получение сводки аналитики"""
        if not await self.role_manager.check_permission(user_id, "analytics", "view"):
            return {"error": "Нет доступа к аналитике"}
        
        try:
            # Получение последних данных
            latest_system = self.metrics_history["system"][-1] if self.metrics_history["system"] else None
            latest_processes = self.metrics_history["processes"][-1] if self.metrics_history["processes"] else None
            latest_storage = self.metrics_history["storage"][-1] if self.metrics_history["storage"] else None
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "data_points": {
                    "system": len(self.metrics_history["system"]),
                    "processes": len(self.metrics_history["processes"]),
                    "storage": len(self.metrics_history["storage"]),
                    "users": len(self.metrics_history["users"])
                },
                "current_status": {
                    "system": latest_system,
                    "processes": latest_processes,
                    "storage": latest_storage
                },
                "retention_days": self.data_retention_days,
                "auto_reports": self.auto_reports
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки аналитики: {e}")
            return {"error": f"Ошибка получения сводки: {str(e)}"} 