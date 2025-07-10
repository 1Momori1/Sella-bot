import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
from pathlib import Path

class AIAssistant:
    """Модуль ИИ-ассистента для автоматизации и умных рекомендаций"""
    
    def __init__(self, config: dict, role_manager, system_monitor, process_manager, notification_manager):
        self.config = config.get("ai_assistant", {})
        self.role_manager = role_manager
        self.system_monitor = system_monitor
        self.process_manager = process_manager
        self.notification_manager = notification_manager
        self.logger = logging.getLogger(__name__)
        
        # Настройки ИИ-ассистента
        self.enabled = self.config.get("enabled", True)
        self.auto_optimization = self.config.get("auto_optimization", True)
        self.smart_alerts = self.config.get("smart_alerts", True)
        self.learning_mode = self.config.get("learning_mode", True)
        
        # История действий и рекомендаций
        self.action_history = []
        self.recommendations = []
        self.system_patterns = {}
        
    async def analyze_system_health(self, user_id: int) -> Dict[str, Any]:
        """Анализ здоровья системы и генерация рекомендаций"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return {"error": "Нет доступа к системной информации"}
        
        try:
            system_info = await self.system_monitor.get_system_info(user_id)
            if not system_info:
                return {"error": "Не удалось получить системную информацию"}
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": "good",
                "issues": [],
                "recommendations": [],
                "optimization_opportunities": []
            }
            
            # Анализ CPU
            cpu_usage = system_info["cpu"]["usage_percent"]
            if cpu_usage > 90:
                analysis["overall_health"] = "critical"
                analysis["issues"].append({
                    "type": "cpu",
                    "severity": "critical",
                    "message": f"Критическая нагрузка на CPU: {cpu_usage}%",
                    "recommendation": "Проверьте процессы с высоким потреблением CPU"
                })
            elif cpu_usage > 80:
                analysis["overall_health"] = "warning"
                analysis["issues"].append({
                    "type": "cpu",
                    "severity": "warning",
                    "message": f"Высокая нагрузка на CPU: {cpu_usage}%",
                    "recommendation": "Мониторьте процессы и рассмотрите оптимизацию"
                })
            
            # Анализ памяти
            memory_usage = system_info["memory"]["usage_percent"]
            if memory_usage > 95:
                analysis["overall_health"] = "critical"
                analysis["issues"].append({
                    "type": "memory",
                    "severity": "critical",
                    "message": f"Критическое использование памяти: {memory_usage}%",
                    "recommendation": "Немедленно освободите память или перезапустите систему"
                })
            elif memory_usage > 85:
                analysis["overall_health"] = "warning"
                analysis["issues"].append({
                    "type": "memory",
                    "severity": "warning",
                    "message": f"Высокое использование памяти: {memory_usage}%",
                    "recommendation": "Проверьте процессы, потребляющие много памяти"
                })
            
            # Анализ диска
            disk_usage = system_info["disk"]["usage_percent"]
            if disk_usage > 95:
                analysis["overall_health"] = "critical"
                analysis["issues"].append({
                    "type": "disk",
                    "severity": "critical",
                    "message": f"Критическое заполнение диска: {disk_usage}%",
                    "recommendation": "Немедленно освободите место на диске"
                })
            elif disk_usage > 90:
                analysis["overall_health"] = "warning"
                analysis["issues"].append({
                    "type": "disk",
                    "severity": "warning",
                    "message": f"Высокое заполнение диска: {disk_usage}%",
                    "recommendation": "Очистите временные файлы и логи"
                })
            
            # Анализ температуры
            if system_info["temperature"]["current"]:
                temp = system_info["temperature"]["current"]
                if temp > 80:
                    analysis["overall_health"] = "critical"
                    analysis["issues"].append({
                        "type": "temperature",
                        "severity": "critical",
                        "message": f"Критическая температура: {temp}°C",
                        "recommendation": "Проверьте систему охлаждения"
                    })
                elif temp > 70:
                    analysis["overall_health"] = "warning"
                    analysis["issues"].append({
                        "type": "temperature",
                        "severity": "warning",
                        "message": f"Высокая температура: {temp}°C",
                        "recommendation": "Мониторьте температуру и нагрузку"
                    })
            
            # Генерация рекомендаций по оптимизации
            await self._generate_optimization_recommendations(analysis, system_info)
            
            # Сохранение анализа
            self.action_history.append({
                "type": "system_analysis",
                "timestamp": datetime.now(),
                "user_id": user_id,
                "result": analysis
            })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа системы: {e}")
            return {"error": f"Ошибка анализа: {str(e)}"}
    
    async def _generate_optimization_recommendations(self, analysis: Dict[str, Any], system_info: Dict[str, Any]):
        """Генерация рекомендаций по оптимизации"""
        recommendations = []
        
        # Рекомендации по CPU
        cpu_usage = system_info["cpu"]["usage_percent"]
        if cpu_usage > 70:
            recommendations.append({
                "type": "cpu_optimization",
                "priority": "high" if cpu_usage > 85 else "medium",
                "action": "analyze_processes",
                "description": "Анализ процессов с высоким потреблением CPU",
                "command": "top -o %CPU -n 10"
            })
        
        # Рекомендации по памяти
        memory_usage = system_info["memory"]["usage_percent"]
        if memory_usage > 80:
            recommendations.append({
                "type": "memory_optimization",
                "priority": "high" if memory_usage > 90 else "medium",
                "action": "clear_cache",
                "description": "Очистка кэша и временных файлов",
                "command": "sync && echo 3 > /proc/sys/vm/drop_caches"
            })
        
        # Рекомендации по диску
        disk_usage = system_info["disk"]["usage_percent"]
        if disk_usage > 85:
            recommendations.append({
                "type": "disk_optimization",
                "priority": "high" if disk_usage > 95 else "medium",
                "action": "cleanup_storage",
                "description": "Очистка старых логов и временных файлов",
                "command": "find /var/log -name '*.log' -mtime +7 -delete"
            })
        
        analysis["optimization_opportunities"] = recommendations
    
    async def smart_process_management(self, user_id: int) -> Dict[str, Any]:
        """Умное управление процессами"""
        if not await self.role_manager.check_permission(user_id, "processes", "manage"):
            return {"error": "Нет прав для управления процессами"}
        
        try:
            processes = await self.process_manager.get_all_processes(user_id, limit=50)
            if not processes:
                return {"error": "Не удалось получить информацию о процессах"}
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "suspicious_processes": [],
                "resource_hogs": [],
                "recommendations": []
            }
            
            # Анализ подозрительных процессов
            for proc in processes:
                # Процессы с высоким потреблением ресурсов
                if proc["cpu_percent"] > 50 or proc["memory_percent"] > 10:
                    analysis["resource_hogs"].append({
                        "pid": proc["pid"],
                        "name": proc["name"],
                        "cpu_percent": proc["cpu_percent"],
                        "memory_percent": proc["memory_percent"],
                        "username": proc.get("username", "unknown")
                    })
                
                # Подозрительные имена процессов
                suspicious_patterns = [
                    r"crypto", r"miner", r"botnet", r"malware", r"virus",
                    r"\.exe$", r"\.bat$", r"\.scr$", r"\.com$"
                ]
                
                for pattern in suspicious_patterns:
                    if re.search(pattern, proc["name"], re.IGNORECASE):
                        analysis["suspicious_processes"].append({
                            "pid": proc["pid"],
                            "name": proc["name"],
                            "pattern": pattern,
                            "risk_level": "high"
                        })
                        break
            
            # Генерация рекомендаций
            if analysis["resource_hogs"]:
                analysis["recommendations"].append({
                    "type": "resource_optimization",
                    "description": "Обнаружены процессы с высоким потреблением ресурсов",
                    "action": "review_processes",
                    "priority": "medium"
                })
            
            if analysis["suspicious_processes"]:
                analysis["recommendations"].append({
                    "type": "security_alert",
                    "description": "Обнаружены подозрительные процессы",
                    "action": "investigate_security",
                    "priority": "high"
                })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Ошибка умного управления процессами: {e}")
            return {"error": f"Ошибка анализа процессов: {str(e)}"}
    
    async def predict_system_issues(self, user_id: int) -> Dict[str, Any]:
        """Предсказание возможных проблем системы"""
        if not await self.role_manager.check_permission(user_id, "system", "view"):
            return {"error": "Нет доступа к системной информации"}
        
        try:
            # Анализ трендов (в реальной реализации здесь была бы база данных)
            predictions = {
                "timestamp": datetime.now().isoformat(),
                "predictions": [],
                "confidence": 0.0
            }
            
            system_info = await self.system_monitor.get_system_info(user_id)
            if not system_info:
                return {"error": "Не удалось получить системную информацию"}
            
            # Простые предсказания на основе текущих метрик
            cpu_usage = system_info["cpu"]["usage_percent"]
            memory_usage = system_info["memory"]["usage_percent"]
            disk_usage = system_info["disk"]["usage_percent"]
            
            # Предсказание проблем с памятью
            if memory_usage > 80:
                predictions["predictions"].append({
                    "type": "memory_shortage",
                    "probability": 0.8,
                    "timeframe": "1-2 часа",
                    "description": "Высокая вероятность нехватки памяти",
                    "mitigation": "Освободите память или добавьте swap"
                })
            
            # Предсказание проблем с диском
            if disk_usage > 90:
                predictions["predictions"].append({
                    "type": "disk_full",
                    "probability": 0.9,
                    "timeframe": "несколько часов",
                    "description": "Диск может заполниться",
                    "mitigation": "Очистите временные файлы и логи"
                })
            
            # Предсказание проблем с температурой
            if system_info["temperature"]["current"] and system_info["temperature"]["current"] > 75:
                predictions["predictions"].append({
                    "type": "overheating",
                    "probability": 0.7,
                    "timeframe": "30-60 минут",
                    "description": "Риск перегрева системы",
                    "mitigation": "Снизьте нагрузку или улучшите охлаждение"
                })
            
            # Расчет общего уровня уверенности
            if predictions["predictions"]:
                total_probability = sum(p["probability"] for p in predictions["predictions"])
                predictions["confidence"] = total_probability / len(predictions["predictions"])
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Ошибка предсказания проблем: {e}")
            return {"error": f"Ошибка предсказания: {str(e)}"}
    
    async def auto_optimize_system(self, user_id: int) -> Dict[str, Any]:
        """Автоматическая оптимизация системы"""
        if not await self.role_manager.check_permission(user_id, "system", "settings"):
            return {"error": "Нет прав для изменения настроек системы"}
        
        if not self.auto_optimization:
            return {"error": "Автоматическая оптимизация отключена"}
        
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "actions_taken": [],
                "improvements": [],
                "warnings": []
            }
            
            system_info = await self.system_monitor.get_system_info(user_id)
            if not system_info:
                return {"error": "Не удалось получить системную информацию"}
            
            # Автоматическая очистка логов (если они слишком большие)
            log_size = await self._check_log_size()
            if log_size > 100 * 1024 * 1024:  # 100MB
                await self._cleanup_old_logs()
                optimization_results["actions_taken"].append({
                    "action": "cleanup_logs",
                    "description": "Очистка старых логов",
                    "space_freed": "~50MB"
                })
            
            # Автоматическая оптимизация процессов
            processes = await self.process_manager.get_all_processes(user_id, limit=20)
            if processes:
                for proc in processes:
                    # Завершение зависших процессов
                    if proc["cpu_percent"] > 90 and proc["memory_percent"] > 20:
                        # В реальной реализации здесь была бы логика завершения
                        optimization_results["warnings"].append({
                            "type": "high_resource_process",
                            "pid": proc["pid"],
                            "name": proc["name"],
                            "description": "Процесс потребляет много ресурсов"
                        })
            
            # Отправка уведомления о результатах оптимизации
            if optimization_results["actions_taken"]:
                await self.notification_manager.send_custom_notification(
                    f"🤖 Автоматическая оптимизация завершена\n\n"
                    f"Выполнено действий: {len(optimization_results['actions_taken'])}\n"
                    f"Предупреждений: {len(optimization_results['warnings'])}",
                    [user_id],
                    "info"
                )
            
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Ошибка автоматической оптимизации: {e}")
            return {"error": f"Ошибка оптимизации: {str(e)}"}
    
    async def _check_log_size(self) -> int:
        """Проверка размера логов"""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return 0
            
            total_size = 0
            for log_file in log_dir.rglob("*.log"):
                total_size += log_file.stat().st_size
            
            return total_size
        except Exception as e:
            self.logger.error(f"Ошибка проверки размера логов: {e}")
            return 0
    
    async def _cleanup_old_logs(self):
        """Очистка старых логов"""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned_files = 0
            
            for log_file in log_dir.rglob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned_files += 1
            
            self.logger.info(f"Очищено {cleaned_files} старых лог-файлов")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки логов: {e}")
    
    async def get_ai_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение ИИ-рекомендаций для пользователя"""
        recommendations = []
        
        try:
            # Анализ системы
            system_analysis = await self.analyze_system_health(user_id)
            if "issues" in system_analysis:
                for issue in system_analysis["issues"]:
                    recommendations.append({
                        "type": "system_issue",
                        "priority": issue["severity"],
                        "title": issue["message"],
                        "description": issue["recommendation"],
                        "category": "system"
                    })
            
            # Анализ процессов
            process_analysis = await self.smart_process_management(user_id)
            if "recommendations" in process_analysis:
                for rec in process_analysis["recommendations"]:
                    recommendations.append({
                        "type": "process_optimization",
                        "priority": rec["priority"],
                        "title": rec["description"],
                        "description": f"Действие: {rec['action']}",
                        "category": "processes"
                    })
            
            # Предсказания
            predictions = await self.predict_system_issues(user_id)
            if "predictions" in predictions:
                for pred in predictions["predictions"]:
                    recommendations.append({
                        "type": "prediction",
                        "priority": "high" if pred["probability"] > 0.8 else "medium",
                        "title": f"Предсказание: {pred['type']}",
                        "description": f"{pred['description']} (вероятность: {pred['probability']:.1%})",
                        "mitigation": pred["mitigation"],
                        "category": "prediction"
                    })
            
            # Сортировка по приоритету
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))
            
            return recommendations[:10]  # Возвращаем топ-10 рекомендаций
            
        except Exception as e:
            self.logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
    
    async def learn_from_actions(self, action_data: Dict[str, Any]):
        """Обучение на основе действий пользователя"""
        if not self.learning_mode:
            return
        
        try:
            self.action_history.append({
                "timestamp": datetime.now(),
                "action": action_data,
                "outcome": "pending"
            })
            
            # В реальной реализации здесь была бы логика машинного обучения
            # для улучшения рекомендаций на основе действий пользователя
            
        except Exception as e:
            self.logger.error(f"Ошибка обучения: {e}") 