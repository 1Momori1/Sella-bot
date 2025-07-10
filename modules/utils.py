import os
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class Utils:
    """Утилиты для проекта Селла"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def format_uptime(seconds: int) -> str:
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
    
    @staticmethod
    def generate_file_hash(content: bytes) -> str:
        """Генерация хеша файла"""
        return hashlib.md5(content).hexdigest()
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Безопасное имя файла"""
        # Удаляем небезопасные символы
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Получение расширения файла"""
        return os.path.splitext(filename)[1].lower().lstrip('.')
    
    @staticmethod
    def is_allowed_extension(filename: str, allowed_extensions: list) -> bool:
        """Проверка разрешенного расширения"""
        if not allowed_extensions:
            return True
        ext = Utils.get_file_extension(filename)
        return ext in allowed_extensions
    
    @staticmethod
    def create_backup_filename(original_name: str) -> str:
        """Создание имени файла для бэкапа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(original_name)
        return f"{name}_backup_{timestamp}{ext}"
    
    @staticmethod
    def parse_time_string(time_str: str) -> int:
        """Парсинг строки времени в секунды"""
        try:
            if 'd' in time_str:
                days = int(time_str.split('d')[0])
                return days * 86400
            elif 'h' in time_str:
                hours = int(time_str.split('h')[0])
                return hours * 3600
            elif 'm' in time_str:
                minutes = int(time_str.split('m')[0])
                return minutes * 60
            else:
                return int(time_str)
        except:
            return 0
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Валидация конфигурации"""
        required_fields = ['bot_token', 'admin_ids', 'users']
        
        for field in required_fields:
            if field not in config:
                logging.error(f"Отсутствует обязательное поле: {field}")
                return False
        
        if not config['bot_token'] or config['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
            logging.error("Не настроен токен бота")
            return False
        
        if not config['admin_ids']:
            logging.error("Не указаны администраторы")
            return False
        
        return True
    
    @staticmethod
    def setup_logging(config: Dict[str, Any]) -> None:
        """Настройка логирования"""
        log_config = config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'logs/sella_bot.log')
        
        # Создание директории для логов
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    @staticmethod
    def check_disk_space(path: str) -> Dict[str, Any]:
        """Проверка свободного места на диске"""
        try:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            
            return {
                'total': total,
                'free': free,
                'used': used,
                'percent_used': round((used / total) * 100, 2)
            }
        except Exception as e:
            logging.error(f"Ошибка проверки диска: {e}")
            return {'total': 0, 'free': 0, 'used': 0, 'percent_used': 0}
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Очистка пользовательского ввода"""
        # Удаляем потенциально опасные символы
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text.strip()
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """Форматирование временной метки"""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def is_valid_user_id(user_id: str) -> bool:
        """Проверка валидности ID пользователя"""
        try:
            int(user_id)
            return True
        except ValueError:
            return False 