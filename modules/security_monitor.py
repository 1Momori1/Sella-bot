import logging
import json
import asyncio
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
import re
import subprocess
import psutil
from pathlib import Path

class SecurityMonitor:
    """Модуль мониторинга безопасности и обнаружения угроз"""
    
    def __init__(self, config: dict, role_manager, system_monitor, process_manager, notification_manager):
        self.config = config.get("security", {})
        self.role_manager = role_manager
        self.system_monitor = system_monitor
        self.process_manager = process_manager
        self.notification_manager = notification_manager
        self.logger = logging.getLogger(__name__)
        
        # Настройки безопасности
        self.enabled = self.config.get("enabled", True)
        self.threat_detection = self.config.get("threat_detection", True)
        self.intrusion_prevention = self.config.get("intrusion_prevention", True)
        self.audit_logging = self.config.get("audit_logging", True)
        
        # База данных угроз и подозрительной активности
        self.threat_database = {
            "suspicious_processes": set(),
            "suspicious_connections": set(),
            "failed_login_attempts": {},
            "file_integrity_violations": [],
            "network_anomalies": []
        }
        
        # История событий безопасности
        self.security_events = []
        self.blocked_ips = set()
        self.suspicious_users = set()
        
        # Настройки мониторинга
        self.monitoring_interval = self.config.get("monitoring_interval", 30)
        self.max_failed_attempts = self.config.get("max_failed_attempts", 5)
        self.block_duration = self.config.get("block_duration", 3600)  # 1 час
        
    async def start_security_monitoring(self):
        """Запуск мониторинга безопасности"""
        if not self.enabled:
            return
        
        self.logger.info("Запуск мониторинга безопасности")
        
        # Запуск фоновых задач мониторинга
        asyncio.create_task(self._continuous_monitoring())
        asyncio.create_task(self._network_monitoring())
        asyncio.create_task(self._file_integrity_monitoring())
        
    async def _continuous_monitoring(self):
        """Непрерывный мониторинг системы"""
        while self.enabled:
            try:
                await self._check_system_security()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Ошибка непрерывного мониторинга: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _check_system_security(self):
        """Проверка безопасности системы"""
        try:
            # Проверка подозрительных процессов
            await self._detect_suspicious_processes()
            
            # Проверка сетевых соединений
            await self._detect_suspicious_connections()
            
            # Проверка файловой системы
            await self._check_file_integrity()
            
            # Проверка системных логов
            await self._analyze_system_logs()
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки безопасности: {e}")
    
    async def _detect_suspicious_processes(self):
        """Обнаружение подозрительных процессов"""
        try:
            processes = await self.process_manager.get_all_processes(123456789, limit=100)
            if not processes:
                return
            
            suspicious_patterns = [
                # Криптомайнеры
                r"xmrig", r"cpuminer", r"ccminer", r"ethminer", r"t-rex",
                r"nbminer", r"lolminer", r"teamredminer", r"phoenixminer",
                
                # Вредоносное ПО
                r"malware", r"virus", r"trojan", r"backdoor", r"keylogger",
                r"spyware", r"adware", r"ransomware", r"botnet",
                
                # Подозрительные расширения
                r"\.exe$", r"\.bat$", r"\.cmd$", r"\.scr$", r"\.com$",
                r"\.pif$", r"\.vbs$", r"\.js$", r"\.jar$",
                
                # Подозрительные имена
                r"crypto", r"miner", r"hash", r"coin", r"wallet",
                r"update", r"install", r"setup", r"service",
                
                # Сетевые сканеры и атаки
                r"nmap", r"masscan", r"hydra", r"medusa", r"sqlmap",
                r"nikto", r"dirb", r"gobuster", r"wfuzz"
            ]
            
            for proc in processes:
                process_name = proc["name"].lower()
                
                # Проверка по паттернам
                for pattern in suspicious_patterns:
                    if re.search(pattern, process_name, re.IGNORECASE):
                        await self._report_suspicious_process(proc, pattern)
                        break
                
                # Проверка аномального потребления ресурсов
                if proc["cpu_percent"] > 80 and proc["memory_percent"] > 20:
                    await self._report_resource_abuse(proc)
                
                # Проверка процессов с подозрительными аргументами
                if proc.get("cmdline"):
                    cmdline = " ".join(proc["cmdline"]).lower()
                    if any(keyword in cmdline for keyword in ["--mining", "--pool", "--wallet", "--hashrate"]):
                        await self._report_mining_activity(proc)
                        
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения подозрительных процессов: {e}")
    
    async def _detect_suspicious_connections(self):
        """Обнаружение подозрительных сетевых соединений"""
        try:
            connections = psutil.net_connections()
            
            suspicious_ports = {
                22, 23, 3389, 5900, 5901, 5902,  # SSH, Telnet, RDP, VNC
                1433, 3306, 5432, 1521,  # Базы данных
                80, 443, 8080, 8443,  # Веб-серверы
                25, 110, 143, 993, 995,  # Почта
                21, 20,  # FTP
                137, 138, 139, 445,  # SMB/NetBIOS
                53,  # DNS
                123,  # NTP
                161, 162,  # SNMP
                389, 636,  # LDAP
                636,  # LDAPS
                1433, 1434,  # SQL Server
                1521, 1526,  # Oracle
                3306,  # MySQL
                5432,  # PostgreSQL
                27017,  # MongoDB
                6379,  # Redis
                11211,  # Memcached
                9200,  # Elasticsearch
                5601,  # Kibana
                8080, 8081, 8082,  # Различные сервисы
                9000, 9001, 9002,  # Jenkins, другие
                3000, 3001, 3002,  # Node.js приложения
                5000, 5001, 5002,  # Flask, другие
                8000, 8001, 8002,  # Django, другие
            }
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    # Проверка подозрительных портов
                    if conn.raddr and conn.raddr.port in suspicious_ports:
                        await self._report_suspicious_connection(conn)
                    
                    # Проверка соединений с известными вредоносными IP
                    if conn.raddr and self._is_suspicious_ip(conn.raddr.ip):
                        await self._report_malicious_connection(conn)
                    
                    # Проверка множественных соединений
                    if self._has_multiple_connections(conn.raddr.ip if conn.raddr else None):
                        await self._report_connection_flood(conn)
                        
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения подозрительных соединений: {e}")
    
    async def _check_file_integrity(self):
        """Проверка целостности файлов"""
        try:
            critical_files = [
                "/etc/passwd", "/etc/shadow", "/etc/hosts",
                "/etc/ssh/sshd_config", "/etc/fstab",
                "/boot/grub/grub.cfg", "/etc/resolv.conf"
            ]
            
            for file_path in critical_files:
                if Path(file_path).exists():
                    current_hash = await self._calculate_file_hash(file_path)
                    stored_hash = self._get_stored_hash(file_path)
                    
                    if stored_hash and current_hash != stored_hash:
                        await self._report_file_integrity_violation(file_path, stored_hash, current_hash)
                    elif not stored_hash:
                        # Первый запуск - сохраняем хеш
                        self._store_file_hash(file_path, current_hash)
                        
        except Exception as e:
            self.logger.error(f"Ошибка проверки целостности файлов: {e}")
    
    async def _analyze_system_logs(self):
        """Анализ системных логов"""
        try:
            log_files = [
                "/var/log/auth.log",
                "/var/log/syslog",
                "/var/log/messages",
                "/var/log/secure"
            ]
            
            for log_file in log_files:
                if Path(log_file).exists():
                    await self._analyze_log_file(log_file)
                    
        except Exception as e:
            self.logger.error(f"Ошибка анализа системных логов: {e}")
    
    async def _analyze_log_file(self, log_file: str):
        """Анализ конкретного лог-файла"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Анализ последних 1000 строк
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            for line in recent_lines:
                # Поиск неудачных попыток входа
                if "Failed password" in line or "authentication failure" in line:
                    await self._analyze_failed_login(line)
                
                # Поиск подозрительной активности
                if any(keyword in line.lower() for keyword in ["suspicious", "malware", "virus", "attack"]):
                    await self._report_suspicious_log_entry(line)
                
                # Поиск попыток эскалации привилегий
                if "sudo" in line and "incorrect password" in line:
                    await self._report_privilege_escalation_attempt(line)
                    
        except Exception as e:
            self.logger.error(f"Ошибка анализа лог-файла {log_file}: {e}")
    
    async def _report_suspicious_process(self, process: Dict[str, Any], pattern: str):
        """Отчет о подозрительном процессе"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "suspicious_process",
            "severity": "high",
            "process": {
                "pid": process["pid"],
                "name": process["name"],
                "cmdline": process.get("cmdline", []),
                "cpu_percent": process["cpu_percent"],
                "memory_percent": process["memory_percent"]
            },
            "pattern": pattern,
            "description": f"Обнаружен подозрительный процесс, соответствующий паттерну: {pattern}"
        }
        
        self.security_events.append(event)
        self.threat_database["suspicious_processes"].add(process["name"])
        
        # Уведомление администраторов
        await self._notify_security_event(event)
        
        self.logger.warning(f"Подозрительный процесс: {process['name']} (PID: {process['pid']})")
    
    async def _report_resource_abuse(self, process: Dict[str, Any]):
        """Отчет о злоупотреблении ресурсами"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "resource_abuse",
            "severity": "medium",
            "process": {
                "pid": process["pid"],
                "name": process["name"],
                "cpu_percent": process["cpu_percent"],
                "memory_percent": process["memory_percent"]
            },
            "description": "Процесс потребляет аномально много ресурсов"
        }
        
        self.security_events.append(event)
        self.logger.warning(f"Злоупотребление ресурсами: {process['name']} (CPU: {process['cpu_percent']}%, RAM: {process['memory_percent']}%)")
    
    async def _report_mining_activity(self, process: Dict[str, Any]):
        """Отчет о майнинге"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "mining_activity",
            "severity": "critical",
            "process": {
                "pid": process["pid"],
                "name": process["name"],
                "cmdline": process.get("cmdline", [])
            },
            "description": "Обнаружена активность криптомайнинга"
        }
        
        self.security_events.append(event)
        
        # Немедленное уведомление
        await self._notify_security_event(event)
        
        self.logger.critical(f"КРИПТОМАЙНИНГ: {process['name']} (PID: {process['pid']})")
    
    async def _report_suspicious_connection(self, connection):
        """Отчет о подозрительном соединении"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "suspicious_connection",
            "severity": "medium",
            "connection": {
                "local_address": f"{connection.laddr.ip}:{connection.laddr.port}",
                "remote_address": f"{connection.raddr.ip}:{connection.raddr.port}",
                "status": connection.status,
                "pid": connection.pid
            },
            "description": f"Подозрительное соединение на порт {connection.raddr.port}"
        }
        
        self.security_events.append(event)
        self.logger.warning(f"Подозрительное соединение: {connection.raddr.ip}:{connection.raddr.port}")
    
    async def _report_malicious_connection(self, connection):
        """Отчет о вредоносном соединении"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "malicious_connection",
            "severity": "high",
            "connection": {
                "local_address": f"{connection.laddr.ip}:{connection.laddr.port}",
                "remote_address": f"{connection.raddr.ip}:{connection.raddr.port}",
                "status": connection.status,
                "pid": connection.pid
            },
            "description": "Соединение с известным вредоносным IP"
        }
        
        self.security_events.append(event)
        await self._notify_security_event(event)
        
        self.logger.critical(f"ВРЕДОНОСНОЕ СОЕДИНЕНИЕ: {connection.raddr.ip}:{connection.raddr.port}")
    
    async def _report_file_integrity_violation(self, file_path: str, original_hash: str, current_hash: str):
        """Отчет о нарушении целостности файла"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "file_integrity_violation",
            "severity": "critical",
            "file": file_path,
            "original_hash": original_hash,
            "current_hash": current_hash,
            "description": f"Нарушена целостность критического файла: {file_path}"
        }
        
        self.security_events.append(event)
        self.threat_database["file_integrity_violations"].append(event)
        
        await self._notify_security_event(event)
        
        self.logger.critical(f"НАРУШЕНИЕ ЦЕЛОСТНОСТИ ФАЙЛА: {file_path}")
    
    async def _analyze_failed_login(self, log_line: str):
        """Анализ неудачной попытки входа"""
        try:
            # Извлечение IP адреса из лог-строки
            ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', log_line)
            if ip_match:
                ip_address = ip_match.group(1)
                
                if ip_address not in self.threat_database["failed_login_attempts"]:
                    self.threat_database["failed_login_attempts"][ip_address] = {
                        "count": 0,
                        "first_attempt": datetime.now(),
                        "last_attempt": datetime.now()
                    }
                
                self.threat_database["failed_login_attempts"][ip_address]["count"] += 1
                self.threat_database["failed_login_attempts"][ip_address]["last_attempt"] = datetime.now()
                
                # Проверка на брутфорс атаку
                if self.threat_database["failed_login_attempts"][ip_address]["count"] >= self.max_failed_attempts:
                    await self._report_bruteforce_attack(ip_address)
                    
        except Exception as e:
            self.logger.error(f"Ошибка анализа неудачного входа: {e}")
    
    async def _report_bruteforce_attack(self, ip_address: str):
        """Отчет о брутфорс атаке"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "bruteforce_attack",
            "severity": "high",
            "ip_address": ip_address,
            "attempts": self.threat_database["failed_login_attempts"][ip_address]["count"],
            "description": f"Брутфорс атака с IP {ip_address}"
        }
        
        self.security_events.append(event)
        self.blocked_ips.add(ip_address)
        
        await self._notify_security_event(event)
        
        self.logger.critical(f"БРУТФОРС АТАКА: {ip_address}")
    
    async def _notify_security_event(self, event: Dict[str, Any]):
        """Уведомление о событии безопасности"""
        try:
            # Получение списка администраторов
            admin_ids = []
            for user_id_str, user_info in self.role_manager.users.items():
                if user_info.get("role") == "admin":
                    admin_ids.append(int(user_id_str))
            
            if admin_ids:
                message = f"🚨 **СОБЫТИЕ БЕЗОПАСНОСТИ**\n\n"
                message += f"**Тип:** {event['type']}\n"
                message += f"**Уровень:** {event['severity']}\n"
                message += f"**Описание:** {event['description']}\n"
                message += f"**Время:** {event['timestamp']}"
                
                await self.notification_manager.send_custom_notification(
                    message, admin_ids, "security"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления о безопасности: {e}")
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Проверка IP на подозрительность"""
        # В реальной реализации здесь была бы проверка по базе данных
        # известных вредоносных IP адресов
        suspicious_ranges = [
            "192.168.1.100",  # Пример
            "10.0.0.50",      # Пример
        ]
        return ip_address in suspicious_ranges
    
    def _has_multiple_connections(self, ip_address: str) -> bool:
        """Проверка множественных соединений с одного IP"""
        if not ip_address:
            return False
        
        connections = psutil.net_connections()
        count = sum(1 for conn in connections 
                   if conn.raddr and conn.raddr.ip == ip_address and conn.status == 'ESTABLISHED')
        
        return count > 10  # Более 10 соединений считается подозрительным
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Вычисление хеша файла"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Ошибка вычисления хеша файла {file_path}: {e}")
            return ""
    
    def _get_stored_hash(self, file_path: str) -> Optional[str]:
        """Получение сохраненного хеша файла"""
        hash_file = Path("security/file_hashes.json")
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    hashes = json.load(f)
                return hashes.get(file_path)
            except Exception as e:
                self.logger.error(f"Ошибка чтения хешей файлов: {e}")
        return None
    
    def _store_file_hash(self, file_path: str, file_hash: str):
        """Сохранение хеша файла"""
        try:
            hash_file = Path("security/file_hashes.json")
            hash_file.parent.mkdir(exist_ok=True)
            
            hashes = {}
            if hash_file.exists():
                with open(hash_file, 'r') as f:
                    hashes = json.load(f)
            
            hashes[file_path] = file_hash
            
            with open(hash_file, 'w') as f:
                json.dump(hashes, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения хеша файла: {e}")
    
    async def get_security_report(self, user_id: int) -> Dict[str, Any]:
        """Получение отчета по безопасности"""
        if not await self.role_manager.check_permission(user_id, "security", "view"):
            return {"error": "Нет доступа к отчетам безопасности"}
        
        try:
            # Статистика за последние 24 часа
            now = datetime.now()
            day_ago = now - timedelta(days=1)
            
            recent_events = [
                event for event in self.security_events
                if datetime.fromisoformat(event["timestamp"]) > day_ago
            ]
            
            # Группировка по типам событий
            event_types = {}
            for event in recent_events:
                event_type = event["type"]
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            # Статистика по уровням угроз
            threat_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            for event in recent_events:
                severity = event.get("severity", "medium")
                if severity in threat_levels:
                    threat_levels[severity] += 1
            
            report = {
                "timestamp": now.isoformat(),
                "period": "24 часа",
                "total_events": len(recent_events),
                "event_types": event_types,
                "threat_levels": threat_levels,
                "blocked_ips": len(self.blocked_ips),
                "suspicious_processes": len(self.threat_database["suspicious_processes"]),
                "file_violations": len(self.threat_database["file_integrity_violations"]),
                "recent_critical_events": [
                    event for event in recent_events[-10:]  # Последние 10 событий
                    if event.get("severity") in ["high", "critical"]
                ]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета безопасности: {e}")
            return {"error": f"Ошибка генерации отчета: {str(e)}"}
    
    async def _network_monitoring(self):
        """Мониторинг сети"""
        while self.enabled:
            try:
                # Мониторинг сетевой активности
                await asyncio.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга сети: {e}")
                await asyncio.sleep(60)
    
    async def _file_integrity_monitoring(self):
        """Мониторинг целостности файлов"""
        while self.enabled:
            try:
                await self._check_file_integrity()
                await asyncio.sleep(300)  # Проверка каждые 5 минут
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга целостности файлов: {e}")
                await asyncio.sleep(300) 