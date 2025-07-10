import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
from aiohttp import web
import jwt
from pathlib import Path

class WebInterface:
    """Модуль веб-интерфейса для бота Селла"""
    
    def __init__(self, config: dict, role_manager, system_monitor, process_manager, cloud_storage):
        self.config = config.get("web_interface", {})
        self.role_manager = role_manager
        self.system_monitor = system_monitor
        self.process_manager = process_manager
        self.cloud_storage = cloud_storage
        self.logger = logging.getLogger(__name__)
        
        # Настройки веб-интерфейса
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8080)
        self.secret_key = self.config.get("secret_key", "your-secret-key")
        self.enabled = self.config.get("enabled", False)
        
        # Сессии пользователей
        self.sessions = {}  # {session_id: user_data}
        
    async def start_server(self):
        """Запуск веб-сервера"""
        if not self.enabled:
            return
            
        app = web.Application()
        
        # Настройка маршрутов
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/api/system', self.api_system_handler)
        app.router.add_get('/api/processes', self.api_processes_handler)
        app.router.add_get('/api/storage', self.api_storage_handler)
        app.router.add_post('/api/login', self.api_login_handler)
        app.router.add_post('/api/logout', self.api_logout_handler)
        
        # Статические файлы
        app.router.add_static('/static', Path('web/static'))
        
        # Middleware для аутентификации
        app.middlewares.append(self.auth_middleware)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        self.logger.info(f"Веб-интерфейс запущен на http://{self.host}:{self.port}")
    
    async def auth_middleware(self, request, handler):
        """Middleware для аутентификации"""
        # Пропускаем публичные маршруты
        if request.path in ['/', '/api/login', '/static']:
            return await handler(request)
        
        # Проверка токена
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                return web.json_response({'error': 'Invalid token'}, status=401)
            
            request['user_id'] = user_id
            return await handler(request)
        except jwt.InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
    
    async def index_handler(self, request):
        """Главная страница"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Селла - Панель управления</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="#">
                        <i class="fas fa-robot"></i> Селла
                    </a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="#" id="loginBtn">Войти</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-server"></i> Система
                                </h5>
                                <div id="systemInfo">Загрузка...</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-robot"></i> Процессы
                                </h5>
                                <div id="processesInfo">Загрузка...</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-cloud"></i> Хранилище
                                </h5>
                                <div id="storageInfo">Загрузка...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script src="/static/js/app.js"></script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def api_login_handler(self, request):
        """API для входа в систему"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            password = data.get('password')
            
            # Проверка пользователя
            user_info = await self.role_manager.get_user_info(int(user_id))
            if not user_info:
                return web.json_response({'error': 'User not found'}, status=401)
            
            # В реальной реализации здесь была бы проверка пароля
            # Пока просто проверяем существование пользователя
            
            # Создание токена
            token = jwt.encode({
                'user_id': user_id,
                'name': user_info.get('name', 'Unknown'),
                'role': user_info.get('role', 'user'),
                'exp': datetime.utcnow().timestamp() + 3600  # 1 час
            }, self.secret_key, algorithm='HS256')
            
            return web.json_response({
                'token': token,
                'user': {
                    'id': user_id,
                    'name': user_info.get('name'),
                    'role': user_info.get('role')
                }
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка входа: {e}")
            return web.json_response({'error': 'Login failed'}, status=500)
    
    async def api_logout_handler(self, request):
        """API для выхода из системы"""
        return web.json_response({'message': 'Logged out successfully'})
    
    async def api_system_handler(self, request):
        """API для получения системной информации"""
        try:
            user_id = request.get('user_id')
            if not user_id:
                return web.json_response({'error': 'Unauthorized'}, status=401)
            
            system_info = await self.system_monitor.get_system_info(int(user_id))
            if not system_info:
                return web.json_response({'error': 'System info not available'}, status=500)
            
            return web.json_response(system_info)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения системной информации: {e}")
            return web.json_response({'error': 'Failed to get system info'}, status=500)
    
    async def api_processes_handler(self, request):
        """API для получения информации о процессах"""
        try:
            user_id = request.get('user_id')
            if not user_id:
                return web.json_response({'error': 'Unauthorized'}, status=401)
            
            processes = await self.process_manager.get_bots_status(int(user_id))
            if not processes:
                return web.json_response({'error': 'Processes info not available'}, status=500)
            
            return web.json_response(processes)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о процессах: {e}")
            return web.json_response({'error': 'Failed to get processes info'}, status=500)
    
    async def api_storage_handler(self, request):
        """API для получения информации о хранилище"""
        try:
            user_id = request.get('user_id')
            if not user_id:
                return web.json_response({'error': 'Unauthorized'}, status=401)
            
            storage_info = await self.cloud_storage.get_storage_usage(int(user_id))
            if not storage_info:
                return web.json_response({'error': 'Storage info not available'}, status=500)
            
            return web.json_response(storage_info)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о хранилище: {e}")
            return web.json_response({'error': 'Failed to get storage info'}, status=500)
    
    async def generate_api_token(self, user_id: int, expires_in: int = 3600) -> str:
        """Генерация API токена для пользователя"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow().timestamp() + expires_in
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    async def validate_api_token(self, token: str) -> Optional[int]:
        """Проверка API токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload.get('user_id')
        except jwt.InvalidTokenError:
            return None 