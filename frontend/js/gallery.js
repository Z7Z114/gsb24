async function loadConceptArts(discussionId) {
    const arts = await apiRequest(`/api/brainstorm/discussions/${discussionId}/concept-arts`);
    if (arts) {
        state.conceptArts = arts;
        renderGallery();
    }
}

function renderGallery() {
    const container = document.getElementById('galleryGrid');
    if (state.conceptArts.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: #64748b;">
                <p>暂无设定图</p>
                <p style="margin-top: 0.5rem;">点击「上传设定图」添加</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.conceptArts.map(art => `
        <div class="gallery-item">
            <img src="${art.image_url}" alt="${art.title}" class="gallery-image" 
                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 400 200%22><rect fill=%22%23667eea%22 width=%22400%22 height=%22200%22/><text fill=%22white%22 font-family=%22Arial%22 font-size=%2224%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>${art.title}</text></svg>'">
            <div class="gallery-info">
                <span class="gallery-category">${art.category}</span>
                <h4>${art.title}</h4>
                <p>${art.description || '暂无描述'}</p>
            </div>
        </div>
    `).join('');
}
