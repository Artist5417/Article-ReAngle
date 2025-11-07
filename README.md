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

### 多模型支持

应用支持多个主流大语言模型，用户可以根据需求自由选择：

- **OpenAI GPT-5** - 使用最新的 OpenAI Responses API，提供高质量的改写结果
- **Google Gemini 2.5 Flash** - 快速响应，成本更低，适合大批量处理

通过前端下拉菜单即可切换模型，系统会自动路由到相应的 API 客户端。

### 模型处理逻辑

文章进入模型层后，会根据用户选择的改写要求进行处理：

1. **内容理解**：LLM 深入理解原文的核心信息、逻辑结构和关键论点
2. **风格改写**：根据用户提供的提示词（风格、立场、语气等），重新组织和表达内容

用户提示词既可以控制风格（如"学术化""新闻报道""幽默化"），也可以指定立场（如"支持某政策"或"从消费者角度出发"）。系统还提供了预设风格模板，包括口语风、学术风、新闻风、公众号风和诗意风等。

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

**安装依赖**：

```bash
pip install -r requirements.txt
```

**设置环境变量**：

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-openai-api-key-here"
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-openai-api-key-here
set GEMINI_API_KEY=your-gemini-api-key-here

# Linux/Mac
export OPENAI_API_KEY="your-openai-api-key-here"
export GEMINI_API_KEY="your-gemini-api-key-here"
```

**注意**：根据您选择的语言模型，至少需要设置一个 API Key。如果要使用 OpenAI 的 GPT 模型，需要设置 `OPENAI_API_KEY`；如果要使用 Google Gemini 模型，需要设置 `GEMINI_API_KEY`。

**启动应用**：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

或者直接运行：

```bash
python -m app.main
```

**访问应用**：
打开浏览器访问 <http://localhost:8000>

## 📁 项目结构

遵循 FastAPI 最佳实践的模块化架构：

```text
Article-ReAngle/
├── app/                      # 应用主包
│   ├── __init__.py           # 包初始化文件
│   ├── main.py               # FastAPI 应用入口
│   ├── configs/              # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py       # 应用配置和常量
│   ├── routers/              # API 路由模块
│   │   ├── __init__.py       # 路由注册
│   │   ├── rewrite.py        # 文章改写端点
│   │   └── miniprogram.py    # 故事生成和结果查询端点
│   ├── schemas/              # 请求/响应数据模型
│   │   ├── rewrite_schema.py      # 改写请求/响应模型
│   │   └── miniprogram_schema.py  # 小程序数据模型
│   ├── services/             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── extractors.py     # 内容提取（URL、PDF、DOCX）
│   │   ├── utils.py          # 工具函数
│   │   └── llms/             # 语言模型服务
│   │       ├── __init__.py
│   │       ├── llm.py              # 旧版 LLM 服务（OpenAI）
│   │       ├── rewriting_client.py # 统一 LLM 接口
│   │       ├── openai_client.py    # OpenAI Responses API 客户端
│   │       ├── gemini_client.py    # Google Gemini API 客户端
│   │       └── prompts/            # 系统提示词模板
│   │           ├── openai_system_prompt.yaml
│   │           └── gemini_system_prompt.yaml
│   └── static/               # 前端文件
│       ├── index.html        # 主页面
│       ├── app.js            # 前端逻辑
│       └── styles.css        # 样式文件
├── docs/                     # 文档
│   └── 小程序对接.md         # 小程序 API 对接指南
├── results/                  # 生成内容存储目录
├── requirements.txt          # 项目依赖
├── render.yaml               # Render 部署配置
└── README.md                 # 项目文档
```

## 🔄 程序运行流程

### 应用启动流程

```text
用户启动命令 → app/main.py (FastAPI 应用) → 加载环境变量 → 配置中间件 → 
注册路由 (/api/v1/rewrite, /api/v1/miniprogram) → 启动 Uvicorn 服务器 → 监听端口
```

### 用户请求处理流程

```text
用户访问 → app/main.py @app.get('/') → 返回 app/static/index.html → 
加载前端资源 → 用户界面准备就绪
```

### 文章改写流程（多模型支持）

```text
用户输入 → app/static/app.js → POST /api/v1/rewrite → app/routers/rewrite.py → 
调用 app/services/extractors.py 提取内容 → 
调用 app/services/llms/rewriting_client.py → 
根据选择的模型类型 (OpenAI/Gemini) → 
  → app/services/llms/openai_client.py (GPT-5 Responses API) 或
  → app/services/llms/gemini_client.py (Gemini 2.5 Flash) → 
返回改写结果 → 前端展示
```

### 故事生成流程

```text
用户请求 → POST /api/v1/miniprogram/generate → app/routers/miniprogram.py → 
解析参数和关键词 → 
生成故事 (app/services/llms/llm.py call_openai) → 
存储结果到 results/ 目录 → 返回 JSON 响应
```

### 模块架构

```text
app/main.py (FastAPI 应用)
├── 配置层 (configs/)
│   └── settings.py         → 应用配置和常量
├── 路由层 (routers/)
│   ├── __init__.py         → API 路由注册 (/api/v1)
│   ├── rewrite.py          → 文章改写 API
│   └── miniprogram.py      → 故事生成和结果查询 API
├── 数据层 (schemas/)
│   ├── rewrite_schema.py   → 改写请求/响应模型
│   └── miniprogram_schema.py → 小程序数据模型
├── 服务层 (services/)
│   ├── extractors.py       → 内容提取服务
│   ├── utils.py            → 工具函数
│   └── llms/               → 大模型服务
│       ├── llm.py              → 旧版 LLM 服务
│       ├── rewriting_client.py → 统一 LLM 接口
│       ├── openai_client.py    → OpenAI 客户端
│       ├── gemini_client.py    → Gemini 客户端
│       └── prompts/            → 系统提示词模板 (YAML)
└── 静态资源 (static/)     → 前端界面
```

## 🛠️ 技术栈

- **后端框架**: FastAPI, Uvicorn
- **大语言模型**:
  - OpenAI GPT-5 (Responses API)
  - Google Gemini 2.5 Flash
- **内容提取**: httpx, BeautifulSoup4, readability-lxml, python-docx, pypdf, pytesseract
- **数据处理**: Pydantic, PyYAML, rapidfuzz
- **前端**: 原生 HTML/CSS/JavaScript, 响应式设计
- **部署**: Render (云端部署)

## ❓ 常见问题

### 如何处理大文件？

程序会自动限制输入长度，建议单次处理不超过3000字符。

### 支持哪些文件格式？

目前支持 TXT、Word(.docx)、PDF 格式。

### 如何提高改写质量？

可以尝试调整改写强度，或提供更详细的风格和立场要求。

---

**Article ReAngle** - 让文章改写变得简单高效！
