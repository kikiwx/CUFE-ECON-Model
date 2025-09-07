/**
 * CUFE经济学大模型助手 - 主JavaScript文件
 * 中央财经大学经济学院
 */

const CONFIG = {
    API_BASE: '/api',
    POLLING_INTERVAL: 2000,
    MAX_MESSAGE_LENGTH: 4000,
    AUTO_SCROLL_DELAY: 100
};

let messages = [];
let messageIdCounter = 0;
let isTyping = false;
let isModelReady = false;
let currentReportId = null;
let reportPollingInterval = null;

let domElements = {};

/**
 * 初始化DOM元素引用
 */
function initDOMElements() {
    domElements = {

        messagesContainer: document.getElementById('messagesContainer'),
        messageInput: document.getElementById('messageInput'),
        sendButton: document.getElementById('sendButton'),
        statusIndicator: document.getElementById('statusIndicator'),
        statusText: document.getElementById('statusText'),
        settingsToggle: document.getElementById('settingsToggle'),
        settingsPanel: document.getElementById('settingsPanel'),


        reportBtn: document.getElementById('reportBtn'),
        reportButtonSmall: document.getElementById('reportButtonSmall'),
        reportListBtn: document.getElementById('reportListBtn'),
        reportModal: document.getElementById('reportModal'),
        reportListModal: document.getElementById('reportListModal'),
        closeReportModal: document.getElementById('closeReportModal'),
        closeReportListModal: document.getElementById('closeReportListModal'),
        reportTopic: document.getElementById('reportTopic'),
        reportRequirements: document.getElementById('reportRequirements'),
        startGeneration: document.getElementById('startGeneration'),
        cancelReport: document.getElementById('cancelReport'),
        reportProgress: document.getElementById('reportProgress'),
        progressFill: document.getElementById('progressFill'),
        progressPercentage: document.getElementById('progressPercentage'),
        progressStatus: document.getElementById('progressStatus'),
        progressSections: document.getElementById('progressSections'),
        downloadOptions: document.getElementById('downloadOptions'),
        downloadWord: document.getElementById('downloadWord'),

        reportListLoading: document.getElementById('reportListLoading'),
        reportListContainer: document.getElementById('reportListContainer'),
        reportListEmpty: document.getElementById('reportListEmpty'),

        maxTokensInput: document.getElementById('maxTokens'),
        temperatureInput: document.getElementById('temperature'),
        temperatureValue: document.getElementById('temperatureValue'),
        enableThinkingInput: document.getElementById('enableThinking'),

        quickOptions: document.getElementById('quickOptions')
    };
}

/**
 * 配置markdown渲染器
 */
function configureMarkdown() {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {
                        console.warn('代码高亮失败:', err);
                    }
                }
                if (typeof hljs !== 'undefined') {
                    return hljs.highlightAuto(code).value;
                }
                return code;
            },
            breaks: true,
            gfm: true,
            sanitize: false
        });
    }
}

/**
 * 应用初始化
 */
function initializeApp() {
    // 设置欢迎消息时间
    const welcomeTimeElement = document.getElementById('welcome-time');
    if (welcomeTimeElement) {
        welcomeTimeElement.textContent = formatTime(new Date());
    }

    initDOMElements();

    configureMarkdown();

    bindEvents();

    checkModelStatus();
    setInterval(checkModelStatus, 5000);

    window.addEventListener('load', function() {
        if (domElements.messageInput) {
            domElements.messageInput.focus();
        }
        scrollToBottom();
    });

    window.addEventListener('resize', scrollToBottom);

    window.addEventListener('unhandledrejection', function(event) {
        console.error('未处理的Promise错误:', event.reason);
        showError('发生了未知错误，请稍后重试');
    });

    window.addEventListener('beforeunload', function() {
        if (reportPollingInterval) {
            clearInterval(reportPollingInterval);
        }
    });
}

/**
 * 绑定所有事件监听器
 */
function bindEvents() {
    // 基础聊天功能
    if (domElements.sendButton) {
        domElements.sendButton.addEventListener('click', handleSendMessage);
    }
    if (domElements.messageInput) {
        domElements.messageInput.addEventListener('keydown', handleKeyPress);
        domElements.messageInput.addEventListener('input', handleInputChange);
    }

    if (domElements.settingsToggle) {
        domElements.settingsToggle.addEventListener('click', toggleSettings);
    }
    if (domElements.temperatureInput) {
        domElements.temperatureInput.addEventListener('input', updateTemperatureDisplay);
    }

    if (domElements.reportBtn) {
        domElements.reportBtn.addEventListener('click', openReportModal);
    }
    if (domElements.reportButtonSmall) {
        domElements.reportButtonSmall.addEventListener('click', openReportModal);
    }
    if (domElements.reportListBtn) {
        domElements.reportListBtn.addEventListener('click', openReportListModal);
    }
    if (domElements.closeReportModal) {
        domElements.closeReportModal.addEventListener('click', closeReportModalFunc);
    }
    if (domElements.closeReportListModal) {
        domElements.closeReportListModal.addEventListener('click', closeReportListModalFunc);
    }
    if (domElements.cancelReport) {
        domElements.cancelReport.addEventListener('click', closeReportModalFunc);
    }
    if (domElements.startGeneration) {
        domElements.startGeneration.addEventListener('click', startReportGeneration);
    }

    document.addEventListener('click', function(e) {
        if (e.target === domElements.reportModal) {
            closeReportModalFunc();
        }
        if (e.target === domElements.reportListModal) {
            closeReportListModalFunc();
        }
        if (domElements.settingsPanel && domElements.settingsToggle &&
            !domElements.settingsPanel.contains(e.target) &&
            !domElements.settingsToggle.contains(e.target)) {
            domElements.settingsPanel.classList.remove('open');
        }
    });
}

/**
 * 格式化时间显示
 */
function formatTime(timestamp) {
    return timestamp.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    if (domElements.messagesContainer) {
        setTimeout(() => {
            domElements.messagesContainer.scrollTop = domElements.messagesContainer.scrollHeight;
        }, CONFIG.AUTO_SCROLL_DELAY);
    }
}

/**
 * 显示错误消息
 */
function showError(errorMsg) {
    if (!domElements.messagesContainer) return;

    const errorDiv = document.createElement('div');
    errorDiv.className = 'message';
    errorDiv.innerHTML = `
        <div class="avatar">
            <img src="/static/icons/t1.svg" alt="AI Assistant" style="width: 100%; height: 100%; object-fit: contain;" />
        </div>
        <div class="message-bubble assistant">
            <div class="error-message">${errorMsg}</div>
            <div class="message-time assistant">${formatTime(new Date())}</div>
        </div>
    `;
    domElements.messagesContainer.appendChild(errorDiv);
    scrollToBottom();
}

/**
 * 检查模型状态
 */
async function checkModelStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();

        if (data.status === 'ready') {
            isModelReady = true;
            if (domElements.statusIndicator) {
                domElements.statusIndicator.className = 'status-indicator status-online';
            }
            if (domElements.statusText) {
                domElements.statusText.textContent = '在线';
            }
        } else {
            isModelReady = false;
            if (domElements.statusIndicator) {
                domElements.statusIndicator.className = 'status-indicator status-loading';
            }
            if (domElements.statusText) {
                domElements.statusText.textContent = '加载中...';
            }
        }
    } catch (error) {
        isModelReady = false;
        if (domElements.statusIndicator) {
            domElements.statusIndicator.className = 'status-indicator status-offline';
        }
        if (domElements.statusText) {
            domElements.statusText.textContent = '连接失败';
        }
    }

    updateSendButtonState();
}

/**
 * 更新发送按钮状态
 */
function updateSendButtonState() {
    if (domElements.sendButton) {
        const inputValue = domElements.messageInput ? domElements.messageInput.value.trim() : '';
        domElements.sendButton.disabled = inputValue === '' || isTyping || !isModelReady;
    }
}

/**
 * 处理输入框变化
 */
function handleInputChange() {
    if (!domElements.messageInput) return;

    const input = domElements.messageInput;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    updateSendButtonState();

    if (input.value.trim() !== '') {
        hideQuickOptionsOnInput();
    } else {
        showQuickOptionsIfEmpty();
    }
}

/**
 * 处理键盘事件
 */
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
}

/**
 * 选择快捷选项
 */
function selectQuickOption(text) {
    if (domElements.messageInput) {
        domElements.messageInput.value = text;
        domElements.messageInput.focus();
        handleInputChange();
    }

    if (domElements.quickOptions) {
        domElements.quickOptions.style.opacity = '0';
        domElements.quickOptions.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            domElements.quickOptions.style.display = 'none';
        }, 300);
    }
}

/**
 * 当用户输入时隐藏快捷选项
 */
function hideQuickOptionsOnInput() {
    if (domElements.quickOptions && domElements.quickOptions.style.display !== 'none') {
        domElements.quickOptions.style.opacity = '0.3';
        domElements.quickOptions.style.transform = 'translateY(-5px)';
    }
}

/**
 * 当输入框为空时显示快捷选项
 */
function showQuickOptionsIfEmpty() {
    if (domElements.quickOptions && domElements.messageInput &&
        domElements.messageInput.value.trim() === '' && messages.length <= 1) {
        domElements.quickOptions.style.display = 'block';
        domElements.quickOptions.style.opacity = '0.7';
        domElements.quickOptions.style.transform = 'translateY(0)';
    }
}

/**
 * 发送消息
 */
async function handleSendMessage() {
    if (!domElements.messageInput) return;

    const message = domElements.messageInput.value.trim();
    if (message === '' || isTyping || !isModelReady) return;

    if (domElements.quickOptions) {
        domElements.quickOptions.style.display = 'none';
    }

    addMessage('user', message);
    domElements.messageInput.value = '';
    domElements.messageInput.style.height = 'auto';
    updateSendButtonState();

    showTypingIndicator();

    try {
        const requestData = {
            message: message,
            max_new_tokens: domElements.maxTokensInput ? parseInt(domElements.maxTokensInput.value) : 1024,
            temperature: domElements.temperatureInput ? parseFloat(domElements.temperatureInput.value) : 0.7,
            enable_thinking: domElements.enableThinkingInput ? domElements.enableThinkingInput.checked : true
        };

        const response = await fetch(`${CONFIG.API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            hideTypingIndicator();
            addMessage('assistant', data.message, data.thinking);
        } else {
            hideTypingIndicator();
            showError(data.error || '请求失败');
        }

    } catch (error) {
        hideTypingIndicator();
        showError('网络连接失败，请检查后端服务是否运行');
        console.error('API调用失败:', error);
    }
}

/**
 * 添加消息到界面
 */
function addMessage(type, content, thinking = null) {
    messageIdCounter++;
    const message = {
        id: messageIdCounter,
        type: type,
        content: content,
        thinking: thinking,
        timestamp: new Date()
    };

    messages.push(message);
    renderMessage(message);
    scrollToBottom();
}

/**
 * 渲染单条消息
 */
function renderMessage(message) {
    if (!domElements.messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';

    if (message.type === 'user') {
        avatar.innerHTML = '<span style="font-size: 1.5rem;">👤</span>';
    } else {
        avatar.innerHTML = '<img src="/static/icons/t1.svg" alt="AI Assistant" style="width: 100%; height: 100%; object-fit: contain;" />';
    }

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${message.type}`;

    let bubbleHTML = '';

    // 如果是助手消息，使用 Markdown 渲染
    if (message.type === 'assistant') {
        const markdownContent = typeof marked !== 'undefined' ? marked.parse(message.content) : message.content;
        bubbleHTML = `
            <div class="markdown-content">${markdownContent}</div>
            <div class="message-time ${message.type}">${formatTime(message.timestamp)}</div>
        `;
    } else {

        bubbleHTML = `
            ${message.content}
            <div class="message-time ${message.type}">${formatTime(message.timestamp)}</div>
        `;
    }

    if (message.thinking && message.thinking.trim()) {
        const thinkingId = `thinking-${message.id}`;
        bubbleHTML += `
            <div class="thinking-toggle" onclick="toggleThinking('${thinkingId}')">
                💭 查看思维过程
            </div>
            <div id="${thinkingId}" class="thinking-content">
                <div class="thinking-section">${message.thinking}</div>
            </div>
        `;
    }

    bubble.innerHTML = bubbleHTML;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    domElements.messagesContainer.appendChild(messageDiv);
}

/**
 * 切换思维过程显示
 */
function toggleThinking(thinkingId) {
    const thinkingContent = document.getElementById(thinkingId);
    if (thinkingContent) {
        thinkingContent.classList.toggle('expanded');
    }
}

/**
 * 显示打字指示器
 */
function showTypingIndicator() {
    if (!domElements.messagesContainer) return;

    isTyping = true;
    updateSendButtonState();

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="avatar">
            <img src="/static/icons/t1.svg" alt="AI Assistant" style="width: 100%; height: 100%; object-fit: contain;" />
        </div>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    domElements.messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

/**
 * 隐藏打字指示器
 */
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    updateSendButtonState();
}

/**
 * 切换设置面板
 */
function toggleSettings() {
    if (domElements.settingsPanel) {
        domElements.settingsPanel.classList.toggle('open');
    }
}

/**
 * 更新温度显示
 */
function updateTemperatureDisplay() {
    if (domElements.temperatureInput && domElements.temperatureValue) {
        domElements.temperatureValue.textContent = domElements.temperatureInput.value;
    }
}

/**
 * 打开报告生成模态框
 */
function openReportModal() {
    if (!isModelReady) {
        showError('模型还未加载完成，请稍后再试');
        return;
    }
    if (domElements.reportModal) {
        domElements.reportModal.classList.add('active');
    }
    if (domElements.reportTopic) {
        domElements.reportTopic.focus();
    }
}

/**
 * 关闭报告生成模态框
 */
function closeReportModalFunc() {
    if (domElements.reportModal) {
        domElements.reportModal.classList.remove('active');
    }
    resetReportModal();
}

/**
 * 重置报告模态框
 */
function resetReportModal() {
    if (domElements.reportTopic) {
        domElements.reportTopic.value = '';
    }
    if (domElements.reportRequirements) {
        domElements.reportRequirements.value = '';
    }
    if (domElements.reportProgress) {
        domElements.reportProgress.style.display = 'none';
    }
    if (domElements.downloadOptions) {
        domElements.downloadOptions.style.display = 'none';
    }
    if (domElements.progressSections) {
        domElements.progressSections.style.display = 'none';
    }
    if (domElements.startGeneration) {
        domElements.startGeneration.disabled = false;
        domElements.startGeneration.textContent = '开始生成';
    }

    if (domElements.reportProgress) {
        const dynamicElements = domElements.reportProgress.querySelectorAll('.completion-message, .report-preview, .error-message');
        dynamicElements.forEach(element => element.remove());
    }

    if (reportPollingInterval) {
        clearInterval(reportPollingInterval);
        reportPollingInterval = null;
    }
    currentReportId = null;
}

/**
 * 开始报告生成
 */
async function startReportGeneration() {
    if (!domElements.reportTopic || !domElements.reportRequirements) return;

    const topic = domElements.reportTopic.value.trim();
    const requirements = domElements.reportRequirements.value.trim();

    if (!topic) {
        alert('请输入报告主题');
        return;
    }

    if (domElements.startGeneration) {
        domElements.startGeneration.disabled = true;
        domElements.startGeneration.textContent = '生成中...';
    }
    if (domElements.reportProgress) {
        domElements.reportProgress.style.display = 'block';
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE}/report/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                requirements: requirements
            })
        });

        const data = await response.json();

        if (response.ok && data.report_id) {
            currentReportId = data.report_id;
            startPollingReportStatus();
        } else {
            throw new Error(data.error || '开始生成报告失败');
        }

    } catch (error) {
        console.error('报告生成失败:', error);
        showError(`报告生成失败: ${error.message}`);
        if (domElements.startGeneration) {
            domElements.startGeneration.disabled = false;
            domElements.startGeneration.textContent = '开始生成';
        }
        if (domElements.reportProgress) {
            domElements.reportProgress.style.display = 'none';
        }
    }
}

/**
 * 开始轮询报告状态
 */
function startPollingReportStatus() {
    if (reportPollingInterval) {
        clearInterval(reportPollingInterval);
    }

    reportPollingInterval = setInterval(async () => {
        if (!currentReportId) return;

        try {
            const response = await fetch(`${CONFIG.API_BASE}/report/status/${currentReportId}`);
            const data = await response.json();

            if (response.ok) {
                updateReportProgress(data);

                if (data.status === 'completed') {
                    clearInterval(reportPollingInterval);
                    reportPollingInterval = null;
                    showDownloadOptions();
                } else if (data.status === 'error') {
                    clearInterval(reportPollingInterval);
                    reportPollingInterval = null;
                    showError(`报告生成失败: ${data.error}`);
                    if (domElements.startGeneration) {
                        domElements.startGeneration.disabled = false;
                        domElements.startGeneration.textContent = '重新生成';
                    }
                }
            }
        } catch (error) {
            console.error('获取报告状态失败:', error);
        }
    }, CONFIG.POLLING_INTERVAL);
}

/**
 * 更新报告进度
 */
function updateReportProgress(data) {
    const progress = data.progress || 0;

    if (domElements.progressFill) {
        domElements.progressFill.style.width = `${progress}%`;
    }
    if (domElements.progressPercentage) {
        domElements.progressPercentage.textContent = `${progress}%`;
    }

    // 更新状态文本
    let statusText = '准备中...';
    switch (data.status) {
        case 'generating_outline':
            statusText = '正在生成报告大纲...';
            break;
        case 'generating_sections':
            statusText = `正在生成章节内容... (${data.sections_completed}/${data.total_sections})`;
            break;
        case 'completed':
            statusText = '报告生成完成！';
            handleReportCompletion(data);
            break;
        case 'error':
            statusText = `生成失败: ${data.error}`;
            handleReportError(data);
            break;
    }

    if (domElements.progressStatus) {
        domElements.progressStatus.textContent = statusText;
    }

    // 显示章节进度
    if (data.outline && data.outline.sections) {
        showSectionProgress(data.outline.sections, data.sections_completed);
    }
}

/**
 * 显示章节进度
 */
function showSectionProgress(sections, completedCount) {
    if (!domElements.progressSections) return;

    domElements.progressSections.style.display = 'block';
    domElements.progressSections.innerHTML = '<h4 style="margin-bottom: 0.5rem; font-size: 0.875rem;">章节进度:</h4>';

    sections.forEach((section, index) => {
        const isCompleted = index < completedCount;
        const isGenerating = index === completedCount;

        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'section-item';

        const statusClass = isCompleted ? 'completed' : isGenerating ? 'generating' : 'pending';
        const statusSymbol = isCompleted ? '✓' : isGenerating ? '⏳' : '○';

        sectionDiv.innerHTML = `
            <span class="section-status ${statusClass}">${statusSymbol}</span>
            <span>${section.id}. ${section.title}</span>
        `;

        domElements.progressSections.appendChild(sectionDiv);
    });
}

/**
 * 处理报告生成完成
 */
function handleReportCompletion(data) {
    if (reportPollingInterval) {
        clearInterval(reportPollingInterval);
        reportPollingInterval = null;
    }

    if (domElements.startGeneration) {
        domElements.startGeneration.textContent = '生成完成';
        domElements.startGeneration.disabled = true;
    }

    showCompletionMessage(data);

    showDownloadOptions();

    showReportPreview(data);

    addCompletionMessageToChat(data);
}

/**
 * 显示完成消息
 */
function showCompletionMessage(data) {
    if (!domElements.reportProgress) return;

    const completionDiv = document.createElement('div');
    completionDiv.className = 'completion-message';
    completionDiv.innerHTML = `
        <div class="completion-icon">✅</div>
        <div class="completion-text">
            <h4>报告生成完成！</h4>
            <p>您的报告《${data.outline?.title || '经济学报告'}》已经生成完成，包含 ${data.total_sections} 个章节。</p>
            <p class="completion-time">完成时间：${new Date().toLocaleString('zh-CN')}</p>
        </div>
    `;

    domElements.reportProgress.appendChild(completionDiv);
}

/**
 * 显示报告预览
 */
function showReportPreview(data) {
    if (!domElements.reportProgress) return;

    const previewDiv = document.createElement('div');
    previewDiv.className = 'report-preview';
    previewDiv.innerHTML = `
        <div class="preview-header">
            <h4>报告预览</h4>
            <button class="preview-toggle" onclick="togglePreview()">展开预览</button>
        </div>
        <div class="preview-content" id="previewContent" style="display: none;">
            <div class="preview-section">
                <h5>标题</h5>
                <p>${data.outline?.title || ''}</p>
            </div>
            <div class="preview-section">
                <h5>摘要</h5>
                <p>${data.outline?.abstract || ''}</p>
            </div>
            <div class="preview-section">
                <h5>章节目录</h5>
                <ul class="chapter-list">
                    ${data.outline?.sections?.map(section =>
                        `<li>${section.id}. ${section.title}</li>`
                    ).join('') || ''}
                </ul>
            </div>
        </div>
    `;

    domElements.reportProgress.appendChild(previewDiv);
}

/**
 * 切换预览显示
 */
function togglePreview() {
    const previewContent = document.getElementById('previewContent');
    const toggleBtn = document.querySelector('.preview-toggle');

    if (previewContent && toggleBtn) {
        if (previewContent.style.display === 'none') {
            previewContent.style.display = 'block';
            toggleBtn.textContent = '收起预览';
        } else {
            previewContent.style.display = 'none';
            toggleBtn.textContent = '展开预览';
        }
    }
}

/**
 * 显示下载选项
 */
function showDownloadOptions() {
    if (!domElements.downloadOptions || !currentReportId) return;

    domElements.downloadOptions.style.display = 'block';
    domElements.downloadOptions.innerHTML = `
        <div class="download-header">
            <h4>下载选项</h4>
        </div>
        <div class="download-buttons">
            <a href="${CONFIG.API_BASE}/report/download/${currentReportId}/docx"
               class="download-btn primary"
               id="downloadWord"
               download="report_${currentReportId}.docx">
                📄 下载Word文档
            </a>
            <button class="download-btn secondary" onclick="generateNewReport()">
                🔄 生成新报告
            </button>
        </div>
        <div class="download-info">
            <p class="download-note">💡 建议下载后使用Microsoft Word或WPS打开文档以获得最佳阅读体验</p>
        </div>
    `;
}

/**
 * 向聊天区域添加完成消息
 */
function addCompletionMessageToChat(data) {
    const completionMessage = `
报告生成完成！📊

📋 **报告标题**: ${data.outline?.title || '经济学报告'}
📝 **章节数量**: ${data.total_sections} 个章节
⏰ **生成时间**: ${new Date().toLocaleString('zh-CN')}
📄 **文档格式**: Word文档 (.docx)

您可以在报告生成窗口中下载完整的报告文档。如需重新生成或修改要求，请点击"生成新报告"按钮。
    `;

    addMessage('assistant', completionMessage);
}

/**
 * 处理报告生成错误
 */
function handleReportError(data) {

    if (reportPollingInterval) {
        clearInterval(reportPollingInterval);
        reportPollingInterval = null;
    }

    if (domElements.startGeneration) {
        domElements.startGeneration.disabled = false;
        domElements.startGeneration.textContent = '重新生成';
    }

    if (domElements.reportProgress) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="error-icon">❌</div>
            <div class="error-content">
                <h4>报告生成失败</h4>
                <p>错误原因：${data.error}</p>
                <div class="error-actions">
                    <button class="btn btn-primary" onclick="retryReportGeneration()">重试生成</button>
                    <button class="btn btn-secondary" onclick="resetReportModal()">重新开始</button>
                </div>
            </div>
        `;

        domElements.reportProgress.appendChild(errorDiv);
    }
}

/**
 * 重试报告生成
 */
function retryReportGeneration() {
    resetReportModal();
    startReportGeneration();
}

/**
 * 生成新报告
 */
function generateNewReport() {
    resetReportModal();
    if (domElements.reportTopic) {
        domElements.reportTopic.focus();
    }
}

/**
 * 打开报告列表模态框
 */
function openReportListModal() {
    if (domElements.reportListModal) {
        domElements.reportListModal.classList.add('active');
    }
    loadReportList();
}

/**
 * 关闭报告列表模态框
 */
function closeReportListModalFunc() {
    if (domElements.reportListModal) {
        domElements.reportListModal.classList.remove('active');
    }
}

/**
 * 从报告列表打开报告模态框
 */
function openReportModalFromList() {
    closeReportListModalFunc();
    openReportModal();
}

/**
 * 加载报告列表
 */
async function loadReportList() {
    try {
        // 显示加载状态
        if (domElements.reportListLoading) {
            domElements.reportListLoading.style.display = 'block';
        }
        if (domElements.reportListContainer) {
            domElements.reportListContainer.style.display = 'none';
        }
        if (domElements.reportListEmpty) {
            domElements.reportListEmpty.style.display = 'none';
        }

        const response = await fetch(`${CONFIG.API_BASE}/report/list`);
        const data = await response.json();

        if (response.ok) {
            hideReportListLoading();

            if (data.reports && data.reports.length > 0) {
                displayReportList(data.reports);
            } else {
                showEmptyReportList();
            }
        } else {
            throw new Error(data.error || '获取报告列表失败');
        }

    } catch (error) {
        console.error('加载报告列表失败:', error);
        hideReportListLoading();
        showReportListError(error.message);
    }
}

/**
 * 隐藏报告列表加载状态
 */
function hideReportListLoading() {
    if (domElements.reportListLoading) {
        domElements.reportListLoading.style.display = 'none';
    }
}

/**
 * 显示空报告列表
 */
function showEmptyReportList() {
    if (domElements.reportListEmpty) {
        domElements.reportListEmpty.style.display = 'block';
    }
    if (domElements.reportListContainer) {
        domElements.reportListContainer.style.display = 'none';
    }
}

/**
 * 显示报告列表错误
 */
function showReportListError(errorMsg) {
    if (!domElements.reportListContainer) return;

    domElements.reportListContainer.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #dc2626;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">❌</div>
            <h3 style="margin-bottom: 0.5rem;">加载失败</h3>
            <p style="margin-bottom: 1rem;">${errorMsg}</p>
            <button class="btn btn-primary" onclick="loadReportList()">重新加载</button>
        </div>
    `;
    domElements.reportListContainer.style.display = 'block';
}

/**
 * 显示报告列表
 */
function displayReportList(reports) {
    if (!domElements.reportListContainer) return;

    const completedReports = reports.filter(r => r.status === 'completed');
    const otherReports = reports.filter(r => r.status !== 'completed');

    let html = `
        <div class="report-list-header">
            <h3 class="report-list-title">我的报告</h3>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span class="report-list-stats">共 ${reports.length} 份报告</span>
                <button class="refresh-btn" onclick="loadReportList()" title="刷新列表">
                    ↻
                </button>
            </div>
        </div>
    `;


    if (completedReports.length > 0) {
        html += '<div style="margin-bottom: 1.5rem;">';
        completedReports.forEach(report => {
            html += renderReportItem(report);
        });
        html += '</div>';
    }


    if (otherReports.length > 0) {
        if (completedReports.length > 0) {
            html += '<div style="border-top: 1px solid #e5e7eb; padding-top: 1.5rem; margin-bottom: 1.5rem;"></div>';
        }
        otherReports.forEach(report => {
            html += renderReportItem(report);
        });
    }

    html += `
        <div style="text-align: center; padding: 1.5rem; border-top: 1px solid #e5e7eb; margin-top: 1.5rem;">
            <button class="btn btn-primary" onclick="openReportModalFromList()">
                📊 生成新报告
            </button>
        </div>
    `;

    domElements.reportListContainer.innerHTML = html;
    domElements.reportListContainer.style.display = 'block';
}

/**
 * 渲染报告列表项
 */
function renderReportItem(report) {
    const createdDate = new Date(report.created_at).toLocaleString('zh-CN');
    const completedDate = report.completed_at ? new Date(report.completed_at).toLocaleString('zh-CN') : '';

    let statusClass = 'completed';
    let statusText = '已完成';
    let statusIcon = '✅';

    if (report.status === 'generating' || report.status === 'generating_outline' || report.status === 'generating_sections') {
        statusClass = 'generating';
        statusText = '生成中';
        statusIcon = '⏳';
    } else if (report.status === 'error') {
        statusClass = 'error';
        statusText = '生成失败';
        statusIcon = '❌';
    }

    let actionsHtml = '';
    if (report.status === 'completed') {
        actionsHtml = `
            <a href="${CONFIG.API_BASE}/report/download/${report.id}/docx"
               class="report-action-btn primary"
               download="report_${report.id}.docx">
                📄 下载Word
            </a>
            <button class="report-action-btn secondary" onclick="copyReportInfo('${report.id}', '${report.topic}')">
                📋 复制信息
            </button>
        `;
    } else if (report.status === 'error') {
        actionsHtml = `
            <button class="report-action-btn secondary" onclick="retryFailedReport('${report.id}')">
                🔄 重新生成
            </button>
        `;
    } else {
        actionsHtml = `
            <div class="report-progress-mini">
                <div class="progress-bar-mini">
                    <div class="progress-fill-mini" style="width: ${report.progress}%"></div>
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">
                    进度: ${report.progress}%
                </div>
            </div>
        `;
    }

    return `
        <div class="report-list-item">
            <div class="report-item-header">
                <h4 class="report-item-title">${report.topic || '未命名报告'}</h4>
                <span class="report-item-status ${statusClass}">
                    ${statusIcon} ${statusText}
                </span>
            </div>
            <div class="report-item-meta">
                <div class="report-meta-item">
                    <span class="report-meta-icon">📅</span>
                    创建时间: ${createdDate}
                </div>
                ${completedDate ? `
                <div class="report-meta-item">
                    <span class="report-meta-icon">✅</span>
                    完成时间: ${completedDate}
                </div>` : ''}
                ${report.download_count > 0 ? `
                <div class="report-meta-item">
                    <span class="report-meta-icon">📊</span>
                    下载次数: ${report.download_count}
                </div>` : ''}
            </div>
            <div class="report-item-actions">
                ${actionsHtml}
            </div>
        </div>
    `;
}

/**
 * 复制报告信息
 */
function copyReportInfo(reportId, topic) {
    const textToCopy = `报告: ${topic}\n报告ID: ${reportId}\n生成时间: ${new Date().toLocaleString('zh-CN')}`;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const toast = document.createElement('div');
        toast.className = 'download-toast';
        toast.innerHTML = `
            <div class="toast-content">
                📋 报告信息已复制到剪贴板
            </div>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }).catch(() => {
        alert('复制失败，请手动复制报告信息');
    });
}

/**
 * 重试失败的报告
 */
function retryFailedReport(reportId) {
    alert('该功能正在开发中，请重新创建报告');
}


window.selectQuickOption = selectQuickOption;
window.toggleThinking = toggleThinking;
window.togglePreview = togglePreview;
window.generateNewReport = generateNewReport;
window.retryReportGeneration = retryReportGeneration;
window.openReportModalFromList = openReportModalFromList;
window.copyReportInfo = copyReportInfo;
window.retryFailedReport = retryFailedReport;
window.loadReportList = loadReportList;

document.addEventListener('DOMContentLoaded', initializeApp);