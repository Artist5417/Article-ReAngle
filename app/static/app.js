/**
 * Article ReAngle - 前端逻辑
 * 处理用户交互、文件上传、API调用和结果渲染。
 */

// 全局变量
let currentResult = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
    try {
        // 显式打印前端脚本版本，便于定位缓存问题
        const APP_JS_VERSION = '2025-12-09a';
        console.log('[app.js] loaded, version =', APP_JS_VERSION);
    } catch (_) { }
    console.log('DOM加载完成');
    initializeApp();
});

/**
 * 初始化应用
 * 检查必要DOM元素并绑定事件监听器
 */
function initializeApp() {
    console.log('开始初始化应用');

    // 检查所有必要的元素
    const fileInput = document.getElementById('fileInput');
    const selectedFile = document.getElementById('selected-file');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');

    console.log('元素检查:', {
        fileInput: !!fileInput,
        selectedFile: !!selectedFile,
        fileName: !!fileName,
        removeFile: !!removeFile
    });

    if (fileInput) {
        console.log('绑定文件选择事件');
        fileInput.addEventListener('change', function (e) {
            console.log('文件选择事件触发！');
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log('选择的文件:', file.name);

                if (fileName) {
                    fileName.textContent = file.name;
                }
                if (selectedFile) {
                    selectedFile.style.display = 'flex';
                    selectedFile.classList.remove('hidden');
                }
            }
        });
    }

    if (removeFile && selectedFile) {
        removeFile.addEventListener('click', function () {
            console.log('移除文件');
            if (fileInput) fileInput.value = '';
            selectedFile.style.display = 'none';
            selectedFile.classList.add('hidden');
        });
    }

    console.log('初始化完成');
}

/**
 * 切换预设风格列表的显示状态
 */
function togglePresetList() {
    const list = document.getElementById('presetList');
    if (!list) return;
    list.classList.toggle('hidden');
}


/**
 * 切换提示词下拉菜单的显示状态
 * 打开下拉：在输入框聚焦时
 * 箭头按钮点击：展开/收起
 */
function togglePromptDropdown() {
    const dd = document.getElementById('presetDropdown');
    if (!dd) return;
    dd.classList.toggle('hidden');
}

/**
 * 应用预设风格到输入框
 * @param {string} text - 预设风格文本
 * 应用预设到 promptInput
 */
function applyPreset(text) {
    const promptInput = document.getElementById('promptInput');
    if (!promptInput) return;
    // 若已有内容，智能拼接；否则直接填充
    const existing = promptInput.value.trim();
    if (existing) {
        // 若已包含该风格，直接收起列表
        if (existing.includes(text)) {
            togglePresetList();
            return;
        }
        // 追加一个分隔符与风格关键词
        promptInput.value = existing + (existing.endsWith('；') || existing.endsWith(';') ? ' ' : '； ') + text;
    } else {
        promptInput.value = text;
    }
    // 移动光标到末尾并聚焦
    promptInput.focus();
    promptInput.selectionStart = promptInput.selectionEnd = promptInput.value.length;
    // 选择后自动收起
    const dd = document.getElementById('presetDropdown');
    if (dd && !dd.classList.contains('hidden')) dd.classList.add('hidden');
}

// 点击外部区域时收起下拉
document.addEventListener('click', function (e) {
    const wrapper = document.getElementById('promptWrapper');
    const dropdown = document.getElementById('presetDropdown');
    if (!wrapper || !dropdown) return;
    if (!wrapper.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

/**
 * 切换输入面板标签页
 * @param {string} tabName - 标签名称 (text/file/url/youtube)
 */
function switchTab(tabName) {
    // 隐藏所有面板
    document.querySelectorAll('.input-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // 移除所有标签按钮的active类
    document.querySelectorAll('.input-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的面板
    document.getElementById(tabName + '-input').classList.add('active');

    // 激活对应的标签按钮
    event.target.classList.add('active');
}

/**
 * 切换结果展示标签页
 * @param {string} tabName - 标签名称 (rewritten/compare/summary)
 */
function switchResultTab(tabName) {
    // 隐藏所有结果面板
    document.querySelectorAll('.result-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    // 移除所有结果标签按钮的active类
    document.querySelectorAll('.result-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的面板
    document.getElementById(tabName + '-panel').classList.add('active');

    // 激活对应的标签按钮
    event.target.classList.add('active');
}

/**
 * 处理文章改写请求
 * 收集输入数据，发送API请求，并处理响应
 */
async function processArticle() {
    const processBtn = document.getElementById('processBtn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('result-section');

    // 支持多源模式：必须先把内容添加到输入篮
    const useMulti = Array.isArray(inputItems) && inputItems.length > 0;

    if (!useMulti) {
        alert('请先将内容“添加到输入篮”后再开始洗稿');
        return;
    }

    // 获取改写要求
    const promptInput = document.getElementById('promptInput').value.trim();

    // 获取选择的语言模型
    const modelSelector = document.getElementById('modelSelector');
    const selectedModel = modelSelector ? modelSelector.value : 'gpt-5';

    // 显示加载状态
    processBtn.disabled = true;
    processBtn.textContent = '处理中...';
    loading.classList.remove('hidden');

    // 确保右边界面始终显示，显示处理中状态
    showProcessingState();

    try {
        let response;
        {
            const formData = new FormData();
            const inputsPayload = inputItems.map(it => {
                if (it.type === 'file') {
                    const key = `file_${it.id}`;
                    formData.append(key, it._file);
                    return { id: it.id, type: it.type, contentKey: key, meta: { filename: it.meta?.filename, size: it._file?.size } };
                }
                return { id: it.id, type: it.type, content: it.payload };
            });
            formData.append('inputs', JSON.stringify(inputsPayload));
            formData.append('prompt', promptInput);
            formData.append('llm_type', selectedModel);
            response = await fetch('/api/v1/rewrite', { method: 'POST', body: formData });
        }

        // 检查响应状态
        if (!response.ok) {
            const errorText = await response.text();
            console.error('服务器错误:', response.status, errorText);
            throw new Error(`服务器错误 (${response.status}): ${errorText.substring(0, 100)}...`);
        }

        const result = await response.json();
        currentResult = result;

        // 显示结果
        displayResults(result);

    } catch (error) {
        console.error('处理错误:', error);
        showErrorState(error.message);
    } finally {
        // 恢复按钮状态
        processBtn.disabled = false;
        processBtn.textContent = '🚀 开始洗稿';
        loading.classList.add('hidden');
    }
}

/**
 * 获取当前激活面板的输入数据
 * @returns {Object|null} 包含 type 和 content 的对象，若无效则返回 null
 */
function getInputData() {
    console.log('开始检查输入数据（基于当前激活页签）...');

    // 找到当前激活的输入面板
    const activePanel = document.querySelector('.input-panel.active');
    if (!activePanel) {
        console.log('未找到激活的输入面板');
        return null;
    }

    // 通过面板 id 判断类型：text-input / file-input / url-input
    const panelId = activePanel.id || '';
    let inputType = '';
    if (panelId.startsWith('text-')) inputType = 'text';
    else if (panelId.startsWith('file-')) inputType = 'file';
    else if (panelId.startsWith('url-')) inputType = 'url';
    else if (panelId.startsWith('youtube-')) inputType = 'youtube';

    // 根据当前类型仅读取对应控件
    if (inputType === 'text') {
        const inputTextEl = document.getElementById('inputText');
        const value = (inputTextEl?.value || '').trim();
        if (!value) return null;
        return { type: 'text', content: value };
    }

    if (inputType === 'file') {
        const fileInput = document.getElementById('fileInput');
        if (!fileInput || fileInput.files.length === 0) return null;
        return { type: 'file', content: fileInput.files[0] };
    }

    if (inputType === 'url') {
        const urlInput = document.getElementById('urlInput');
        const value = (urlInput?.value || '').trim();
        if (!value) return null;
        return { type: 'url', content: value };
    }

    if (inputType === 'youtube') {
        const ytInput = document.getElementById('youtubeInput');
        const value = (ytInput?.value || '').trim();
        if (!value) return null;
        return { type: 'youtube', content: value };
    }

    console.log('无法识别的输入类型，或当前面板无内容');
    return null;
}

// ================= 多源输入篮（前端收集，UI 展示） =================
let inputItems = [];

function addCurrentInput() {
    const data = getInputData();
    if (!data) {
        alert('请输入内容后再添加');
        return;
    }
    const id = `it_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const item = { id, type: data.type, meta: { createdAt: Date.now() } };
    if (data.type === 'file') {
        const f = data.content;
        item._file = f;
        item.meta.filename = f.name || '未命名文件';
        item.meta.title = `文件 · ${item.meta.filename}`;
    } else if (data.type === 'text') {
        const value = (data.content || '').toString();
        item.payload = value;
        item.meta.title = `文本 · ${value.slice(0, 30)}`;
        item.meta.meta = `${value.length} 字`;
    } else if (data.type === 'url') {
        const url = (data.content || '').toString();
        item.payload = url;
        try {
            const u = new URL(url);
            item.meta.title = `链接 · ${u.hostname}`;
            item.meta.meta = url;
        } catch (_) {
            item.meta.title = `链接 · ${url.slice(0, 30)}`;
            item.meta.meta = url;
        }
    } else if (data.type === 'youtube') {
        const yt = (data.content || '').toString();
        item.payload = yt;
        item.meta.title = `YouTube · ${yt.slice(0, 16)}`;
        item.meta.meta = yt;
    }
    inputItems.push(item);
    renderAddedList();
    // 根据本次输入类型清空对应控件
    clearInputsByType(data.type);
}

function removeInputItem(id) {
    inputItems = inputItems.filter(it => it.id !== id);
    renderAddedList();
}

function clearAllInputs() {
    inputItems = [];
    renderAddedList();
}

function renderAddedList() {
    const list = document.getElementById('addedList');
    if (!list) return;
    if (!inputItems.length) {
        list.innerHTML = '<div class="queue-empty">还没有添加内容，点击上方“添加到输入篮”</div>';
        return;
    }
    const iconOf = (type) => {
        if (type === 'text') return 'T';
        if (type === 'file') return 'F';
        if (type === 'url') return 'U';
        if (type === 'youtube') return 'Y';
        return '?';
    };
    list.innerHTML = inputItems.map(it => {
        const title = it.meta?.title || `${it.type}`;
        const meta = it.meta?.meta || (it.meta?.filename || '');
        return `<div class="queue-item" title="${(meta || '').replace(/"/g, '&quot;')}">
            <div class="qi-icon">${iconOf(it.type)}</div>
            <div class="qi-body">
                <div class="qi-title">${escapeHtml(title)}</div>
                <div class="qi-meta">${escapeHtml(meta || '')}</div>
            </div>
            <button class="qi-del" onclick="removeInputItem('${it.id}')">删除</button>
        </div>`;
    }).join('');
}

/**
 * 清空当前激活面板内指定类型的输入控件。
 * 优先在 .input-panel.active 作用域内查找，找不到再回退到全局 ID。
 */
function clearInputsByType(inputType) {
    const active = document.querySelector('.input-panel.active');
    if (inputType === 'text') {
        const el = (active && active.querySelector('textarea')) || document.getElementById('inputText');
        if (el) { el.value = ''; }
        return;
    }
    if (inputType === 'url') {
        const el = (active && active.querySelector('input[type="url"], input[type="text"]')) || document.getElementById('urlInput');
        if (el) { el.value = ''; }
        return;
    }
    if (inputType === 'youtube') {
        const el = (active && active.querySelector('input[type="url"], input[type="text"]')) || document.getElementById('youtubeInput');
        if (el) { el.value = ''; }
        return;
    }
    if (inputType === 'file') {
        const fileEl = (active && active.querySelector('input[type="file"]')) || document.getElementById('fileInput');
        if (fileEl) { fileEl.value = ''; }
        const selected = (active && (active.querySelector('#selected-file, .selected-file'))) || document.getElementById('selected-file');
        if (selected) { selected.style.display = 'none'; selected.classList.add('hidden'); }
        const fileName = (active && active.querySelector('#fileName')) || document.getElementById('fileName');
        if (fileName) { fileName.textContent = ''; }
    }
}

// 兼容保留：清空当前激活面板输入（委托给 clearInputsByType）
function clearActivePanelInputs() {
    const active = document.querySelector('.input-panel.active');
    if (!active) return;
    const pid = active.id || '';
    let inputType = '';
    if (pid.startsWith('text-')) inputType = 'text';
    else if (pid.startsWith('url-')) inputType = 'url';
    else if (pid.startsWith('youtube-')) inputType = 'youtube';
    else if (pid.startsWith('file-')) inputType = 'file';
    if (inputType) clearInputsByType(inputType);
}

/**
 * 显示处理中加载状态
 * 更新结果区域的 UI 以显示加载动画
 */
function showProcessingState() {
    const resultSection = document.getElementById('result-section');
    const rewrittenContent = document.getElementById('rewrittenContent');
    const originalContent = document.getElementById('originalContent');
    const summaryContent = document.getElementById('summaryContent');

    // 确保结果区域显示
    resultSection.classList.remove('hidden');

    // 显示处理中状态
    if (rewrittenContent) {
        rewrittenContent.innerHTML = '<div class="processing-state"><div class="spinner"></div><p>正在处理中...</p></div>';
    }

    if (originalContent) {
        originalContent.innerHTML = '<div class="processing-state"><div class="spinner"></div><p>正在处理中...</p></div>';
    }

    if (summaryContent) {
        summaryContent.innerHTML = '<div class="processing-state"><div class="spinner"></div><p>正在处理中...</p></div>';
    }

    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 显示错误状态
 * @param {string} errorMessage - 错误信息
 */
function showErrorState(errorMessage) {
    const resultSection = document.getElementById('result-section');
    const rewrittenContent = document.getElementById('rewrittenContent');
    const originalContent = document.getElementById('originalContent');
    const summaryContent = document.getElementById('summaryContent');

    // 确保结果区域显示
    resultSection.classList.remove('hidden');

    // 显示错误状态
    const errorHtml = `<div class="error-state">
        <div class="error-icon">❌</div>
        <h3>处理失败</h3>
        <p>${errorMessage}</p>
    </div>`;

    if (rewrittenContent) {
        rewrittenContent.innerHTML = errorHtml;
    }

    if (originalContent) {
        originalContent.innerHTML = errorHtml;
    }

    if (summaryContent) {
        summaryContent.innerHTML = errorHtml;
    }

    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 全局变量存储当前结果
let currentOriginalText = '';
let currentRewrittenText = '';

/**
 * 展示后端返回的结果
 * @param {Object} result - 后端返回的数据对象
 */
function displayResults(result) {
    const resultSection = document.getElementById('result-section');
    const originalContent = document.getElementById('originalContent');
    const rewrittenContent = document.getElementById('rewrittenContent');
    const rewrittenContentCompare = document.getElementById('rewrittenContentCompare');
    const summaryContent = document.getElementById('summaryContent');

    // 存储到全局变量
    currentOriginalText = result.original || '';
    currentRewrittenText = result.rewritten || '';

    if (originalContent) {
        // 原文也显示段落分割线，确保与右边对齐
        originalContent.innerHTML = renderOriginalWithSeparators(currentOriginalText);
    }

    if (rewrittenContent) {
        rewrittenContent.textContent = currentRewrittenText;
    }

    if (rewrittenContentCompare) {
        // 对比视图：左右两列分开渲染，右侧用与左侧相同的段落块结构，便于虚线对齐
        rewrittenContentCompare.innerHTML = renderRewrittenWithSeparators(currentOriginalText, currentRewrittenText);
    }

    // 动态调整分割线位置
    setTimeout(() => {
        adjustSeparatorAlignment();
    }, 100);

    if (summaryContent) {
        summaryContent.textContent = result.summary || '';
    }

    // 确保结果区域显示
    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 将文本分割为段落
 * @param {string} text - 输入文本
 * @returns {Array<string>} 段落数组
 */
function splitIntoParagraphs(text) {
    if (!text) return [];

    // 清理文本，移除多余的空白字符
    text = text.replace(/\s+/g, ' ').trim();

    // 先按双换行符分割（保持原有段落结构）
    let paragraphs = text.split(/\n\s*\n/);

    // 如果没有双换行符，进行智能分割
    if (paragraphs.length === 1) {
        paragraphs = intelligentParagraphSplit(text);
    }

    // 进一步优化段落分割
    paragraphs = optimizeParagraphSegmentation(paragraphs);

    return paragraphs.map(p => p.trim()).filter(p => p.length > 0);
}

/**
 * 智能段落分割算法
 * 基于标点和长度进行分割
 * @param {string} text - 输入文本
 * @returns {Array<string>} 段落数组
 */
function intelligentParagraphSplit(text) {
    const paragraphs = [];
    const sentences = text.split(/([。！？；])/);
    let currentPara = '';
    let sentenceCount = 0;

    for (let i = 0; i < sentences.length; i += 2) {
        const sentence = sentences[i];
        const punctuation = sentences[i + 1] || '';

        if (sentence.trim()) {
            currentPara += sentence.trim() + punctuation;
            sentenceCount++;

            // 段落分割条件：
            // 1. 句子数量达到3-5个
            // 2. 段落长度超过150字符
            // 3. 遇到明显的段落标记词
            const shouldSplit = (
                sentenceCount >= 3 &&
                (currentPara.length > 150 || hasParagraphMarker(currentPara))
            );

            if (shouldSplit) {
                paragraphs.push(currentPara.trim());
                currentPara = '';
                sentenceCount = 0;
            }
        }
    }

    // 添加最后一个段落
    if (currentPara.trim()) {
        paragraphs.push(currentPara.trim());
    }

    return paragraphs;
}

// 检查是否包含段落标记词
function hasParagraphMarker(text) {
    const markers = [
        '首先', '其次', '再次', '最后', '总之', '综上所述',
        '另外', '此外', '同时', '然而', '但是', '不过',
        '因此', '所以', '由此可见', '总的来说', '简而言之'
    ];

    return markers.some(marker => text.includes(marker));
}

// 优化段落分割
function optimizeParagraphSegmentation(paragraphs) {
    const optimized = [];

    for (let i = 0; i < paragraphs.length; i++) {
        const para = paragraphs[i];

        // 如果段落过长（超过500字符），尝试进一步分割
        if (para.length > 500) {
            const subParagraphs = splitLongParagraph(para);
            optimized.push(...subParagraphs);
        } else {
            optimized.push(para);
        }
    }

    return optimized;
}

// 分割过长的段落
function splitLongParagraph(text) {
    const sentences = text.split(/([。！？；])/);
    const subParagraphs = [];
    let currentPara = '';
    let sentenceCount = 0;

    for (let i = 0; i < sentences.length; i += 2) {
        const sentence = sentences[i];
        const punctuation = sentences[i + 1] || '';

        if (sentence.trim()) {
            currentPara += sentence.trim() + punctuation;
            sentenceCount++;

            // 每2-3个句子分割一次
            if (sentenceCount >= 2 && currentPara.length > 200) {
                subParagraphs.push(currentPara.trim());
                currentPara = '';
                sentenceCount = 0;
            }
        }
    }

    if (currentPara.trim()) {
        subParagraphs.push(currentPara.trim());
    }

    return subParagraphs;
}

/**
 * 渲染对齐的段落对比视图
 * @param {string} originalText - 原文
 * @param {string} rewrittenText - 改写文
 * @returns {string} 构建的 HTML 字符串
 */
function renderAlignedParagraphs(originalText, rewrittenText) {
    const originalParagraphs = splitIntoParagraphs(originalText);
    const rewrittenParagraphs = splitIntoParagraphs(rewrittenText);

    // 智能段落对齐
    const alignedPairs = alignParagraphs(originalParagraphs, rewrittenParagraphs);

    let html = '<div class="paragraph-comparison">';

    for (let i = 0; i < alignedPairs.length; i++) {
        const pair = alignedPairs[i];
        const originalPara = pair.original || '';
        const rewrittenPara = pair.rewritten || '';

        // 计算段落高度，用于动态调整分割线
        const originalHeight = calculateParagraphHeight(originalPara);
        const rewrittenHeight = calculateParagraphHeight(rewrittenPara);
        const maxHeight = Math.max(originalHeight, rewrittenHeight);

        html += `<div class="paragraph-pair" data-paragraph-number="${i + 1}" data-max-height="${maxHeight}">`;

        // 左边原文段落
        html += '<div class="paragraph-original">';
        html += `<div class="paragraph-content" style="min-height: ${maxHeight * 1.6}em;">${escapeHtml(originalPara)}</div>`;
        html += '</div>';

        // 右边改写段落
        html += '<div class="paragraph-rewritten">';
        if (rewrittenPara) {
            html += `<div class="paragraph-content" style="min-height: ${maxHeight * 1.6}em;">${highlightParagraphChanges(originalPara, rewrittenPara)}</div>`;
        } else {
            html += `<div class="paragraph-content empty-paragraph" style="min-height: ${maxHeight * 1.6}em;"></div>`;
        }
        html += '</div>';

        html += '</div>';
    }

    html += '</div>';
    return html;
}

// 智能段落对齐算法
function alignParagraphs(originalParagraphs, rewrittenParagraphs) {
    const alignedPairs = [];
    const maxParagraphs = Math.max(originalParagraphs.length, rewrittenParagraphs.length);

    for (let i = 0; i < maxParagraphs; i++) {
        const originalPara = originalParagraphs[i] || '';
        const rewrittenPara = rewrittenParagraphs[i] || '';

        // 如果右侧缺段，创建空白占位符
        const alignedPair = {
            original: originalPara,
            rewritten: rewrittenPara || createEmptyParagraphPlaceholder()
        };

        alignedPairs.push(alignedPair);
    }

    return alignedPairs;
}

// 创建空白段落占位符
function createEmptyParagraphPlaceholder() {
    return ''; // 返回空字符串，由CSS样式处理显示
}

// 计算段落高度
function calculateParagraphHeight(text) {
    if (!text) return 1;

    // 基于文本长度和换行符数量估算高度
    const lineCount = text.split('\n').length;
    const charCount = text.length;
    const estimatedLines = Math.max(lineCount, Math.ceil(charCount / 50));

    return Math.max(1, estimatedLines);
}

/**
 * 高亮显示段落内的文本变化
 * @param {string} originalPara - 原文段落
 * @param {string} rewrittenPara - 改写段落
 * @returns {string} 包含高亮标签的 HTML
 */
function highlightParagraphChanges(originalPara, rewrittenPara) {
    if (!originalPara || !rewrittenPara) {
        return escapeHtml(rewrittenPara);
    }

    // 使用更智能的差异检测
    const diff = computeSmartDiff(originalPara, rewrittenPara);
    let result = '';

    for (const part of diff) {
        if (part.type === 'equal') {
            result += escapeHtml(part.text);
        } else if (part.type === 'insert' || part.type === 'replace') {
            result += `<span class="text-changed">${escapeHtml(part.text)}</span>`;
        }
    }

    return result;
}

// 智能差异检测
function computeSmartDiff(text1, text2) {
    const words1 = text1.split(/(\s+|[，。！？；：""''（）【】])/);
    const words2 = text2.split(/(\s+|[，。！？；：""''（）【】])/);

    const diff = [];
    let i = 0, j = 0;

    while (i < words1.length || j < words2.length) {
        if (i >= words1.length) {
            diff.push({ type: 'insert', text: words2[j] });
            j++;
        } else if (j >= words2.length) {
            diff.push({ type: 'delete', text: words1[i] });
            i++;
        } else if (words1[i] === words2[j]) {
            diff.push({ type: 'equal', text: words1[i] });
            i++;
            j++;
        } else {
            // 查找最佳匹配
            const match = findBestMatch(words1, words2, i, j);
            if (match.distance <= 3) {
                // 在范围内找到匹配
                for (let k = i; k < match.index1; k++) {
                    diff.push({ type: 'delete', text: words1[k] });
                }
                for (let k = j; k < match.index2; k++) {
                    diff.push({ type: 'insert', text: words2[k] });
                }
                i = match.index1;
                j = match.index2;
            } else {
                // 直接替换
                diff.push({ type: 'replace', text: words2[j] });
                i++;
                j++;
            }
        }
    }

    return diff;
}

// 查找最佳匹配
function findBestMatch(words1, words2, start1, start2) {
    let bestMatch = { index1: words1.length, index2: words2.length, distance: Infinity };

    for (let i = start1 + 1; i < Math.min(start1 + 10, words1.length); i++) {
        for (let j = start2 + 1; j < Math.min(start2 + 10, words2.length); j++) {
            if (words1[i] === words2[j]) {
                const distance = Math.max(i - start1, j - start2);
                if (distance < bestMatch.distance) {
                    bestMatch = { index1: i, index2: j, distance };
                }
            }
        }
    }

    return bestMatch;
}

// 计算段落差异
function computeParagraphDiff(text1, text2) {
    const words1 = text1.split(/(\s+|[，。！？；：""''（）【】])/);
    const words2 = text2.split(/(\s+|[，。！？；：""''（）【】])/);

    const diff = [];
    let i = 0, j = 0;

    while (i < words1.length || j < words2.length) {
        if (i >= words1.length) {
            diff.push({ type: 'insert', text: words2[j] });
            j++;
        } else if (j >= words2.length) {
            diff.push({ type: 'delete', text: words1[i] });
            i++;
        } else if (words1[i] === words2[j]) {
            diff.push({ type: 'equal', text: words1[i] });
            i++;
            j++;
        } else {
            // 查找下一个匹配
            const nextMatch1 = findNextWordMatch(words1, words2, i, j);
            const nextMatch2 = findNextWordMatch(words2, words1, j, i);

            if (nextMatch1.distance <= nextMatch2.distance && nextMatch1.distance < 5) {
                for (let k = i; k < nextMatch1.index; k++) {
                    diff.push({ type: 'delete', text: words1[k] });
                }
                i = nextMatch1.index;
            } else if (nextMatch2.distance < 5) {
                for (let k = j; k < nextMatch2.index; k++) {
                    diff.push({ type: 'insert', text: words2[k] });
                }
                j = nextMatch2.index;
            } else {
                diff.push({ type: 'replace', text: words2[j] });
                i++;
                j++;
            }
        }
    }

    return diff;
}

// 查找下一个词匹配
function findNextWordMatch(words1, words2, start1, start2) {
    for (let i = start1 + 1; i < Math.min(start1 + 10, words1.length); i++) {
        for (let j = start2 + 1; j < Math.min(start2 + 10, words2.length); j++) {
            if (words1[i] === words2[j]) {
                return { index: i, distance: i - start1 };
            }
        }
    }
    return { index: words1.length, distance: Infinity };
}

// HTML转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 动态调整分割线对齐
function adjustSeparatorAlignment() {
    const originalContent = document.getElementById('originalContent');
    const rewrittenContent = document.getElementById('rewrittenContentCompare');

    if (!originalContent || !rewrittenContent) return;

    const originalBlocks = originalContent.querySelectorAll('.paragraph-block');
    const rewrittenBlocks = rewrittenContent.querySelectorAll('.paragraph-block');

    // 确保段落数量一致
    const maxBlocks = Math.max(originalBlocks.length, rewrittenBlocks.length);

    // 根据较长段落调整高度，确保分割线对齐
    for (let i = 0; i < maxBlocks; i++) {
        const originalBlock = originalBlocks[i];
        const rewrittenBlock = rewrittenBlocks[i];

        if (originalBlock && rewrittenBlock) {
            // 等待内容渲染完成
            setTimeout(() => {
                const originalHeight = originalBlock.offsetHeight;
                const rewrittenHeight = rewrittenBlock.offsetHeight;
                const maxHeight = Math.max(originalHeight, rewrittenHeight);

                // 设置最小高度确保对齐
                if (originalHeight < maxHeight) {
                    originalBlock.style.minHeight = maxHeight + 'px';
                }
                if (rewrittenHeight < maxHeight) {
                    rewrittenBlock.style.minHeight = maxHeight + 'px';
                }

                // 确保分割线位置一致
                const originalSeparator = originalBlock.querySelector('.paragraph-separator');
                const rewrittenSeparator = rewrittenBlock.querySelector('.paragraph-separator');

                if (originalSeparator && rewrittenSeparator) {
                    // 分割线位置基于较长段落
                    const separatorPosition = maxHeight + 20; // 20px margin
                    originalSeparator.style.marginTop = '20px';
                    rewrittenSeparator.style.marginTop = '20px';
                }
            }, 100);
        }
    }
}

/**
 * 渲染带有分割线的原文
 * @param {string} originalText - 原文
 * @returns {string} 构建的 HTML 字符串
 */
function renderOriginalWithSeparators(originalText) {
    const paragraphs = splitIntoParagraphs(originalText);
    let html = '<div class="paragraphs-with-separators">';
    const total = paragraphs.length;

    for (let i = 0; i < paragraphs.length; i++) {
        const para = paragraphs[i];
        html += `<div class=\"paragraph-block\" data-paragraph-index=\"${i}\" data-paragraph-number=\"${i + 1}\" data-total=\"${total}\" data-side=\"left\">`;
        html += `<div class="paragraph-content">${escapeHtml(para)}</div>`;
        if (i < paragraphs.length - 1) {
            html += '<div class="paragraph-separator"></div>';
        }
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// 渲染带分割线的新文
function renderRewrittenWithSeparators(originalText, rewrittenText) {
    const originalParagraphs = splitIntoParagraphs(originalText);
    const rewrittenParagraphs = splitIntoParagraphs(rewrittenText);
    let html = '<div class="paragraphs-with-separators">';

    // 确保段落数量一致，以原文段落数量为准
    const maxParagraphs = Math.max(originalParagraphs.length, rewrittenParagraphs.length);
    const total = maxParagraphs;

    for (let i = 0; i < maxParagraphs; i++) {
        const originalPara = originalParagraphs[i] || '';
        const rewrittenPara = rewrittenParagraphs[i] || '';

        html += `<div class=\"paragraph-block\" data-paragraph-index=\"${i}\" data-paragraph-number=\"${i + 1}\" data-total=\"${total}\" data-side=\"right\">`;
        if (rewrittenPara) {
            html += `<div class="paragraph-content">${highlightParagraphChanges(originalPara, rewrittenPara)}</div>`;
        } else {
            html += `<div class="paragraph-content empty-paragraph">此段落在改写版本中不存在</div>`;
        }
        if (i < maxParagraphs - 1) {
            html += '<div class="paragraph-separator"></div>';
        }
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// 高亮显示文本变化（保持原有功能）
function highlightChanges(originalText, rewrittenText) {
    if (!originalText || !rewrittenText) {
        return rewrittenText || '';
    }

    // 使用段落对比视图
    return renderAlignedParagraphs(originalText, rewrittenText);
}

// 高亮单行内的变化
function highlightLineChanges(originalLine, rewrittenLine) {
    if (!originalLine || !rewrittenLine) {
        return rewrittenLine;
    }

    // 使用更智能的差异检测
    const diff = computeDiff(originalLine, rewrittenLine);
    let result = '';

    for (const part of diff) {
        if (part.type === 'equal') {
            result += part.text;
        } else if (part.type === 'insert' || part.type === 'replace') {
            result += `<span class="text-changed">${part.text}</span>`;
        }
    }

    return result;
}

// 计算文本差异
function computeDiff(text1, text2) {
    const words1 = text1.split(/(\s+|[，。！？；：""''（）【】])/);
    const words2 = text2.split(/(\s+|[，。！？；：""''（）【】])/);

    const diff = [];
    let i = 0, j = 0;

    while (i < words1.length || j < words2.length) {
        if (i >= words1.length) {
            // 只有text2有内容，是新增
            diff.push({ type: 'insert', text: words2[j] });
            j++;
        } else if (j >= words2.length) {
            // 只有text1有内容，是删除
            diff.push({ type: 'delete', text: words1[i] });
            i++;
        } else if (words1[i] === words2[j]) {
            // 相同内容
            diff.push({ type: 'equal', text: words1[i] });
            i++;
            j++;
        } else {
            // 不同内容，检查是否是替换
            const match1 = findNextMatch(words1, words2, i, j);
            const match2 = findNextMatch(words2, words1, j, i);

            if (match1.distance <= match2.distance && match1.distance < 3) {
                // 在text1中找到匹配
                for (let k = i; k < match1.index; k++) {
                    diff.push({ type: 'delete', text: words1[k] });
                }
                i = match1.index;
            } else if (match2.distance < 3) {
                // 在text2中找到匹配
                for (let k = j; k < match2.index; k++) {
                    diff.push({ type: 'insert', text: words2[k] });
                }
                j = match2.index;
            } else {
                // 没有找到匹配，直接替换
                diff.push({ type: 'replace', text: words2[j] });
                i++;
                j++;
            }
        }
    }

    return diff;
}

// 查找下一个匹配
function findNextMatch(words1, words2, start1, start2) {
    for (let i = start1 + 1; i < words1.length; i++) {
        for (let j = start2 + 1; j < words2.length; j++) {
            if (words1[i] === words2[j]) {
                return { index: i, distance: i - start1 };
            }
        }
    }
    return { index: words1.length, distance: Infinity };
}

// 找到最长公共子序列
function findLCS(arr1, arr2) {
    const m = arr1.length;
    const n = arr2.length;
    const dp = Array(m + 1).fill().map(() => Array(n + 1).fill(0));

    // 构建DP表
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (arr1[i - 1] === arr2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    // 回溯找到LCS
    const lcs = [];
    let i = m, j = n;
    while (i > 0 && j > 0) {
        if (arr1[i - 1] === arr2[j - 1]) {
            lcs.unshift(arr1[i - 1]);
            i--;
            j--;
        } else if (dp[i - 1][j] > dp[i][j - 1]) {
            i--;
        } else {
            j--;
        }
    }

    return lcs;
}

// 复制文本
function copyText(type) {
    let text = '';
    if (type === 'rewritten') {
        text = document.getElementById('rewrittenContent').textContent;
    }

    navigator.clipboard.writeText(text).then(() => {
        alert('已复制到剪贴板！');
    }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动选择文本复制');
    });
}

// 下载文本
function downloadText(type) {
    if (!currentResult) return;

    let content = '';
    let filename = '';

    if (type === 'rewritten') {
        content = currentResult.rewritten || '';
        filename = 'rewritten_article.txt';
    } else if (type === 'original') {
        content = currentResult.original || '';
        filename = 'original_article.txt';
    }

    if (!content) {
        alert('没有内容可下载');
        return;
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}


/**
 * 此时添加 getTTSResult 函数
 * 调用后端 TTS 接口
 * @param {string} source - 文本来源 'summary' 或 'rewritten'
 */
async function getTTSResult(source) {
    let text = '';
    let header = null;

    if (source === 'summary') {
        const el = document.getElementById('summaryContent');
        text = el ? el.textContent : '';
        header = document.querySelector('#summary-section-inner .result-header');
    } else if (source === 'rewritten') {
        // 优先取全局变量
        text = typeof currentRewrittenText !== 'undefined' ? currentRewrittenText : (document.getElementById('rewrittenContent')?.textContent || '');
        header = document.querySelector('#rewritten-panel .result-header');
    }

    text = text.trim();
    if (!text) {
        alert('没有可朗读的文本内容');
        return;
    }

    if (text.length > 600) {
        alert('文本过长（超过600字），无法进行语音合成。');
        return;
    }

    // 显式捕获 button 元素，防止 async/await 后 event 丢失
    const btn = (event && event.target) ? event.target : null;
    const originalBtnText = btn ? btn.innerText : '🔊 朗读';

    if (btn) {
        btn.innerText = '⏳ 请求中...';
        btn.disabled = true;
    }

    try {
        const response = await fetch('/api/v1/rewrite/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                model: 'qwen3-tts-flash',
                voice: 'Cherry'
            })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`TTS 请求失败: ${response.status} ${errText}`);
        }

        const data = await response.json();

        if (data.audio_url) {
            // 请求成功，立即恢复按钮状态
            if (btn) {
                btn.innerText = originalBtnText;
                btn.disabled = false;
            }

            // 创建或更新音频播放器
            let audioPlayer = header.querySelector('.tts-player');
            if (!audioPlayer) {
                audioPlayer = document.createElement('audio');
                audioPlayer.className = 'tts-player';
                audioPlayer.controls = true;
                audioPlayer.style.marginTop = '10px';
                audioPlayer.style.width = '100%';
                // 插入到 header 末尾
                header.parentNode.insertBefore(audioPlayer, header.nextSibling);
            }

            audioPlayer.src = data.audio_url;
            audioPlayer.style.display = 'block';

            // 尝试自动播放
            try {
                await audioPlayer.play();
            } catch (playErr) {
                console.warn('Auto-play failed:', playErr);
            }
        } else {
            alert('TTS 请求成功，但未返回音频 URL');
        }

    } catch (error) {
        console.error('getTTSResult error:', error);
        alert('朗读请求出错: ' + error.message);
    } finally {
        // 恢复按钮状态
        if (btn) {
            btn.innerText = originalBtnText;
            btn.disabled = false;
        }
    }
}
