let mindmapData = null;
let svg = null;
let g = null;
let simulation = null;

const categoryColors = {
    '角色': '#ef4444',
    '物理规则': '#f59e0b',
    '科技': '#10b981',
    '社会': '#3b82f6',
    '地理': '#8b5cf6',
    '历史': '#ec4899',
    '其他': '#6b7280'
};

async function loadMindMap(discussionId) {
    const settings = await apiRequest(`/api/brainstorm/discussions/${discussionId}/world-settings`);
    if (settings) {
        state.worldSettings = settings;
        renderMindMap(settings);
    } else {
        renderDemoMindMap();
    }
}

function renderDemoMindMap() {
    const demoData = {
        nodes: [
            { id: 'root', name: '世界观核心', category: 'root', fx: 0, fy: 0 },
            { id: '1', name: '量子意识上传', category: '科技', description: '将人类意识数字化转移到量子计算机中', owner: '张工' },
            { id: '2', name: '戴森球文明', category: '社会', description: '围绕恒星建造的能量采集结构', owner: '李科' },
            { id: '3', name: '时空折叠理论', category: '物理规则', description: '通过弯曲时空实现超光速旅行', owner: '王物' },
            { id: '4', name: 'AI执政官', category: '社会', description: '管理人类社会的人工智能系统', owner: '李科' },
            { id: '5', name: '基因飞升者', category: '角色', description: '通过基因改造获得超能力的人类', owner: '陈生' },
            { id: '6', name: '暗能量引擎', category: '科技', description: '利用暗能量作为动力源的引擎', owner: '张工' },
            { id: '7', name: '星际联邦', category: '社会', description: '多个星系文明组成的联邦政府', owner: '赵社' },
            { id: '8', name: '虚拟宇宙', category: '科技', description: '完全沉浸式的虚拟世界', owner: '张工' }
        ],
        links: [
            { source: 'root', target: '1' },
            { source: 'root', target: '2' },
            { source: 'root', target: '3' },
            { source: 'root', target: '4' },
            { source: 'root', target: '5' },
            { source: '1', target: '6' },
            { source: '2', target: '7' },
            { source: '6', target: '8' }
        ]
    };

    drawMindMap(demoData);
}

function renderMindMap(settings) {
    if (settings.length === 0) {
        renderDemoMindMap();
        showToast('暂无设定数据，显示示例思维导图', 'success');
        return;
    }

    const nodes = [{ id: 'root', name: '世界观核心', category: 'root', fx: 0, fy: 0 }];
    const links = [];

    const categories = {};
    settings.forEach(s => {
        if (!categories[s.category]) {
            categories[s.category] = [];
        }
        categories[s.category].push(s);
    });

    Object.keys(categories).forEach((cat, catIndex) => {
        const catId = `cat_${cat}`;
        nodes.push({ id: catId, name: cat, category: cat });
        links.push({ source: 'root', target: catId });

        categories[cat].forEach((setting, setIndex) => {
            const setId = `set_${catIndex}_${setIndex}`;
            nodes.push({
                id: setId,
                name: setting.key,
                category: setting.category,
                description: setting.value,
                owner: setting.owner_name
            });
            links.push({ source: catId, target: setId });
        });
    });

    mindmapData = { nodes, links };
    drawMindMap(mindmapData);
}

function drawMindMap(data) {
    const container = document.getElementById('mindmapContainer');
    const width = container.clientWidth - 64;
    const height = 600;

    d3.select('#mindmapSvg').selectAll('*').remove();

    svg = d3.select('#mindmapSvg')
        .attr('viewBox', [-width / 2, -height / 2, width, height])
        .attr('width', width)
        .attr('height', height);

    const defs = svg.append('defs');
    defs.append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .append('path')
        .attr('d', 'M 0,-5 L 10,0 L 0,5')
        .attr('fill', 'rgba(99, 102, 241, 0.5)');

    g = svg.append('g');

    svg.call(d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        }));

    simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(0, 0))
        .force('collision', d3.forceCollide().radius(50));

    const link = g.append('g')
        .selectAll('line')
        .data(data.links)
        .join('line')
        .attr('class', 'link')
        .attr('marker-end', 'url(#arrowhead)');

    const node = g.append('g')
        .selectAll('g')
        .data(data.nodes)
        .join('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('circle')
        .attr('r', d => d.id === 'root' ? 35 : 25)
        .attr('fill', d => {
            if (d.id === 'root') return 'url(#rootGradient)';
            return categoryColors[d.category] || '#667eea';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('filter', 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3))');

    const gradient = defs.append('radialGradient')
        .attr('id', 'rootGradient')
        .attr('cx', '50%')
        .attr('cy', '50%')
        .attr('r', '50%');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#764ba2');
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#667eea');

    node.append('text')
        .text(d => d.name)
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.id === 'root' ? -45 : -35)
        .style('font-size', d => d.id === 'root' ? '14px' : '11px')
        .style('font-weight', d => d.id === 'root' ? 'bold' : 'normal');

    node.on('click', (event, d) => {
        event.stopPropagation();
        showNodeDetail(d);
    });

    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    if (d.id !== 'root') {
        d.fx = null;
        d.fy = null;
    }
}

function showNodeDetail(node) {
    const detailPanel = document.getElementById('nodeDetail');
    document.getElementById('nodeTitle').textContent = node.name;
    document.getElementById('nodeDescription').textContent = node.description || '该节点暂无详细描述';
    document.getElementById('nodeOwner').textContent = node.owner || '未指定';
    detailPanel.classList.remove('hidden');
    detailPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

window.addEventListener('resize', () => {
    if (mindmapData) {
        drawMindMap(mindmapData);
    }
});
