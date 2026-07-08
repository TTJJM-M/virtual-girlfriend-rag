# 虚拟女友 RAG 知识库问答系统

基于 LangChain + FastAPI + Vue3 构建的企业级 RAG（检索增强生成）知识库问答系统，专为"虚拟女友"场景设计。

## ✨ 特性

### 核心功能
- 🔐 **用户系统** - 注册/登录/JWT 认证/修改密码
- 👤 **管理员账号** - 默认 `admin/123456`
- 💬 **多会话管理** - 每个用户独立的多个会话，支持删除
- 📚 **知识库管理** - 上传/解析/删除文档（txt/md/pdf/docx）
- 🤖 **RAG 问答** - 基于知识库内容回答，显示引用来源
- 🌓 **主题切换** - 白天/夜晚模式

### 企业级优化
- 🔄 **模型池自动切换** - 免费额度用尽时自动切换备用模型
  - Embedding: `text-embedding-v3` → `text-embedding-v2`
  - LLM: `qwen-plus` → `qwen-turbo` → `qwen-max`
- ⚡ **流式输出** - SSE 实时流式响应，首 token < 500ms
- 💾 **查询缓存** - LRU 缓存相同查询结果
- 📊 **向量隔离** - 按用户隔离 FAISS 索引
- 🔒 **权限控制** - RBAC 角色管理

## 🏗️ 技术架构

```
┌─────────────────┐
│   Vue 3 +       │
│   Element Plus  │  ← 前端（暗黑模式支持）
└────────┬────────┘
         │ REST API + SSE
┌────────▼────────┐
│   FastAPI +     │
│   LangChain     │  ← 后端（异步高性能）
├─────────────────┤
│ DashScope API   │  ← 阿里云百炼
│ - Embedding     │     text-embedding-v3
│ - Qwen LLM      │     qwen-plus/turbo/max
├─────────────────┤
│ FAISS           │  ← 向量检索（按用户隔离）
├─────────────────┤
│ MySQL           │  ← 用户/会话/知识库存储
└─────────────────┘
```

## 📦 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

系统会自动创建数据库，使用以下默认配置：
- **MySQL 账号**: `root`
- **MySQL 密码**: `Ttxhxx`
- **数据库名**: `virtual_girlfriend`

如需修改，编辑 `backend/app/config.py` 或创建 `.env` 文件。

### 3. 配置 API Key

默认 API Key 已配置在 `backend/app/config.py`：
```python
DASHSCOPE_API_KEY = "sk-ws-H.EMIXDIL.esfE..."
```

如需修改，编辑配置文件或设置环境变量。

### 4. 启动后端服务

```bash
cd backend
python run.py
```

服务启动后：
- 自动初始化数据库
- 自动创建管理员账号 `admin/123456`
- API 文档：http://localhost:8000/docs

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 📖 使用说明

### 1. 登录/注册
- 使用管理员账号 `admin/123456` 登录
- 或注册新用户

### 2. 上传知识库
1. 点击侧边栏"知识库"
2. 上传女友相关资料（聊天记录、人设文档等）
3. 等待文档处理完成（解析 → 分块 → 向量化）

### 3. 开始问答
1. 点击"新对话"创建会话
2. 输入问题，系统会基于知识库内容回答
3. 回答下方显示引用来源和相似度

### 4. 管理会话
- 侧边栏显示所有会话
- 点击切换会话
- 删除不需要的会话

### 5. 切换主题
- 点击侧边栏 🌙/☀️ 按钮切换白天/夜晚模式

## 📁 项目结构

```
virtual-girlfriend-rag/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心模块（安全/依赖）
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic Schema
│   │   ├── services/     # 业务服务
│   │   ├── utils/        # 工具函数
│   │   ├── config.py     # 配置
│   │   ├── database.py   # 数据库连接
│   │   └── main.py       # FastAPI 入口
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── views/        # 页面组件
│   │   ├── router/       # 路由配置
│   │   └── styles/       # 样式
│   ├── package.json
│   └── vite.config.js
└── data/
    ├── uploads/          # 上传的文档
    └── vector_store/     # FAISS 向量索引
```

## 🔧 配置说明

### 数据库配置
```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "Ttxhxx"
DB_NAME = "virtual_girlfriend"
```

### DashScope 配置
```python
DASHSCOPE_API_KEY = "your-api-key"
DASHSCOPE_EMBEDDING_MODEL = "text-embedding-v3"
DASHSCOPE_LLM_MODEL = "qwen-plus"
```

### 管理员配置
```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"
```

## 🚨 故障排除

### 数据库连接失败
- 确认 MySQL 服务已启动
- 检查用户名密码是否正确
- 确保数据库有创建权限

### API 调用失败
- 检查 API Key 是否有效
- 确认网络连接正常
- 查看后端日志错误信息

### 模型额度用尽
系统会自动切换到备用模型，在设置页面可查看模型状态。

### 文档处理失败
- 检查文件格式是否支持（txt/md/pdf/docx）
- 确认文件内容可解析
- 查看错误信息

## 📝 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| POST | /api/auth/refresh | 刷新 token |
| PUT | /api/auth/password | 修改密码 |
| GET | /api/auth/me | 获取用户信息 |
| GET | /api/sessions | 获取会话列表 |
| POST | /api/sessions | 创建会话 |
| DELETE | /api/sessions/{id} | 删除会话 |
| GET | /api/sessions/{id}/messages | 获取消息历史 |
| POST | /api/chat/{session_id} | 发送消息（SSE） |
| GET | /api/knowledge | 知识库列表 |
| POST | /api/knowledge/upload | 上传文档 |
| DELETE | /api/knowledge/{id} | 删除文档 |

## 📄 License

MIT License
