# ⚙️ Примеры конфигурации

## Базовая конфигурация

```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "bot_name": "Селла",
  "admin_ids": [123456789],
  "users": {
    "123456789": {
      "name": "Админ",
      "role": "admin",
      "permissions": {
        "system": ["view", "monitor", "settings"],
        "processes": ["view", "manage", "restart"],
        "server": ["view", "manage", "backup"],
        "storage": ["view", "upload", "download", "delete", "manage"],
        "notifications": ["view", "manage"],
        "analytics": ["view"],
        "security": ["view"],
        "admin": ["users", "roles", "logs", "config"]
      }
    },
    "987654321": {
      "name": "Оператор",
      "role": "operator",
      "permissions": {
        "system": ["view", "monitor"],
        "processes": ["view", "manage"],
        "server": ["view", "manage"],
        "storage": ["view", "upload", "download"],
        "notifications": ["view"],
        "analytics": ["view"]
      }
    }
  },
  "system": {
    "monitoring": {
      "check_interval": 60,
      "cpu_threshold": 80,
      "memory_threshold": 85,
      "disk_threshold": 90,
      "temperature_threshold": 45
    },
    "notifications": {
      "enabled": true,
      "cooldown": 300,
      "alert_levels": ["warning", "critical"]
    }
  },
  "bots": {
    "example_bot": {
      "name": "Example Bot",
      "path": "/path/to/your/bot/main.py",
      "enabled": true,
      "auto_restart": true
    }
  },
  "storage": {
    "path": "storage/",
    "max_files_per_user": 1000,
    "max_file_size": 52428800,
    "auto_cleanup": true,
    "allowed_extensions": [
      "pdf", "doc", "docx", "txt", "rtf",
      "jpg", "jpeg", "png", "gif", "bmp", "webp",
      "mp4", "avi", "mkv", "mov", "wmv",
      "mp3", "wav", "flac", "aac", "ogg",
      "zip", "rar", "7z", "tar", "gz"
    ]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## Расширенная конфигурация с новыми функциями

```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "bot_name": "Селла",
  "admin_ids": [123456789],
  "users": {
    "123456789": {
      "name": "Админ",
      "role": "admin",
      "permissions": {
        "system": ["view", "monitor", "settings"],
        "processes": ["view", "manage", "restart"],
        "server": ["view", "manage", "backup"],
        "storage": ["view", "upload", "download", "delete", "manage"],
        "notifications": ["view", "manage"],
        "analytics": ["view"],
        "security": ["view"],
        "admin": ["users", "roles", "logs", "config"]
      }
    }
  },
  "system": {
    "monitoring": {
      "check_interval": 60,
      "cpu_threshold": 80,
      "memory_threshold": 85,
      "disk_threshold": 90,
      "temperature_threshold": 45
    },
    "notifications": {
      "enabled": true,
      "cooldown": 300,
      "alert_levels": ["warning", "critical"]
    }
  },
  "bots": {
    "example_bot": {
      "name": "Example Bot",
      "path": "/path/to/your/bot/main.py",
      "enabled": true,
      "auto_restart": true
    }
  },
  "storage": {
    "path": "storage/",
    "max_files_per_user": 1000,
    "max_file_size": 52428800,
    "auto_cleanup": true,
    "allowed_extensions": [
      "pdf", "doc", "docx", "txt", "rtf",
      "jpg", "jpeg", "png", "gif", "bmp", "webp",
      "mp4", "avi", "mkv", "mov", "wmv",
      "mp3", "wav", "flac", "aac", "ogg",
      "zip", "rar", "7z", "tar", "gz"
    ]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "web_interface": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8080,
    "secret_key": "your-secret-key-change-this-in-production"
  },
  "ai_assistant": {
    "enabled": true,
    "auto_optimization": true,
    "smart_alerts": true,
    "learning_mode": true
  },
  "security": {
    "enabled": true,
    "threat_detection": true,
    "intrusion_prevention": true,
    "audit_logging": true,
    "monitoring_interval": 30,
    "max_failed_attempts": 5,
    "block_duration": 3600
  },
  "analytics": {
    "enabled": true,
    "data_retention_days": 30,
    "auto_reports": true,
    "report_interval": 86400
  }
}
```

## Конфигурация для Termux

```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "bot_name": "Селла Termux",
  "admin_ids": [123456789],
  "users": {
    "123456789": {
      "name": "Админ",
      "role": "admin",
      "permissions": {
        "system": ["view", "monitor", "settings"],
        "processes": ["view", "manage", "restart"],
        "storage": ["view", "upload", "download", "delete", "manage"],
        "notifications": ["view", "manage"],
        "analytics": ["view"],
        "security": ["view"],
        "admin": ["users", "roles", "logs", "config"]
      }
    }
  },
  "system": {
    "monitoring": {
      "check_interval": 60,
      "cpu_threshold": 80,
      "memory_threshold": 85,
      "disk_threshold": 90,
      "temperature_threshold": 45
    },
    "notifications": {
      "enabled": true,
      "cooldown": 300,
      "alert_levels": ["warning", "critical"]
    }
  },
  "storage": {
    "path": "storage/",
    "max_files_per_user": 500,
    "max_file_size": 26214400,
    "auto_cleanup": true,
    "allowed_extensions": [
      "pdf", "doc", "docx", "txt", "rtf",
      "jpg", "jpeg", "png", "gif", "bmp", "webp",
      "mp4", "avi", "mkv", "mov", "wmv",
      "mp3", "wav", "flac", "aac", "ogg",
      "zip", "rar", "7z", "tar", "gz"
    ]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot_termux.log",
    "max_size": "5MB",
    "backup_count": 3
  },
  "ai_assistant": {
    "enabled": true,
    "auto_optimization": true,
    "smart_alerts": true,
    "learning_mode": false
  },
  "security": {
    "enabled": true,
    "threat_detection": true,
    "intrusion_prevention": false,
    "audit_logging": true,
    "monitoring_interval": 60,
    "max_failed_attempts": 3,
    "block_duration": 1800
  },
  "analytics": {
    "enabled": true,
    "data_retention_days": 7,
    "auto_reports": false,
    "report_interval": 86400
  }
}
```

## Минимальная конфигурация

```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "admin_ids": [123456789],
  "users": {
    "123456789": {
      "name": "Админ",
      "role": "admin",
      "permissions": {
        "system": ["view", "monitor", "settings"],
        "processes": ["view", "manage", "restart"],
        "storage": ["view", "upload", "download", "delete"],
        "notifications": ["view", "manage"],
        "admin": ["users", "roles", "logs", "config"]
      }
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sella_bot.log"
  }
}
```

## Настройка ролей

### Роль "admin"
```json
{
  "permissions": {
    "system": ["view", "monitor", "settings"],
    "processes": ["view", "manage", "restart"],
    "server": ["view", "manage", "backup"],
    "storage": ["view", "upload", "download", "delete", "manage"],
    "notifications": ["view", "manage"],
    "analytics": ["view"],
    "security": ["view"],
    "admin": ["users", "roles", "logs", "config"]
  }
}
```

### Роль "operator"
```json
{
  "permissions": {
    "system": ["view", "monitor"],
    "processes": ["view", "manage"],
    "server": ["view", "manage"],
    "storage": ["view", "upload", "download"],
    "notifications": ["view"],
    "analytics": ["view"]
  }
}
```

### Роль "monitor"
```json
{
  "permissions": {
    "system": ["view", "monitor"],
    "processes": ["view"],
    "server": ["view"],
    "storage": ["view"],
    "notifications": ["view"],
    "analytics": ["view"]
  }
}
```

### Роль "user"
```json
{
  "permissions": {
    "system": ["view"],
    "storage": ["view", "upload", "download"]
  }
}
```

### Роль "guest"
```json
{
  "permissions": {
    "system": ["view"]
  }
}
```

## Важные замечания

1. **Безопасность**: Измените `secret_key` в продакшене
2. **Токен бота**: Получите у @BotFather в Telegram
3. **ID пользователя**: Узнайте у @userinfobot
4. **Пути**: Используйте абсолютные пути для ботов
5. **Права**: Настройте права доступа согласно вашим требованиям 