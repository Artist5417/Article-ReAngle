# Article ReAngle - 智能洗稿程序

一个基于大语言模型的智能文本重写应用，支持本地和云端部署。程序保留文章核心信息，根据用户指定的风格或立场重新组织和表达文章。采用了前后端分离的现代化架构，前端使用 React + Vite构建，后端基于 FastAPI。

## 快速体验

<https://article-reangle.onrender.com/>

## ✨ 核心功能

### 1. 多源输入

- **文本粘贴**：直接输入或粘贴文本
- **URL 抓取**：自动提取网页正文
- **文件上传**：支持 PDF, Word, TXT 格式
- **YouTube 视频**：提取视频字幕内容

### 2. 智能重写

- **多模型支持**：集成 OpenAI GPT-5, Google Gemini 2.5 Flash, Qwen Flash
- **风格定制**：支持幽默、学术、新闻等多种预设风格，也可自定义提示词
- **结构化输出**：同时生成重写后的文章和精简摘要

### 3. 多维展示与交互

- **摘要朗读 (TTS)**：支持对生成摘要进行语音朗读
- **原文对比**：提供直观的 Diff 视图，高亮显示改动细节
- **文件下载**：支持将重写结果下载为 TXT 文件
- **响应式设计**：适配桌面和移动端，提供现代化的 UI 体验

## 🛠️ 技术栈

### 前端 (Frontend)

- **核心框架**: React 18, TypeScript, Vite
- **UI 组件库**: shadcn/ui, Radix UI
- **样式**: Tailwind CSS
- **图标**: Lucide React
- **路由**: React Router v6

### 后端 (Backend)

- **核心框架**: FastAPI
- **语言模型**: OpenAI API, Google Gemini API, DashScope (阿里云)
- **工具库**: Pydantic, httpx, BeautifulSoup4, Lxml, PyPDF, Python-docx

## 🚀 本地部署

### 前置要求

- Python 3.9+
- Node.js 18+
- API Keys (OpenAI, Gemini, 或 DashScope)

### 1. 后端配置与启动

```bash
# 进入项目根目录
cd Article-ReAngle

# 安装依赖
pip install -r requirements.txt

# 设置环境变量 (Windows PowerShell 示例)
$env:OPENAI_API_KEY="your-key"
$env:GEMINI_API_KEY="your-key"
$env:DASHSCOPE_API_KEY="your-key"
# 或者在 .env 文件中配置

# 启动后端服务
python -m app.main
# 服务运行在 http://localhost:8000
```

### 2. 前端配置与启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 前端运行在 http://localhost:5173
```

## 📁 项目结构

```text
Article-ReAngle/
├── app/                      # 后端 (FastAPI)
│   ├── main.py               # 入口文件
│   ├── routers/              # API 路由
│   ├── services/             # 业务逻辑 (LLM, 提取器)
│   └── schemas/              # Pydantic 模型
├── frontend/                 # 前端 (React + Vite)
│   ├── src/
│   │   ├── components/       # UI 组件 (shadcn/ui)
│   │   ├── pages/            # 页面 (Landing, MainApp)
│   │   ├── lib/              # 工具函数
│   │   └── App.tsx           # 根组件
│   ├── tailwind.config.js    # Tailwind 配置
│   └── vite.config.ts        # Vite 配置
├── tests/                    # 单元测试
└── requirements.txt          # Python 依赖
```
