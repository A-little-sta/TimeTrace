# 数据库配置指南

## 1. 数据库表结构

根据项目需求，我们需要创建以下三个主要表：

### 1.1 用户表 (users)
- 存储用户账号信息
- 包含用户名、邮箱、密码哈希等字段

### 1.2 照片表 (photos)
- 存储用户上传的原始照片信息
- 包含文件名、文件路径、所属用户ID等字段

### 1.3 任务表 (tasks)
- 存储照片修复任务信息
- 包含任务类型、步骤、状态、结果路径等字段

## 2. SQL语句

### 2.1 MySQL兼容版 (推荐)
完整的MySQL兼容SQL建表语句已生成在 `database_schema.sql` 文件中：

```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建照片表
CREATE TABLE IF NOT EXISTS photos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_type VARCHAR(50) NOT NULL,
    steps JSON,
    current_step INT DEFAULT 0,
    photo_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    result_path VARCHAR(255),
    step_results JSON,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_photos_user_id ON photos(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_photo_id ON tasks(photo_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

### 2.2 SQLite版 (仅开发环境)

```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建照片表
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type VARCHAR(50) NOT NULL,
    steps JSON,
    current_step INTEGER DEFAULT 0,
    photo_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    result_path VARCHAR(255),
    step_results JSON,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_photos_user_id ON photos(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_photo_id ON tasks(photo_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

### 2.3 语法差异说明

| 特性 | MySQL | SQLite |
|------|-------|--------|
| 整数类型 | `INT` | `INTEGER` |
| 自增关键字 | `AUTO_INCREMENT` | `AUTOINCREMENT` |
| JSON类型支持 | MySQL 5.7+ | SQLite 3.9+ |
| 外键约束 | 需要InnoDB引擎 | 需要显式启用 |
| CREATE INDEX IF NOT EXISTS | MySQL 8.0+ | 支持 |

### 2.4 MySQL版本兼容性注意事项

1. **MySQL 8.0+**：
   - 支持所有语法，包括`CREATE INDEX IF NOT EXISTS`

2. **MySQL 5.7及以下**：
   - 不支持`CREATE INDEX IF NOT EXISTS`语法
   - 需要使用简化的`CREATE INDEX`语法
   - 已在`database_schema.sql`中提供兼容版本

3. **JSON类型**：
   - MySQL 5.7+支持JSON类型
   - 如果使用MySQL 5.6及以下，需要将JSON字段改为TEXT类型

## 3. 数据库配置

### 3.1 配置文件位置
数据库配置位于 `app/core/config.py` 文件中：

```python
class Settings(BaseSettings):
    # 项目基本配置
    PROJECT_NAME: str = "岁月笺影"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./timetrace.db"
    
    # Redis配置
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # 静态文件配置
    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/uploads"
    RESULT_DIR: str = "static/results"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif"}
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 3.2 配置说明

#### 3.2.1 SQLite配置
当前项目默认使用SQLite数据库，配置格式为：
```
DATABASE_URL: str = "sqlite:///./timetrace.db"
```

#### 3.2.2 MySQL配置（可选）
如果需要切换到MySQL数据库，可以修改为：
```
DATABASE_URL: str = "mysql+pymysql://username:password@localhost:3306/dbname"
```

#### 3.2.3 PostgreSQL配置（可选）
如果需要切换到PostgreSQL数据库，可以修改为：
```
DATABASE_URL: str = "postgresql://username:password@localhost:5432/dbname"
```

### 3.3 环境变量配置
可以通过 `.env` 文件覆盖默认配置：

```
# 数据库配置
DATABASE_URL=sqlite:///./timetrace.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## 4. Redis配置

### 4.1 Redis是否必需？
- **用于Celery异步任务**：是的，Redis是Celery的默认消息代理和结果后端，用于处理照片修复的异步任务
- **用于缓存**：可选，如果需要缓存功能，可以使用Redis进行缓存

### 4.2 Redis配置说明

#### 4.2.1 基本Redis配置
```python
# Redis配置
REDIS_URL: Optional[str] = "redis://localhost:6379/0"
```

#### 4.2.2 Celery Redis配置
```python
# Celery配置
CELERY_BROKER_URL: str = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
```

### 4.3 Redis安装与启动

#### Windows
1. 下载Redis Windows版本：https://github.com/microsoftarchive/redis/releases
2. 解压并运行 `redis-server.exe`

#### Linux
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

## 5. 数据库初始化

项目使用SQLAlchemy ORM，数据库表会在应用启动时自动创建：

```python
# app/db/__init__.py
from .base import Base, engine, SessionLocal
from .models import Photo, User, Task

# 创建所有数据库表
Base.metadata.create_all(bind=engine)
```

## 6. 总结

1. **需要的数据库表**：users, photos, tasks
2. **SQL语句**：已生成在 `database_schema.sql` 文件中
3. **Redis需求**：
   - 用于Celery异步任务：必需
   - 用于缓存：可选
4. **数据库配置**：
   - 默认使用SQLite
   - 可通过 `app/core/config.py` 或 `.env` 文件修改配置
   - 支持切换到MySQL或PostgreSQL
5. **Redis配置**：
   - 默认使用本地Redis服务器
   - 可通过配置文件修改Redis连接信息

