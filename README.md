# Article ReAngle - 智能洗稿程序

一个基于大语言模型的本地网页应用，用于在保留文章核心信息的前提下，根据用户指定的风格或立场重新组织和表达文章。

## 功能特点

### 🎯 核心功能
- **智能洗稿**：保留原文核心信息，改变表达方式和风格
- **多输入方式**：支持文本粘贴、文件上传、URL抓取
- **灵活控制**：可调节改写强度和指定风格立场
- **实时对比**：原文与新文对比，显示相似度

### 📝 输入方式
1. **直接粘贴文本** - 在网页上直接粘贴要改写的文章
2. **上传文件** - 支持 TXT、Word、PDF 格式
3. **输入URL** - 自动抓取网页正文内容

### 🎨 风格控制
- **预设风格**：新闻报道、学术论文、轻松幽默、正式商务、科普文章
- **自定义风格**：用户可输入任意风格要求
- **立场控制**：支持指定特定立场或角度
- **改写强度**：从轻度改写到完全重写

### 📊 输出功能
- **在线阅读**：网页端直接展示结果
- **对比视图**：原文与新文并排对比
- **相似度计算**：显示改写前后的相似度
- **多格式导出**：支持 TXT、Markdown 格式下载

## 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（Chrome、Firefox、Edge等）

### 安装运行

1. **克隆项目**
```bash
git clone <repository-url>
cd Article-ReAngle
```

2. **配置API Key（推荐）**
```bash
# Windows PowerShell（推荐）
$env:OPENAI_API_KEY="your_openai_api_key_here"

# Windows CMD
set OPENAI_API_KEY=your_openai_api_key_here

# Linux/macOS
export OPENAI_API_KEY="your_openai_api_key_here"
```

3. **一键启动**
```bash
# Windows用户
start.bat

# 或手动启动
cd backend
pip install -r requirements.txt
python main.py
```

4. **访问应用**
- 打开 `frontend/index.html` 在浏览器中
- 后端API运行在 `http://localhost:8000`

### LLM配置

程序支持多种LLM配置方式，**推荐使用环境变量**：

#### 方式1：环境变量配置（推荐）

**Windows PowerShell:**
```powershell
# 临时设置（当前会话有效）
$env:OPENAI_API_KEY="your_openai_api_key_here"

# 永久设置（需要重启终端）
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_openai_api_key_here", "User")
```

**Windows CMD:**
```cmd
# 临时设置
set OPENAI_API_KEY=your_openai_api_key_here

# 永久设置
setx OPENAI_API_KEY "your_openai_api_key_here"
```

**Linux/macOS:**
```bash
# 临时设置
export OPENAI_API_KEY="your_openai_api_key_here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="your_openai_api_key_here"' >> ~/.bashrc
```

#### 方式2：界面输入（备选）
如果未设置环境变量，程序会在界面中提示输入API Key。

#### 方式3：使用本地Ollama
```bash
# 安装Ollama
# 下载地址：https://ollama.ai/

# 设置环境变量（可选，默认localhost:11434）
set OLLAMA_BASE_URL=http://localhost:11434
```

## 使用说明

### 基本流程

1. **提交"稿"**
   - 选择输入方式（文本/文件/URL）
   - 输入或上传要改写的文章

2. **设置"洗"稿参数**
   - 选择或自定义风格要求
   - 设置立场要求（可选）
   - 调节改写强度（0.1-1.0）

3. **获取结果**
   - 查看改写后的文章
   - 对比原文与新文
   - 查看要点总结
   - 下载结果文件

### 高级功能

- **相似度分析**：自动计算原文与新文的相似度
- **要点提取**：智能总结原文核心要点
- **多格式导出**：支持多种文件格式下载

## 技术架构

### 后端技术栈
- **FastAPI** - 现代Python Web框架
- **Pydantic** - 数据验证和序列化
- **httpx** - 异步HTTP客户端
- **BeautifulSoup** - HTML解析
- **python-docx** - Word文档处理
- **PyPDF2** - PDF文档处理

### 前端技术栈
- **原生HTML/CSS/JavaScript** - 轻量级前端
- **响应式设计** - 支持多设备访问
- **现代UI** - 简洁美观的用户界面

### LLM集成
- **OpenAI API** - 云端大语言模型
- **Ollama** - 本地大语言模型
- **灵活配置** - 支持多种模型切换

## 项目结构

```
Article-ReAngle/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI主应用
│   ├── extractors.py       # 文本提取模块
│   ├── llm.py             # LLM处理模块
│   ├── utils.py           # 工具函数
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── styles.css         # 样式文件
│   └── app.js             # JavaScript逻辑
├── start.bat              # Windows启动脚本
└── README.md              # 项目说明
```

## 开发说明

### 本地开发

1. **后端开发**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

2. **前端开发**
- 直接编辑 `frontend/` 目录下的文件
- 使用现代浏览器打开 `index.html`

### API接口

- `GET /health` - 健康检查
- `POST /process` - 处理文章

### 环境变量

- `OPENAI_API_KEY` - OpenAI API密钥
- `OLLAMA_BASE_URL` - Ollama服务地址（默认：http://localhost:11434）

## 常见问题

### Q: 如何处理大文件？
A: 程序会自动限制输入长度，建议单次处理不超过3000字符。

### Q: 支持哪些文件格式？
A: 目前支持 TXT、Word(.docx)、PDF 格式。

### Q: 如何提高改写质量？
A: 可以尝试调整改写强度，或提供更详细的风格和立场要求。

### Q: 程序运行缓慢怎么办？
A: 建议使用本地Ollama模型，或检查网络连接（使用OpenAI API时）。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**Article ReAngle** - 让文章改写变得简单高效！

A local web app powered by LLMs that rewrites articles while preserving key information, enabling users to generate new versions with customizable style, perspective, and viewpoints.

---

## 1. Program Overview

This program is a **localhost web application** powered by **Large Language Models (LLMs)**.  
Core objectives:  

- Preserve the main information of the article  
- Adjust **style/perspective** according to user requirements  
- Generate a newly expressed version of the article  

Supported input methods: paste text / upload files / provide URL.  
Output methods: online reading, export as Word/PDF/Markdown.  

---

## 2. Input and Preprocessing

### Input Methods

1. **Paste text directly**  
2. **Upload files** (TXT / Word / PDF)  
3. **Enter article URL** (automatically extract the main body)  

### Preprocessing Logic

- **Word** → Extract body paragraphs  
- **PDF** → Parse text layer; if scanned, call OCR to extract text  
- **URL** → Extract main content and filter ads, navigation bars, etc.  

All inputs are eventually unified into **structured plain text**, ready for model processing.  

---

## 3. Model Processing Logic

Adopts a “two-step” strategy:  

1. **Key Point Extraction**  
   - Use LLM to summarize the article, extract core information and logical framework  
   - Ensure content fidelity, complete structure, and neutral stance  

2. **Perspective Rewriting**  
   - Combine extracted key points with user prompts  
   - User prompts support:  
     - **Style control** (academic / news reporting / humorous)  
     - **Perspective control** (supporting a policy / consumer’s viewpoint, etc.)  
   - Output a new article reflecting the chosen perspective  

---

## 4. Output and Display

### Display Options

- Direct reading on the web page  
- **Comparison view** between original and rewritten article (with similarity calculation)  

### Export Formats

- Word  
- PDF  
- Markdown / HTML  

---

## 5. User Interface and Interaction

- **Homepage functions**: paste text / upload file / enter URL  
- **Prompt input**: freeform entry & preset templates (academic, news, humorous, etc.)  
- **Rewrite intensity adjustment**: from light editing → full rewrite  
- **User experience**: progress display after submission → result page → read / compare / download  

---

## 6. Extended Features and Future Plans

- **API interface**: support for external system integration  
- **Logs & optimization**: keep processing logs (de-identified), useful for debugging and improvement  
- **Risk alerts**: notify users of compliance when dealing with sensitive or controversial topics  
- **Future plans**: expand into plugins (Word plugin, browser extension)  

---

## License

[MIT](LICENSE)
