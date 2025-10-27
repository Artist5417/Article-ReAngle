# Article ReAngle - 智能洗稿程序

一个基于大语言模型的智能文本重写应用，支持本地和云端部署。程序保留文章核心信息，根据用户指定的风格或立场重新组织和表达文章。用户既可以上传文档、粘贴文字，也可以输入网页链接，程序会自动提取文章主体内容，并结合用户的提示词生成全新的文章。

## 功能特性

### 输入与预处理

用户可以通过三种方式提供文章：

1. **直接粘贴文本** - 在文本框中直接粘贴要改写的文章内容
2. **上传文件** - 支持 TXT、Word、PDF 格式的文件上传  
3. **输入文章 URL** - 由系统自动抓取网页正文内容

程序会自动进行预处理：

- **Word 文档**：提取正文段落，保留格式结构
- **PDF 文件**：优先解析文字层，若遇到扫描件则调用 OCR 技术将图片转为文字
- **URL 链接**：自动抓取网页主体并过滤掉广告、导航栏等无关部分

经过清洗，所有输入最终统一为一份 **结构化、干净的纯文本**，以便后续模型处理。

### 模型处理逻辑

文章进入模型层后，会按照"两步走"的策略进行处理：

1. **要点提炼**：调用 LLM 对文章进行总结，提取核心信息与逻辑框架，确保保留主要内容并保持客观中立
2. **视角改写**：将提炼出的要点与用户提示词结合，根据指定的风格或立场生成新文章

用户提示词既可以控制风格（如"学术化""新闻报道""幽默化"），也可以指定立场（如"支持某政策"或"从消费者角度出发"）。

### 输出与展示

生成结果会在网页端展示，用户可以直接在线阅读。同时提供多种下载格式：

- **Word 文档** - 便于编辑和分享
- **PDF 文件** - 适合正式文档  
- **Markdown / HTML** - 方便在博客或网站发布

此外，系统支持 **原文与新文的对比视图**，并能计算两者的相似度，帮助用户直观判断改写效果和差异程度。

## 🚀 快速开始

### 部署地址

- **Render**: <https://article-reangle.onrender.com>
- **本地运行**: <http://localhost:8000>

### 本地运行步骤

1. **安装依赖**：

```bash
pip install -r requirements.txt
```

2. **设置环境变量**：

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

3. **启动应用**：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或者直接运行：

```bash
python -m app.main
```

4. **访问应用**：
打开浏览器访问 <http://localhost:8000>

## 📁 项目结构

Following FastAPI best practices with modular architecture:

```text
Article-ReAngle/
├── app/                      # Main application package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration and constants
│   ├── dependencies.py       # Shared dependencies and utilities
│   ├── routers/              # API route modules
│   │   ├── __init__.py
│   │   ├── articles.py       # Article rewriting endpoints
│   │   ├── stories.py        # Story generation endpoints
│   │   └── results.py        # Results retrieval endpoints
│   ├── services/             # Business logic layer
│   │   ├── __init__.py
│   │   ├── extractors.py     # Content extraction (URL, PDF, DOCX)
│   │   ├── llm.py            # LLM services (OpenAI integration)
│   │   └── utils.py          # Utility functions
│   ├── models/               # LLM client models (under development)
│   │   ├── gemini_client.py
│   │   ├── openai_client.py
│   │   └── prompts/
│   └── static/               # Frontend files
│       ├── index.html        # Main page
│       ├── app.js            # Frontend logic
│       └── styles.css        # Styles
├── results/                  # Generated content storage
├── requirements.txt          # Project dependencies
├── render.yaml               # Render deployment config
└── README.md                 # Project documentation
```

## 🔄 程序运行流程

### 应用启动流程

```text
用户启动命令 → app/main.py (FastAPI 应用) → 加载环境变量 → 配置中间件 → 
注册路由 (articles, stories, results) → 启动 Uvicorn 服务器 → 监听端口
```

### 用户请求处理流程

```text
用户访问 → app/main.py @app.get('/') → 返回 app/static/index.html → 
加载前端资源 → 用户界面准备就绪
```

### 文章改写流程

```text
用户输入 → app/static/app.js → POST /process → app/routers/articles.py → 
调用 app/services/extractors.py 提取内容 → 
调用 app/services/llm.py rewrite_text() → OpenAI API → 
返回改写结果 → 前端展示
```

### 故事生成流程

```text
用户请求 → POST /generate → app/routers/stories.py → 
解析参数 (app/dependencies.py) → 
生成故事 (app/services/llm.py) → 
存储结果 → 返回 JSON 响应
```

### 模块架构

```text
app/main.py (FastAPI 应用)
├── 路由层 (routers/)
│   ├── articles.py → 文章改写 API
│   ├── stories.py  → 故事生成 API
│   └── results.py  → 结果查询 API
├── 服务层 (services/)
│   ├── extractors.py → 内容提取服务
│   ├── llm.py        → LLM 调用服务
│   └── utils.py      → 工具函数
├── 配置层
│   ├── config.py       → 应用配置
│   └── dependencies.py → 共享依赖
└── 静态资源 (static/) → 前端界面
```

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn, OpenAI API, httpx, BeautifulSoup4, python-docx, pypdf
- **前端**: 原生 HTML/CSS/JavaScript, 响应式设计
- **部署**: Render (主要), Vercel (备用)

## ❓ 常见问题

### 如何处理大文件？

程序会自动限制输入长度，建议单次处理不超过3000字符。

### 支持哪些文件格式？

目前支持 TXT、Word(.docx)、PDF 格式。

### 如何提高改写质量？

可以尝试调整改写强度，或提供更详细的风格和立场要求。

---

**Article ReAngle** - 让文章改写变得简单高效！
