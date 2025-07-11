"""
Модуль системной аналитики с использованием plotly
Создает интерактивные графики для мониторинга системы
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import psutil
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio
import aiofiles


class SystemAnalytics:
    """Класс для создания аналитических графиков системы"""
    
    def __init__(self, storage_path: str = "analytics/charts"):
        self.storage_path = storage_path
        self.ensure_storage_dir()
        
    def ensure_storage_dir(self):
        """Создает директорию для хранения графиков"""
        os.makedirs(self.storage_path, exist_ok=True)
        
    def get_system_stats(self) -> Dict:
        """Получает текущую статистику системы"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters(),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_cpu_memory_chart(self, data_points: List[Dict]) -> str:
        """Создает график CPU и памяти"""
        if len(data_points) < 2:
            return self._create_empty_chart("Недостаточно данных для графика")
            
        timestamps = [point['timestamp'] for point in data_points]
        cpu_values = [point['cpu_percent'] for point in data_points]
        memory_values = [point['memory_percent'] for point in data_points]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Использование CPU (%)', 'Использование памяти (%)'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_values, mode='lines+markers', 
                      name='CPU', line=dict(color='#ff6b6b')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=memory_values, mode='lines+markers', 
                      name='Память', line=dict(color='#4ecdc4')),
            row=2, col=1
        )
        
        fig.update_layout(
            title='Мониторинг системы',
            height=600,
            showlegend=True,
            template='plotly_white'
        )
        
        return self._save_chart(fig, "system_monitoring")
    
    def create_disk_usage_chart(self) -> str:
        """Создает круговую диаграмму использования диска"""
        disk_usage = psutil.disk_usage('/')
        used_gb = disk_usage.used / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        
        fig = go.Figure(data=[go.Pie(
            labels=['Использовано', 'Свободно'],
            values=[used_gb, free_gb],
            hole=0.3,
            marker_colors=['#ff6b6b', '#4ecdc4']
        )])
        
        fig.update_layout(
            title=f'Использование диска (Всего: {disk_usage.total / (1024**3):.1f} ГБ)',
            height=400
        )
        
        return self._save_chart(fig, "disk_usage")
    
    def create_network_chart(self, data_points: List[Dict]) -> str:
        """Создает график сетевой активности"""
        if len(data_points) < 2:
            return self._create_empty_chart("Недостаточно данных для сетевого графика")
            
        timestamps = [point['timestamp'] for point in data_points]
        bytes_sent = [point['network_io'].bytes_sent for point in data_points]
        bytes_recv = [point['network_io'].bytes_recv for point in data_points]
        
        # Конвертируем в МБ
        mb_sent = [b / (1024**2) for b in bytes_sent]
        mb_recv = [b / (1024**2) for b in bytes_recv]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps, y=mb_sent, mode='lines+markers',
            name='Отправлено (МБ)', line=dict(color='#45b7d1')
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps, y=mb_recv, mode='lines+markers',
            name='Получено (МБ)', line=dict(color='#96ceb4')
        ))
        
        fig.update_layout(
            title='Сетевая активность',
            xaxis_title='Время',
            yaxis_title='МБ',
            height=400,
            template='plotly_white'
        )
        
        return self._save_chart(fig, "network_activity")
    
    def create_processes_chart(self, top_n: int = 10) -> str:
        """Создает график топ процессов по использованию ресурсов"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Сортируем по CPU
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:top_n]
        
        names = [p['name'][:20] for p in top_processes]  # Обрезаем длинные имена
        cpu_values = [p['cpu_percent'] for p in top_processes]
        memory_values = [p['memory_percent'] for p in top_processes]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Топ процессов по CPU (%)', 'Топ процессов по памяти (%)'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        fig.add_trace(
            go.Bar(x=names, y=cpu_values, name='CPU', marker_color='#ff6b6b'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=names, y=memory_values, name='Память', marker_color='#4ecdc4'),
            row=1, col=2
        )
        
        fig.update_layout(
            title=f'Топ {top_n} процессов',
            height=500,
            showlegend=False
        )
        
        return self._save_chart(fig, "top_processes")
    
    def create_system_summary(self) -> str:
        """Создает сводный график системы"""
        # Получаем данные
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Создаем дашборд
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'CPU', 'Память', 
                'Диск', 'Сеть'
            ),
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}],
                [{"type": "indicator"}, {"type": "bar"}]
            ]
        )
        
        # CPU индикатор
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=cpu_percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "yellow"},
                           {'range': [80, 100], 'color': "red"}
                       ],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': 90
                       }}
            ),
            row=1, col=1
        )
        
        # Память индикатор
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=memory.percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Память (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkgreen"},
                       'steps': [
                           {'range': [0, 60], 'color': "lightgray"},
                           {'range': [60, 85], 'color': "yellow"},
                           {'range': [85, 100], 'color': "red"}
                       ],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': 90
                       }}
            ),
            row=1, col=2
        )
        
        # Диск индикатор
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=disk.percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Диск (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkred"},
                       'steps': [
                           {'range': [0, 70], 'color': "lightgray"},
                           {'range': [70, 90], 'color': "yellow"},
                           {'range': [90, 100], 'color': "red"}
                       ],
                       'threshold': {
                           'line': {'color': "red", 'width': 4},
                           'thickness': 0.75,
                           'value': 95
                       }}
            ),
            row=2, col=1
        )
        
        # Сеть (простая статистика)
        network = psutil.net_io_counters()
        fig.add_trace(
            go.Bar(
                x=['Отправлено', 'Получено'],
                y=[network.bytes_sent / (1024**2), network.bytes_recv / (1024**2)],
                name='МБ',
                marker_color=['#45b7d1', '#96ceb4']
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Сводка системы',
            height=600,
            showlegend=False
        )
        
        return self._save_chart(fig, "system_summary")
    
    def _save_chart(self, fig, filename: str) -> str:
        """Сохраняет график в HTML файл"""
        filepath = os.path.join(self.storage_path, f"{filename}.html")
        
        # Добавляем метаданные
        fig.update_layout(
            title_x=0.5,
            font=dict(size=12),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Сохраняем как интерактивный HTML
        fig.write_html(filepath, include_plotlyjs=True)
        return filepath
    
    def _create_empty_chart(self, message: str) -> str:
        """Создает пустой график с сообщением"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Нет данных",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300
        )
        return self._save_chart(fig, "empty_chart")
    
    async def collect_data_points(self, duration: int = 60, interval: int = 2) -> List[Dict]:
        """Собирает данные в течение указанного времени"""
        data_points = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            data_points.append(self.get_system_stats())
            await asyncio.sleep(interval)
            
        return data_points
    
    def get_available_charts(self) -> List[str]:
        """Возвращает список доступных графиков"""
        charts = []
        if os.path.exists(self.storage_path):
            for file in os.listdir(self.storage_path):
                if file.endswith('.html'):
                    charts.append(file.replace('.html', ''))
        return charts
    
    def cleanup_old_charts(self, max_age_hours: int = 24):
        """Удаляет старые графики"""
        if not os.path.exists(self.storage_path):
            return
            
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file in os.listdir(self.storage_path):
            if file.endswith('.html'):
                filepath = os.path.join(self.storage_path, file)
                if current_time - os.path.getmtime(filepath) > max_age_seconds:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass


# Глобальный экземпляр для использования в боте
analytics = SystemAnalytics() 