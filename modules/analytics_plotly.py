import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import statistics
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
import base64

class AnalyticsPlotly:
    """Модуль аналитики с использованием plotly вместо matplotlib"""
    
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
    
    async def create_performance_chart(self, user_id: int, metric_type: str = "system", period: str = "24h") -> Optional[str]:
        """Создание графика производительности с plotly"""
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
            
            # Создание графика с plotly
            if metric_type == "system":
                fig = self._create_system_chart(data)
            elif metric_type == "processes":
                fig = self._create_processes_chart(data)
            else:
                fig = self._create_generic_chart(data, metric_type)
            
            # Сохранение в изображение
            img_bytes = fig.to_image(format="png", width=800, height=600)
            
            # Кодирование в base64
            image_base64 = base64.b64encode(img_bytes).decode()
            
            return image_base64
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика с plotly: {e}")
            return None
    
    def _create_system_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Создание графика системных метрик"""
        timestamps = [datetime.fromisoformat(metric["timestamp"]) for metric in data]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('CPU Usage', 'Memory Usage', 'Disk Usage', 'Network Activity'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # CPU
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[metric["cpu_usage"] for metric in data],
                name="CPU %",
                line=dict(color='red', width=2)
            ),
            row=1, col=1
        )
        
        # Memory
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[metric["memory_usage"] for metric in data],
                name="Memory %",
                line=dict(color='blue', width=2)
            ),
            row=1, col=2
        )
        
        # Disk
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[metric["disk_usage"] for metric in data],
                name="Disk %",
                line=dict(color='green', width=2)
            ),
            row=2, col=1
        )
        
        # Network
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[metric.get("network_upload", 0) for metric in data],
                name="Upload (MB/s)",
                line=dict(color='orange', width=2)
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="System Performance Metrics",
            height=600,
            showlegend=True,
            template="plotly_white"
        )
        
        return fig
    
    def _create_processes_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Создание графика процессов"""
        timestamps = [datetime.fromisoformat(metric["timestamp"]) for metric in data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[metric["total_cpu_usage"] for metric in data],
            name="Total CPU %",
            line=dict(color='purple', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[metric["total_memory_usage"] for metric in data],
            name="Total Memory (MB)",
            line=dict(color='brown', width=2),
            yaxis="y2"
        ))
        
        fig.update_layout(
            title="Process Performance Metrics",
            xaxis_title="Time",
            yaxis=dict(title="CPU Usage %", side="left"),
            yaxis2=dict(title="Memory Usage (MB)", side="right", overlaying="y"),
            template="plotly_white",
            height=500
        )
        
        return fig
    
    def _create_generic_chart(self, data: List[Dict[str, Any]], metric_type: str) -> go.Figure:
        """Создание общего графика"""
        timestamps = [datetime.fromisoformat(metric["timestamp"]) for metric in data]
        
        # Определяем доступные метрики
        available_metrics = [key for key in data[0].keys() if key != "timestamp" and isinstance(data[0][key], (int, float))]
        
        fig = go.Figure()
        
        for metric in available_metrics[:5]:  # Максимум 5 метрик
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=[point[metric] for point in data],
                name=metric.replace("_", " ").title(),
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title=f"{metric_type.title()} Metrics",
            xaxis_title="Time",
            yaxis_title="Value",
            template="plotly_white",
            height=500
        )
        
        return fig
    
    async def create_storage_chart(self, user_id: int) -> Optional[str]:
        """Создание графика использования хранилища"""
        try:
            storage_usage = await self.cloud_storage.get_storage_usage(user_id)
            
            # Создаем круговую диаграмму
            fig = go.Figure(data=[go.Pie(
                labels=['Использовано', 'Свободно'],
                values=[storage_usage['total_size'], storage_usage['max_size'] - storage_usage['total_size']],
                hole=0.3
            )])
            
            fig.update_layout(
                title="Storage Usage",
                annotations=[dict(text=f"{storage_usage['usage_percent']:.1f}%", x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            img_bytes = fig.to_image(format="png", width=600, height=400)
            return base64.b64encode(img_bytes).decode()
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика хранилища: {e}")
            return None
    
    async def create_memory_history_chart(self, user_id: int, hours: int = 24) -> Optional[str]:
        """Создание графика истории использования памяти"""
        try:
            memory_history = self.system_monitor.get_memory_history(hours)
            
            if not memory_history:
                return None
            
            timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in memory_history]
            percents = [entry["percent"] for entry in memory_history]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=percents,
                fill='tonexty',
                name="Memory Usage %",
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title=f"Memory Usage History ({hours}h)",
                xaxis_title="Time",
                yaxis_title="Memory Usage %",
                template="plotly_white",
                height=400
            )
            
            img_bytes = fig.to_image(format="png", width=800, height=400)
            return base64.b64encode(img_bytes).decode()
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика истории памяти: {e}")
            return None 