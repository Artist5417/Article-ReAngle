// 全局变量
let currentResult = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成 - 新版本');
    initializeApp();
});

function initializeApp() {
    console.log('开始初始化应用 - 新版本');
    
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
        fileInput.addEventListener('change', function(e) {
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
        removeFile.addEventListener('click', function() {
            console.log('移除文件');
            if (fileInput) fileInput.value = '';
            selectedFile.style.display = 'none';
            selectedFile.classList.add('hidden');
        });
    }
    
    console.log('初始化完成 - 新版本');
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
        // 构建FormData
        const formData = new FormData();
        
        console.log('输入数据类型:', inputData.type);
        console.log('输入数据内容:', inputData.content);
        
        if (inputData.type === 'text') {
            formData.append('input_text', inputData.content);
            console.log('添加文本数据到FormData');
        } else if (inputData.type === 'file') {
            formData.append('file', inputData.content);
            console.log('添加文件数据到FormData');
        } else if (inputData.type === 'url') {
            formData.append('url', inputData.content);
            console.log('添加URL数据到FormData:', inputData.content);
        }
        
        formData.append('prompt', promptInput);
        formData.append('api_key', apiKeyInput);
        
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
    console.log('开始检查输入数据...');
    
    // 检查文本输入
    const inputText = document.getElementById('inputText').value.trim();
    console.log('文本输入:', inputText);
    if (inputText) {
        console.log('使用文本输入');
        return {
            type: 'text',
            content: inputText
        };
    }
    
    // 检查文件输入
    const fileInput = document.getElementById('fileInput');
    console.log('文件输入:', fileInput.files.length);
    if (fileInput.files.length > 0) {
        console.log('使用文件输入');
        return {
            type: 'file',
            content: fileInput.files[0]
        };
    }
    
    // 检查URL输入
    const urlInput = document.getElementById('urlInput');
    const urlValue = urlInput.value.trim();
    console.log('URL输入:', urlValue);
    if (urlValue) {
        console.log('使用URL输入');
        return {
            type: 'url',
            content: urlValue
        };
    }
    
    console.log('没有找到任何输入');
    return null;
}

// 显示结果
function displayResults(result) {
    const resultSection = document.getElementById('result-section');
    const originalContent = document.getElementById('originalContent');
    const rewrittenContent = document.getElementById('rewrittenContent');
    const summaryContent = document.getElementById('summaryContent');
    
    if (originalContent) {
        originalContent.textContent = result.original || '';
    }
    
    if (rewrittenContent) {
        rewrittenContent.textContent = result.rewritten || '';
    }
    
    if (summaryContent) {
        summaryContent.textContent = result.summary || '';
    }
    
    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });
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
