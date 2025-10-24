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

1. **设置环境变量**：

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

1. **启动应用**：

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

1. **访问应用**：
打开浏览器访问 <http://localhost:8000>

## 📁 项目结构

```text
Article-ReAngle/
├── backend/               # 后端服务
│   ├── main.py            # FastAPI 主应用入口，处理所有 HTTP 请求
│   ├── llm.py             # AI 文本重写服务，调用 OpenAI API
│   ├── extractors.py      # 内容提取器，处理 URL/文件/PDF 文本提取
│   └── utils.py           # 工具函数，文本相似度计算和格式化
├── frontend/              # 前端界面
│   ├── index.html         # 主页面，左右分栏布局
│   ├── app.js             # 前端逻辑，处理用户交互和 API 调用
│   └── styles.css         # 样式文件，现代化渐变背景和响应式设计
├── requirements.txt       # 项目依赖
├── render.yaml            # Render 部署配置
└── README.md              # 项目文档
```

## 🔄 程序运行流程

### 应用启动流程

```text
用户启动命令 → backend/main.py (FastAPI 应用) → 加载环境变量 → 配置中间件 → 启动 Uvicorn 服务器 → 监听端口
```

### 用户请求处理流程

```text
用户访问 → backend/main.py @app.get('/') → 返回 frontend/index.html → 加载前端资源 → 用户界面准备就绪
```

### 洗稿处理流程

```text
用户输入 → frontend/app.js → POST 请求到 /process → backend/main.py @app.post('/process') → 
根据输入类型调用 extractors.py → backend/llm.py rewrite_text() → 调用 OpenAI API → 
返回改写结果 → frontend/app.js displayResults() → 展示结果给用户
```

### 文件间依赖关系

```text
backend/main.py (主入口)
├── 导入 backend/extractors.py (内容提取)
├── 导入 backend/llm.py (AI 重写)
└── 服务 frontend/ 静态文件 (用户界面)
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
