import os
import time
from analytics.system_analytics import SystemAnalytics


def test_cpu_memory_chart():
    analytics = SystemAnalytics("analytics/test_charts")
    # Генерируем тестовые данные
    data_points = []
    for i in range(10):
        data_points.append({
            'cpu_percent': 10 + i * 5,
            'memory_percent': 30 + i * 2,
            'disk_percent': 50,
            'network_io': type('obj', (object,), {'bytes_sent': 1000 * i, 'bytes_recv': 2000 * i})(),
            'timestamp': f"2024-01-01 12:00:{i:02d}"
        })
    path = analytics.create_cpu_memory_chart(data_points)
    assert os.path.exists(path), f"Файл {path} не создан"
    print("CPU/Memory chart: OK")

def test_disk_chart():
    analytics = SystemAnalytics("analytics/test_charts")
    path = analytics.create_disk_usage_chart()
    assert os.path.exists(path), f"Файл {path} не создан"
    print("Disk chart: OK")

def test_network_chart():
    analytics = SystemAnalytics("analytics/test_charts")
    data_points = []
    for i in range(10):
        data_points.append({
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'network_io': type('obj', (object,), {'bytes_sent': 1000 * i, 'bytes_recv': 2000 * i})(),
            'timestamp': f"2024-01-01 12:00:{i:02d}"
        })
    path = analytics.create_network_chart(data_points)
    assert os.path.exists(path), f"Файл {path} не создан"
    print("Network chart: OK")

def test_processes_chart():
    analytics = SystemAnalytics("analytics/test_charts")
    path = analytics.create_processes_chart(top_n=5)
    assert os.path.exists(path), f"Файл {path} не создан"
    print("Processes chart: OK")

def test_system_summary():
    analytics = SystemAnalytics("analytics/test_charts")
    path = analytics.create_system_summary()
    assert os.path.exists(path), f"Файл {path} не создан"
    print("System summary: OK")

def test_empty_chart():
    analytics = SystemAnalytics("analytics/test_charts")
    path = analytics._create_empty_chart("Нет данных для теста")
    assert os.path.exists(path), f"Файл {path} не создан"
    print("Empty chart: OK")

def cleanup():
    # Удаляем тестовые файлы
    import shutil
    shutil.rmtree("analytics/test_charts", ignore_errors=True)

if __name__ == "__main__":
    cleanup()
    test_cpu_memory_chart()
    test_disk_chart()
    test_network_chart()
    test_processes_chart()
    test_system_summary()
    test_empty_chart()
    print("Все тесты plotly-аналитики успешно пройдены!")
    cleanup() 