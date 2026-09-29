const API_BASE = '';

let currentUser = null;
let currentDiscussion = null;
let currentSummary = null;

const state = {
    discussions: [],
    transcripts: [],
    summaries: [],
    worldSettings: [],
    conceptArts: []
};

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAuth();
    loadDiscussions();
});

function initEventListeners() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    document.getElementById('loginBtn').addEventListener('click', showAuthModal);
    document.getElementById('toggleAuth').addEventListener('click', toggleAuthMode);
    document.getElementById('authForm').addEventListener('submit', handleAuth);

    document.getElementById('createDiscussionBtn').addEventListener('click', () => {
        document.getElementById('createDiscussionModal').classList.remove('hidden');
    });
    document.getElementById('cancelCreateBtn').addEventListener('click', () => {
        document.getElementById('createDiscussionModal').classList.add('hidden');
    });
    document.getElementById('confirmCreateBtn').addEventListener('click', createDiscussion);

    document.getElementById('uploadAudioBtn').addEventListener('click', () => openUploadModal('audio'));
    document.getElementById('uploadArtBtn').addEventListener('click', () => openUploadModal('image'));
    document.getElementById('cancelUploadBtn').addEventListener('click', closeUploadModal);
    document.getElementById('confirmUploadBtn').addEventListener('click', handleUpload);

    document.getElementById('generateSummaryBtn').addEventListener('click', generateSummary);
    document.getElementById('downloadSummaryBtn').addEventListener('click', downloadSummary);
    document.getElementById('sendEmailBtn').addEventListener('click', () => {
        document.getElementById('emailModal').classList.remove('hidden');
    });
    document.getElementById('cancelEmailBtn').addEventListener('click', () => {
        document.getElementById('emailModal').classList.add('hidden');
    });
    document.getElementById('confirmEmailBtn').addEventListener('click', sendEmail);

    document.getElementById('mindmapDiscussion').addEventListener('change', (e) => {
        if (e.target.value) {
            currentDiscussion = parseInt(e.target.value);
            loadMindMap(currentDiscussion);
        }
    });

    document.getElementById('galleryDiscussion').addEventListener('change', (e) => {
        if (e.target.value) {
            currentDiscussion = parseInt(e.target.value);
            loadConceptArts(currentDiscussion);
        }
    });

    document.getElementById('transcriptDiscussion').addEventListener('change', (e) => {
        if (e.target.value) {
            currentDiscussion = parseInt(e.target.value);
            loadTranscripts(currentDiscussion);
        }
    });

    document.getElementById('summaryDiscussion').addEventListener('change', (e) => {
        if (e.target.value) {
            currentDiscussion = parseInt(e.target.value);
            loadSummaries(currentDiscussion);
        }
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
}

function switchView(viewName) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.getElementById(`${viewName}View`).classList.add('active');

    if (viewName === 'mindmap' || viewName === 'gallery' || viewName === 'transcripts' || viewName === 'summaries') {
        populateDiscussionSelect(`${viewName}Discussion`);
    }
}

async function apiRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (currentUser && currentUser.access_token) {
        headers['Authorization'] = `Bearer ${currentUser.access_token}`;
    }

    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        currentUser = null;
        updateAuthUI();
        showToast('请先登录', 'error');
        return null;
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        showToast(error.detail || '请求失败', 'error');
        return null;
    }

    return response.json();
}

function checkAuth() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateAuthUI();
    }
}

function showAuthModal() {
    document.getElementById('authModal').classList.remove('hidden');
}

function toggleAuthMode(e) {
    e.preventDefault();
    const nameInput = document.getElementById('name');
    const authTitle = document.getElementById('authTitle');
    const submitBtn = document.querySelector('#authForm button');
    const toggleText = document.getElementById('toggleAuth');

    if (nameInput.classList.contains('hidden')) {
        nameInput.classList.remove('hidden');
        authTitle.textContent = '注册';
        submitBtn.textContent = '注册';
        toggleText.innerHTML = '已有账号？<a href="#">立即登录</a>';
    } else {
        nameInput.classList.add('hidden');
        authTitle.textContent = '登录';
        submitBtn.textContent = '登录';
        toggleText.innerHTML = '没有账号？<a href="#">立即注册</a>';
    }
}

async function handleAuth(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const name = document.getElementById('name').value;
    const isRegister = !document.getElementById('name').classList.contains('hidden');

    if (isRegister) {
        const result = await apiRequest('/register', {
            method: 'POST',
            body: JSON.stringify({ email, name, password })
        });
        if (result) {
            showToast('注册成功，请登录', 'success');
            toggleAuthMode(e);
        }
    } else {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/token`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            currentUser = { email, access_token: result.access_token };
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateAuthUI();
            document.getElementById('authModal').classList.add('hidden');
            showToast('登录成功', 'success');
            loadDiscussions();
        } else {
            showToast('登录失败', 'error');
        }
    }
}

function updateAuthUI() {
    const loginBtn = document.getElementById('loginBtn');
    if (currentUser) {
        loginBtn.textContent = `👤 ${currentUser.email}`;
        loginBtn.onclick = logout;
    } else {
        loginBtn.textContent = '登录';
        loginBtn.onclick = showAuthModal;
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    updateAuthUI();
    showToast('已退出登录', 'success');
}

async function loadDiscussions() {
    if (!currentUser) return;

    const discussions = await apiRequest('/api/brainstorm/discussions');
    if (discussions) {
        state.discussions = discussions;
        renderDiscussions();
        populateAllDiscussionSelects();
    }
}

function renderDiscussions() {
    const container = document.getElementById('discussionsList');
    if (state.discussions.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: #64748b;">
                <p style="font-size: 1.2rem; margin-bottom: 1rem;">还没有创建项目</p>
                <p>点击上方「新建头脑风暴」按钮开始创作</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.discussions.map(d => `
        <div class="discussion-card" onclick="selectDiscussion(${d.id})">
            <h3>${d.title}</h3>
            <p>${d.description || '暂无描述'}</p>
            <div class="card-meta">
                <span>📅 ${new Date(d.created_at).toLocaleDateString()}</span>
            </div>
        </div>
    `).join('');
}

function selectDiscussion(id) {
    currentDiscussion = id;
    switchView('mindmap');
    document.getElementById('mindmapDiscussion').value = id;
    loadMindMap(id);
}

async function createDiscussion() {
    const title = document.getElementById('discussionTitle').value;
    const description = document.getElementById('discussionDesc').value;

    if (!title) {
        showToast('请输入项目名称', 'error');
        return;
    }

    const result = await apiRequest('/api/brainstorm/discussions', {
        method: 'POST',
        body: JSON.stringify({ title, description })
    });

    if (result) {
        document.getElementById('createDiscussionModal').classList.add('hidden');
        document.getElementById('discussionTitle').value = '';
        document.getElementById('discussionDesc').value = '';
        showToast('项目创建成功', 'success');
        loadDiscussions();
    }
}

function populateAllDiscussionSelects() {
    ['mindmapDiscussion', 'galleryDiscussion', 'transcriptDiscussion', 'summaryDiscussion'].forEach(id => {
        populateDiscussionSelect(id);
    });
}

function populateDiscussionSelect(selectId) {
    const select = document.getElementById(selectId);
    const currentValue = select.value;
    select.innerHTML = '<option value="">选择项目...</option>' +
        state.discussions.map(d => `<option value="${d.id}">${d.title}</option>`).join('');
    select.value = currentValue;
}

let uploadMode = 'audio';

function openUploadModal(mode) {
    if (!currentDiscussion) {
        showToast('请先选择一个项目', 'error');
        return;
    }

    uploadMode = mode;
    const modal = document.getElementById('uploadModal');
    const title = document.getElementById('uploadModalTitle');
    const fileInput = document.getElementById('fileInput');
    const artTitle = document.getElementById('artTitle');
    const artCategory = document.getElementById('artCategory');
    const artDescription = document.getElementById('artDescription');

    if (mode === 'audio') {
        title.textContent = '上传讨论音频';
        fileInput.accept = 'audio/*';
        artTitle.classList.add('hidden');
        artCategory.classList.add('hidden');
        artDescription.classList.add('hidden');
    } else {
        title.textContent = '上传设定图';
        fileInput.accept = 'image/*';
        artTitle.classList.remove('hidden');
        artCategory.classList.remove('hidden');
        artDescription.classList.remove('hidden');
    }

    modal.classList.remove('hidden');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('fileInput').value = '';
    document.getElementById('artTitle').value = '';
    document.getElementById('artDescription').value = '';
}

async function handleUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        showToast('请选择文件', 'error');
        return;
    }

    if (uploadMode === 'audio') {
        await uploadAudio(file);
    } else {
        await uploadConceptArt(file);
    }
}

async function uploadAudio(file) {
    const formData = new FormData();
    formData.append('file', file);

    const result = await apiRequest(`/api/brainstorm/discussions/${currentDiscussion}/upload-audio`, {
        method: 'POST',
        body: formData,
        headers: {}
    });

    if (result) {
        closeUploadModal();
        showToast('音频上传成功，开始处理...', 'success');

        await apiRequest('/api/audio/process', {
            method: 'POST',
            body: JSON.stringify({
                audio_file_id: result.id,
                discussion_id: currentDiscussion
            })
        });

        loadTranscripts(currentDiscussion);
    }
}

async function uploadConceptArt(file) {
    const title = document.getElementById('artTitle').value;
    const category = document.getElementById('artCategory').value;
    const description = document.getElementById('artDescription').value;

    if (!title) {
        showToast('请输入设定图标题', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
        const result = await apiRequest('/api/brainstorm/concept-arts', {
            method: 'POST',
            body: JSON.stringify({
                discussion_id: currentDiscussion,
                title,
                category,
                description,
                image_url: e.target.result
            })
        });

        if (result) {
            closeUploadModal();
            showToast('设定图上传成功', 'success');
            loadConceptArts(currentDiscussion);
        }
    };
    reader.readAsDataURL(file);
}

async function loadTranscripts(discussionId) {
    const transcripts = await apiRequest(`/api/audio/transcripts/${discussionId}`);
    if (transcripts) {
        state.transcripts = transcripts;
        renderTranscripts();
    }
}

function renderTranscripts() {
    const container = document.getElementById('transcriptsList');
    if (state.transcripts.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #64748b;">
                <p>暂无转写记录</p>
                <p style="margin-top: 0.5rem;">上传讨论音频后会自动转写</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.transcripts.map(t => `
        <div class="transcript-item" onclick="loadTranscriptDetail(${t.id})">
            <div>
                <h4>转写记录 #${t.id}</h4>
                <p class="meta">${new Date(t.created_at).toLocaleString()}</p>
            </div>
            <span class="transcript-status ${t.full_text === 'Processing...' ? 'status-processing' : 'status-completed'}">
                ${t.full_text === 'Processing...' ? '处理中' : '已完成'}
            </span>
        </div>
    `).join('');
}

async function loadTranscriptDetail(transcriptId) {
    const segments = await apiRequest(`/api/audio/transcripts/${transcriptId}/segments`);
    if (segments) {
        document.getElementById('transcriptDetail').classList.remove('hidden');
        document.getElementById('transcriptTitle').textContent = `转写记录 #${transcriptId}`;

        const container = document.getElementById('transcriptSegments');
        container.innerHTML = segments.map(s => `
            <div class="segment">
                <div class="speaker">${s.speaker_label}</div>
                <div class="time">${formatTime(s.start_time)} - ${formatTime(s.end_time)}</div>
                <div class="text">${s.text}</div>
            </div>
        `).join('');
    }
}

function formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

async function loadSummaries(discussionId) {
    const summaries = await apiRequest(`/api/summary/${discussionId}`);
    if (summaries) {
        state.summaries = summaries;
        renderSummaries();
    }
}

function renderSummaries() {
    const container = document.getElementById('summariesList');
    if (state.summaries.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #64748b;">
                <p>暂无摘要文档</p>
                <p style="margin-top: 0.5rem;">点击「生成AI摘要」按钮创建</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.summaries.map(s => `
        <div class="summary-item" onclick="loadSummaryDetail(${s.id})">
            <h4>摘要文档 #${s.id}</h4>
            <p class="date">${new Date(s.created_at).toLocaleString()}</p>
        </div>
    `).join('');
}

function loadSummaryDetail(summaryId) {
    const summary = state.summaries.find(s => s.id === summaryId);
    if (summary) {
        currentSummary = summary;
        document.getElementById('summaryPreview').classList.remove('hidden');
        document.getElementById('summaryTitle').textContent = `摘要文档 #${summaryId}`;
        document.getElementById('summaryContent').innerHTML = markdownToHtml(summary.markdown_content || summary.content);
    }
}

async function generateSummary() {
    if (!currentDiscussion) {
        showToast('请先选择一个项目', 'error');
        return;
    }

    const result = await apiRequest('/api/summary/generate', {
        method: 'POST',
        body: JSON.stringify({ discussion_id: currentDiscussion })
    });

    if (result) {
        showToast('正在生成摘要，请稍候...', 'success');
        setTimeout(() => loadSummaries(currentDiscussion), 3000);
    }
}

async function downloadSummary() {
    if (!currentSummary) return;
    window.open(`${API_BASE}/api/summary/download/${currentSummary.id}`, '_blank');
}

async function sendEmail() {
    if (!currentSummary) return;

    const subject = document.getElementById('emailSubject').value;
    const recipientsText = document.getElementById('emailRecipients').value;
    const recipients = recipientsText.split(',').map(e => e.trim()).filter(e => e);

    if (recipients.length === 0) {
        showToast('请输入收件人邮箱', 'error');
        return;
    }

    const result = await apiRequest('/api/email/send-summary', {
        method: 'POST',
        body: JSON.stringify({
            summary_id: currentSummary.id,
            recipients,
            subject
        })
    });

    if (result && result.status === 'success') {
        document.getElementById('emailModal').classList.add('hidden');
        document.getElementById('emailSubject').value = '';
        document.getElementById('emailRecipients').value = '';
        showToast('邮件发送成功', 'success');
    }
}

function markdownToHtml(markdown) {
    return markdown
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        .replace(/\n/gim, '<br>');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => toast.classList.add('hidden'), 3000);
}
