---
title: "Python全栈开发教程"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Python全栈开发教程


> 📌 **导航**：本文是 **Python全栈开发教程** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

## Python全栈开发完整教程：从基础到生产部署

## 一、Python基础语法回顾（800字）

### 1.1 变量和数据类型
```python
# 变量声明与类型注解
name: str = "全栈工程师"
age: int = 28
salary: float = 15000.50
is_experienced: bool = True
skills: list = ["Python", "JavaScript", "SQL"]
profile: dict = {
    "name": name,
    "age": age,
    "skills": skills
}

# 类型转换示例
number_str = "123"
number_int = int(number_str)
number_float = float(number_int)
```

### 1.2 流程控制
```python
# 条件语句
def check_experience(years: int) -> str:
    if years >= 5:
        return "资深工程师"
    elif years >= 2:
        return "中级工程师"
    else:
        return "初级工程师"

# 循环语句
skills = ["Python", "FastAPI", "React", "Docker"]

# for循环
for index, skill in enumerate(skills):
    print(f"{index + 1}. {skill}")

# 列表推导式
skill_upper = [skill.upper() for skill in skills if "r" in skill.lower()]

# while循环
count = 0
while count < len(skills):
    print(f"学习进度: {count+1}/{len(skills)}")
    count += 1
```

### 1.3 函数和面向对象编程
```python
# 函数定义与装饰器
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"调用函数: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logger
def calculate_salary(base: float, bonus: float = 0) -> float:
    """计算总薪资"""
    return base + bonus

# 类定义与继承
class Employee:
    def __init__(self, name: str, position: str):
        self.name = name
        self.position = position
    
    def introduce(self) -> str:
        return f"我是{self.name}，职位是{self.position}"

class FullStackDeveloper(Employee):
    def __init__(self, name: str, frontend_skills: list, backend_skills: list):
        super().__init__(name, "全栈工程师")
        self.frontend_skills = frontend_skills
        self.backend_skills = backend_skills
    
    def get_skills(self) -> dict:
        return {
            "前端": self.frontend_skills,
            "后端": self.backend_skills
        }
```

### 1.4 模块和包管理
```python
# 创建项目结构
# project/
# ├── main.py
# ├── utils/
# │   ├── __init__.py
# │   ├── database.py
# │   └── validators.py
# └── models/
#     ├── __init__.py
#     └── user.py

# utils/database.py
from typing import Any, Optional

class DatabaseConnector:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def connect(self) -> bool:
        """模拟数据库连接"""
        print(f"连接到数据库: {self.connection_string}")
        return True
    
    async def execute_query(self, query: str, params: Optional[dict] = None) -> Any:
        """模拟执行查询"""
        print(f"执行查询: {query}")
        return []

# main.py
from utils.database import DatabaseConnector
import asyncio

async def main():
    db = DatabaseConnector("postgresql://user:pass@localhost/db")
    await db.connect()
    result = await db.execute_query("SELECT * FROM users")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 二、FastAPI后端框架（1000字）

### 2.1 FastAPI基础
```python
# 安装FastAPI和Uvicorn
# pip install fastapi uvicorn[standard]

# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="全栈应用API",
    description="基于FastAPI的RESTful API",
    version="1.0.0"
)

# 数据模型
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        orm_mode = True

# 模拟数据库
fake_users_db = {}
current_id = 1

# OAuth2认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 这里应该验证token
    user = fake_users_db.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )
    return user

# API路由
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    global current_id
    
    # 检查用户名是否已存在
    for existing_user in fake_users_db.values():
        if existing_user["username"] == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 创建用户
    user_dict = user.dict()
    user_dict["id"] = current_id
    user_dict["is_active"] = True
    fake_users_db[str(current_id)] = user_dict
    current_id += 1
    
    return UserResponse(**user_dict)

@app.get("/users/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    users = list(fake_users_db.values())
    return users[skip : skip + limit]

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 这里应该验证用户名和密码
    for user in fake_users_db.values():
        if user["username"] == form_data.username:
            # 简化演示，实际应该生成JWT token
            return {"access_token": str(user["id"]), "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误"
    )

# 中间件示例
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动应用
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### 2.2 路由组织和依赖注入
```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "未找到"}}
)

# 依赖注入示例
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@router.get("/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# routers/tasks.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, user_id: int = Depends(get_current_user_id)):
    # 创建任务逻辑
    task_data = task.dict()
    task_data["user_id"] = user_id
    task_data["created_at"] = datetime.now()
    task_data["is_completed"] = False
    
    # 保存到数据库
    return await save_task_to_db(task_data)

# main.py中注册路由
from routers import users, tasks

app.include_router(users.router)
app.include_router(tasks.router)
```

## 三、SQLAlchemy ORM（1000字）

### 3.1 模型定义和关联
```python
# models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional

# 数据库连接
DATABASE_URL = "postgresql://user:password@localhost:5432/fullstack_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联任务
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# 任务模型
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1:低 2:中 3:高
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系定义
    owner = relationship("User", back_populates="tasks")
    
    # 关联标签
    tags = relationship("Tag", secondary="task_tags", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}')>"

# 标签模型
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # 关系定义
    tasks = relationship("Task", secondary="task_tags", back_populates="tags")

# 任务标签关联表
class TaskTag(Base):
    __tablename__ = "task_tags"
    
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

# 数据库会话管理
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 数据库初始化脚本
if __name__ == "__main__":
    init_db()
    print("数据库表已创建")
```

### 3.2 CRUD操作和查询
```python
# crud/user.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime

from models.database import User, Task
from schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """创建用户"""
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdate) -> Optional[User]:
    """更新用户"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # 更新字段
    for field, value in user.dict(exclude_unset=True).items():
        if field == "password":
            value = pwd_context.hash(value)
            field = "hashed_password"
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# 高级查询示例
def get_user_tasks(
    db: Session, 
    user_id: int, 
    completed: Optional[bool] = None,
    priority: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Task]:
    """获取用户的任务，支持过滤"""
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.is_completed == completed)
    
    if priority is not None:
        query = query.filter(Task.priority == priority)
    
    return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

def get_task_statistics(db: Session, user_id: int) -> dict:
    """获取任务统计"""
    total = db.query(Task).filter(Task.user_id == user_id).count()
    completed = db.query(Task).filter(
        and_(Task.user_id == user_id, Task.is_completed == True)
    ).count()
    
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0
    }

# 批量操作
def bulk_create_tasks(db: Session, user_id: int, tasks: List[dict]) -> List[Task]:
    """批量创建任务"""
    db_tasks = []
    for task_data in tasks:
        db_task = Task(
            user_id=user_id,
            **task_data
        )
        db.add(db_task)
        db_tasks.append(db_task)
    
    db.commit()
    for task in db_tasks:
        db.refresh(task)
    
    return db_tasks
```

## 四、PostgreSQL数据库（800字）

### 4.1 数据库设计和优化
```sql
-- 数据库初始化脚本 init.sql
-- 创建数据库
CREATE DATABASE fullstack_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- 创建用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建任务表
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 1 CHECK (priority IN (1, 2, 3)),
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT valid_due_date CHECK (due_date > created_at)
);

-- 创建标签表
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- 创建任务标签关联表
CREATE TABLE task_tags (
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_is_completed ON tasks(is_completed);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- 创建全文搜索索引
CREATE INDEX idx_tasks_title_search ON tasks USING gin(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- 创建函数和触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建视图
CREATE VIEW user_task_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.is_completed = TRUE THEN 1 END) as completed_tasks,
    ROUND(COUNT(CASE WHEN t.is_completed = TRUE THEN 1 END)::DECIMAL / COUNT(t.id) * 100, 2) as completion_rate
FROM users u
LEFT JOIN tasks t ON u.id = t.user_id
GROUP BY u.id, u.username;

-- 存储过程示例
CREATE OR REPLACE PROCEDURE complete_task(task_id INTEGER, user_id INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    task_exists BOOLEAN;
    is_owner BOOLEAN;
BEGIN
    -- 检查任务是否存在
    SELECT EXISTS(SELECT 1 FROM tasks WHERE id = task_id) INTO task_exists;
    
    IF NOT task_exists THEN
        RAISE EXCEPTION '任务不存在: %', task_id;
    END IF;
    
    -- 检查是否为任务所有者
    SELECT EXISTS(
        SELECT 1 FROM tasks 
        WHERE id = task_id AND user_id = complete_task.user_id
    ) INTO is_owner;
    
    IF NOT is_owner THEN
        RAISE EXCEPTION '无权操作此任务';
    END IF;
    
    -- 更新任务状态
    UPDATE tasks 
    SET is_completed = TRUE, 
        completed_at = NOW(),
        updated_at = NOW()
    WHERE id = task_id;
    
    COMMIT;
END;
$$;
```

### 4.2 数据库连接池和性能优化
```python
# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

# 配置日志
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class DatabaseConnectionPool:
    """数据库连接池管理器"""
    
    def __init__(self, database_url: str, pool_size: int = 5, max_overflow: int = 10):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # 自动重连
            pool_recycle=3600,   # 连接回收时间
            echo=True  # 输出SQL语句
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_db(self):
        """FastAPI依赖注入用的数据库会话生成器"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def execute_raw_sql(self, sql: str, params: dict = None):
        """执行原始SQL"""
        with self.engine.connect() as connection:
            if params:
                result = connection.execute(sql, params)
            else:
                result = connection.execute(sql)
            return result
    
    def check_connection(self):
        """检查数据库连接"""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            return False

# 使用示例
db_pool = DatabaseConnectionPool(
    database_url="postgresql://user:password@localhost/fullstack_db",
    pool_size=20,
    max_overflow=30
)

# 在FastAPI中使用
from fastapi import Depends

async def get_db():
    with db_pool.get_session() as session:
        yield session

# 性能优化配置
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # 生产环境关闭SQL日志
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

# 查询优化示例
from sqlalchemy import text

def get_user_with_tasks(user_id: int, db: Session):
    """优化后的查询：使用JOIN和预加载"""
    from sqlalchemy.orm import joinedload
    
    user = db.query(User).options(
        joinedload(User.tasks).joinedload(Task.tags)
    ).filter(User.id == user_id).first()
    
    return user

def search_tasks(search_term: str, user_id: int, db: Session):
    """全文搜索优化"""
    query = """
    SELECT * FROM tasks 
    WHERE user_id = :user_id 
    AND (
        to_tsvector('english', title) @@ plainto_tsquery('english', :search_term) OR
        to_tsvector('english', description) @@ plainto_tsquery('english', :search_term)
    )
    ORDER BY ts_rank(
        to_tsvector('english', title || ' ' || COALESCE(description, '')),
        plainto_tsquery('english', :search_term)
    ) DESC
    """
    
    return db.execute(
        text(query), 
        {"user_id": user_id, "search_term": search_term}
    ).fetchall()
```

## 五、React前端（1000字）

### 5.1 React基础与项目结构
```javascript
// package.json
{
  "name": "fullstack-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.0",
    "antd": "^5.2.0",
    "@ant-design/icons": "^5.0.0",
    "moment": "^2.29.4",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^3.1.0",
    "vite": "^4.1.0",
    "eslint": "^8.34.0",
    "prettier": "^2.8.4"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,css,md,json}\""
  }
}

// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>
)
```

### 5.2 React组件和状态管理
```jsx
// src/App.jsx
import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import { AuthProvider, useAuth } from './contexts/AuthContext'

const { Content } = Layout

// 受保护的路由组件
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div>加载中...</div>
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

const App = () => {
  return (
    <Layout className="app-layout">
      <Navbar />
      <Content className="app-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <TaskList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tasks/:taskId"
            element={
              <ProtectedRoute>
                <TaskDetail />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App

// src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // 检查本地存储的token
    const token = localStorage.getItem('token')
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/api/users/me')
      setUser(response.data)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      const response = await api.post('/api/token', {
        username,
        password,
      })
      
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      await fetchCurrentUser()
      navigate('/')
      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await api.post('/api/users/', userData)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('注册失败:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败'
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
    navigate('/login')
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// src/pages/TaskList.jsx
import React, { useState, useEffect } from 'react'
import { Table, Tag, Space, Button, Input, Select, DatePicker } from 'antd'
import { PlusOutlined, SearchOutlined, FilterOutlined } from '@ant-design/icons'
import moment from 'moment'
import api from '../services/api'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker

const TaskList = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    priority: 'all',
    dateRange: null
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })

  const columns = [
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <a href={`/tasks/${record.id}`}>{text}</a>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_completed',
      key: 'status',
      render: (completed) => (
        <Tag color={completed ? 'green' : 'orange'}>
          {completed ? '已完成' : '进行中'}
        </Tag>
      ),
      filters: [
        { text: '进行中', value: false },
        { text: '已完成', value: true }
      ],
      onFilter: (value, record) => record.is_completed === value
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => {
        const colors = { 1: 'blue', 2: 'orange', 3: 'red' }
        const labels = { 1: '低', 2: '中', 3: '高' }
        return <Tag color={colors[priority]}>{labels[priority]}</Tag>
      }
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      key: 'due_date',
      render: (date) => date ? moment(date).format('YYYY-MM-DD HH:mm') : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button type="link" size="small">
            编辑
          </Button>
          <Button type="link" danger size="small">
            删除
          </Button>
        </Space>
      )
    }
  ]

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const params = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        ...filters
      }
      
      const response = await api.get('/api/tasks', { params })
      setTasks(response.data.items)
      setPagination(prev => ({
        ...prev,
        total: response.data.total
      }))
    } catch (error) {
      console.error('获取任务列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [pagination.current, pagination.pageSize])

  const handleTableChange = (pagination, filters, sorter) => {
    setPagination(pagination)
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
    setPagination(prev => ({
      ...prev,
      current: 1
    }))
  }

  const handleSearch = (value) => {
    handleFilterChange('search', value)
    fetchTasks()
  }

  return (
    <div className="task-list-page">
      <div className="page-header">
        <h2>任务管理</h2>
        <Button type="primary" icon={<PlusOutlined />}>
          新建任务
        </Button>
      </div>
      
      <div className="filters-bar">
        <Space size="middle" wrap>
          <Search
            placeholder="搜索任务"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            style={{ width: 300 }}
          />
          
          <Select
            defaultValue="all"
            style={{ width: 120 }}
            onChange={(value) => handleFilterChange('status', value)}
          >
            <Option value="all">全部状态</Option>
            <Option value="active">进行中</Option>
            <Option value="completed">已完成</Option>
          </Select>
          
          <Select
            defaultValue="all"
            style={{ width: 120 }}
            onChange={(value) => handleFilterChange('priority', value)}
          >
            <Option value="all">全部优先级</Option>
            <Option value="1">低</Option>
            <Option value="2">中</Option>
            <Option value="3">高</Option>
          </Select>
          
          <RangePicker
            onChange={(dates) => handleFilterChange('dateRange', dates)}
            showTime
          />
          
          <Button icon={<FilterOutlined />}>
            更多筛选
          </Button>
```

## 相关术语

[[Python高级特性]]、[[Python高级编程完全指南]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[React Native移动应用开发]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
