// 全局变量
let currentResult = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 初始化应用
    console.log('Article ReAngle 初始化完成');
    
    // 文件选择处理
    const fileInput = document.getElementById('fileInput');
    const selectedFile = document.getElementById('selected-file');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    
    if (fileInput && selectedFile && fileName && removeFile) {
        console.log('文件选择元素找到，绑定事件监听器');
        
        // 文件选择事件
        fileInput.addEventListener('change', function(e) {
            console.log('文件选择事件触发', e.target.files.length);
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log('选择的文件:', file.name);
                fileName.textContent = file.name;
                selectedFile.classList.remove('hidden');
                console.log('文件显示区域应该已显示');
            }
        });
        
        // 移除文件事件
        removeFile.addEventListener('click', function() {
            console.log('移除文件');
            fileInput.value = '';
            selectedFile.classList.add('hidden');
        });
    } else {
        console.log('文件选择元素未找到:', {
            fileInput: !!fileInput,
            selectedFile: !!selectedFile,
            fileName: !!fileName,
            removeFile: !!removeFile
        });
    }
}

// 切换输入标签页
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

// 切换结果标签页
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

// 处理风格选择变化（已移除，现在使用统一的提示词输入）

// 更新强度值显示（已移除）

// 处理文章
async function processArticle() {
    const processBtn = document.getElementById('processBtn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('result-section');
    
    // 获取输入数据
    const inputData = getInputData();
    if (!inputData) {
        alert('请提供要处理的文章内容！');
        return;
    }
    
    // 获取改写要求
    const promptInput = document.getElementById('promptInput').value.trim();
    
    // 获取API Key（可选）
    const apiKeyInput = document.getElementById('apiKeyInput').value.trim();
    
    // 显示加载状态
    processBtn.disabled = true;
    processBtn.textContent = '处理中...';
    loading.classList.remove('hidden');
    resultSection.classList.add('hidden');
    
    try {
        // 构建请求数据
        const formData = new FormData();
        
        if (inputData.type === 'text') {
            formData.append('input_text', inputData.content);
        } else if (inputData.type === 'url') {
            formData.append('url', inputData.content);
        } else if (inputData.type === 'file') {
            formData.append('file', inputData.content);
        }
        
        if (promptInput) {
            formData.append('prompt', promptInput);
        }
        
        // 添加API Key
        formData.append('api_key', apiKeyInput);
        
        // 发送请求
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
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
        alert('处理失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        processBtn.disabled = false;
        processBtn.textContent = '🚀 开始洗稿';
        loading.classList.add('hidden');
    }
}

// 获取输入数据
function getInputData() {
    // 检查文本输入
    const textInput = document.getElementById('inputText');
    if (textInput.value.trim()) {
        return {
            type: 'text',
            content: textInput.value.trim()
        };
    }
    
    // 检查文件输入
    const fileInput = document.getElementById('fileInput');
    if (fileInput.files.length > 0) {
        return {
            type: 'file',
            content: fileInput.files[0]
        };
    }
    
    // 检查URL输入
    const urlInput = document.getElementById('urlInput');
    if (urlInput.value.trim()) {
        return {
            type: 'url',
            content: urlInput.value.trim()
        };
    }
    
    return null;
}

// 获取风格提示词（已移除，现在使用统一的提示词输入）

// 显示结果
function displayResults(result) {
    // 显示结果区域
    const resultSection = document.getElementById('result-section');
    resultSection.classList.remove('hidden');
    
    // 填充内容
    document.getElementById('rewrittenContent').textContent = result.rewritten;
    document.getElementById('rewrittenContentCompare').textContent = result.rewritten;
    document.getElementById('originalContent').textContent = result.original;
    document.getElementById('summaryContent').textContent = result.summary;
    
    // 计算并显示相似度
    const similarity = calculateSimilarity(result.original, result.rewritten);
    document.getElementById('similarityScore').textContent = Math.round(similarity * 100);
    
    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 计算文本相似度（简单实现）
function calculateSimilarity(text1, text2) {
    // 简单的字符级相似度计算
    const len1 = text1.length;
    const len2 = text2.length;
    const maxLen = Math.max(len1, len2);
    
    if (maxLen === 0) return 1;
    
    // 计算最长公共子序列
    const lcs = longestCommonSubsequence(text1, text2);
    return lcs / maxLen;
}

// 最长公共子序列
function longestCommonSubsequence(text1, text2) {
    const m = text1.length;
    const n = text2.length;
    const dp = Array(m + 1).fill().map(() => Array(n + 1).fill(0));
    
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (text1[i - 1] === text2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }
    
    return dp[m][n];
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
function downloadText(type, format) {
    if (!currentResult) return;
    
    let content = '';
    let filename = '';
    
    if (type === 'rewritten') {
        content = currentResult.rewritten;
        filename = 'rewritten_article';
    }
    
    let mimeType = 'text/plain';
    let extension = 'txt';
    
    if (format === 'md') {
        mimeType = 'text/markdown';
        extension = 'md';
    }
    
    filename += '.' + extension;
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

