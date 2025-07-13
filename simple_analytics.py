#!/usr/bin/env python3
"""
Простая система аналитики для Termux
Работает без matplotlib/plotly, использует только текст и JSON
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psutil

class SimpleAnalytics:
    def __init__(self, data_file: str = "analytics_data.json"):
        self.data_file = data_file
        self.data = self.load_data()
    
    def load_data(self) -> Dict[str, Any]:
        """Загружает данные аналитики из JSON файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "system_stats": [],
            "bot_events": [],
            "user_activity": {},
            "performance_metrics": []
        }
    
    def save_data(self):
        """Сохраняет данные в JSON файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def record_system_stats(self):
        """Записывает системную статистику"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        self.data["system_stats"].append(stats)
        
        # Ограничиваем количество записей
        if len(self.data["system_stats"]) > 1000:
            self.data["system_stats"] = self.data["system_stats"][-500:]
        
        self.save_data()
    
    def record_bot_event(self, event_type: str, details: str = ""):
        """Записывает событие бота"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        self.data["bot_events"].append(event)
        
        if len(self.data["bot_events"]) > 500:
            self.data["bot_events"] = self.data["bot_events"][-250:]
        
        self.save_data()
    
    def record_user_activity(self, user_id: int, action: str):
        """Записывает активность пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.data["user_activity"]:
            self.data["user_activity"][user_id_str] = {
                "actions": [],
                "last_seen": None,
                "total_actions": 0
            }
        
        self.data["user_activity"][user_id_str]["actions"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action
        })
        self.data["user_activity"][user_id_str]["last_seen"] = datetime.now().isoformat()
        self.data["user_activity"][user_id_str]["total_actions"] += 1
        
        # Ограничиваем количество действий на пользователя
        if len(self.data["user_activity"][user_id_str]["actions"]) > 100:
            self.data["user_activity"][user_id_str]["actions"] = \
                self.data["user_activity"][user_id_str]["actions"][-50:]
        
        self.save_data()
    
    def get_system_summary(self) -> str:
        """Возвращает текстовую сводку системной статистики"""
        if not self.data["system_stats"]:
            return "Нет данных о системе"
        
        recent_stats = self.data["system_stats"][-10:]  # Последние 10 записей
        
        avg_cpu = sum(s["cpu_percent"] for s in recent_stats) / len(recent_stats)
        avg_memory = sum(s["memory_percent"] for s in recent_stats) / len(recent_stats)
        avg_disk = sum(s["disk_percent"] for s in recent_stats) / len(recent_stats)
        
        current_stats = self.data["system_stats"][-1]
        
        summary = f"""
📊 СИСТЕМНАЯ СТАТИСТИКА

🖥️ CPU: {current_stats['cpu_percent']:.1f}% (среднее: {avg_cpu:.1f}%)
💾 Память: {current_stats['memory_percent']:.1f}% (среднее: {avg_memory:.1f}%)
💿 Диск: {current_stats['disk_percent']:.1f}% (среднее: {avg_disk:.1f}%)
⏰ Последнее обновление: {current_stats['timestamp'][:19]}
        """
        return summary.strip()
    
    def get_bot_events_summary(self, hours: int = 24) -> str:
        """Возвращает сводку событий бота за последние часы"""
        if not self.data["bot_events"]:
            return "Нет событий бота"
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            e for e in self.data["bot_events"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]
        
        if not recent_events:
            return f"Нет событий за последние {hours} часов"
        
        event_counts = {}
        for event in recent_events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        summary = f"🤖 СОБЫТИЯ БОТА (за {hours}ч):\n\n"
        for event_type, count in sorted(event_counts.items()):
            summary += f"• {event_type}: {count}\n"
        
        summary += f"\nВсего событий: {len(recent_events)}"
        return summary
    
    def get_user_activity_summary(self) -> str:
        """Возвращает сводку активности пользователей"""
        if not self.data["user_activity"]:
            return "Нет данных о пользователях"
        
        # Сортируем пользователей по активности
        sorted_users = sorted(
            self.data["user_activity"].items(),
            key=lambda x: x[1]["total_actions"],
            reverse=True
        )
        
        summary = "👥 АКТИВНОСТЬ ПОЛЬЗОВАТЕЛЕЙ:\n\n"
        
        for user_id, data in sorted_users[:10]:  # Топ 10 пользователей
            last_seen = data["last_seen"][:19] if data["last_seen"] else "Никогда"
            summary += f"• ID {user_id}: {data['total_actions']} действий\n"
            summary += f"  Последний раз: {last_seen}\n\n"
        
        total_users = len(self.data["user_activity"])
        total_actions = sum(data["total_actions"] for data in self.data["user_activity"].values())
        
        summary += f"Всего пользователей: {total_users}"
        summary += f"\nВсего действий: {total_actions}"
        
        return summary
    
    def get_performance_report(self) -> str:
        """Возвращает полный отчет о производительности"""
        report = "📈 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ\n"
        report += "=" * 40 + "\n\n"
        
        report += self.get_system_summary() + "\n\n"
        report += self.get_bot_events_summary() + "\n\n"
        report += self.get_user_activity_summary()
        
        return report
    
    def cleanup_old_data(self, days: int = 30):
        """Удаляет старые данные"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Очищаем системную статистику
        self.data["system_stats"] = [
            s for s in self.data["system_stats"]
            if datetime.fromisoformat(s["timestamp"]) > cutoff_time
        ]
        
        # Очищаем события бота
        self.data["bot_events"] = [
            e for e in self.data["bot_events"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]
        
        # Очищаем действия пользователей
        for user_data in self.data["user_activity"].values():
            user_data["actions"] = [
                a for a in user_data["actions"]
                if datetime.fromisoformat(a["timestamp"]) > cutoff_time
            ]
        
        self.save_data()

# Пример использования
if __name__ == "__main__":
    analytics = SimpleAnalytics()
    
    # Записываем системную статистику
    analytics.record_system_stats()
    
    # Записываем событие бота
    analytics.record_bot_event("startup", "Бот запущен")
    
    # Записываем активность пользователя
    analytics.record_user_activity(123456789, "отправил сообщение")
    
    # Выводим отчет
    print(analytics.get_performance_report()) 