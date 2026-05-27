const USER_ID = getOrCreateUserId();

function getOrCreateUserId() {
    let id = localStorage.getItem('paragi_user_id');
    if (!id) {
        id = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('paragi_user_id', id);
    }
    return id;
}

document.addEventListener('DOMContentLoaded', () => {
    loadHealth();
    loadHistory();

    const input = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');

    sendBtn.addEventListener('click', () => sendQuery(input.value));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuery(input.value);
    });

    document.getElementById('close-graph').addEventListener('click', () => {
        document.getElementById('graph-container').classList.add('hidden');
    });
});

async function sendQuery(text) {
    if (!text.trim()) return;

    const input = document.getElementById('query-input');
    input.value = '';
    appendMessage('user', text);

    const loadingMsg = appendMessage('paragi', 'Thinking...');

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, user_id: USER_ID })
        });
        const data = await response.json();

        loadingMsg.remove();
        renderParagiResponse(data);
        loadHistory();
        loadHealth();
    } catch (e) {
        loadingMsg.innerText = 'Error: ' + e.message;
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerText = text;
    document.getElementById('messages').appendChild(div);
    div.scrollIntoView();
    return div;
}

function renderParagiResponse(data) {
    const div = document.createElement('div');
    div.className = 'message paragi';

    const textSpan = document.createElement('span');
    textSpan.innerText = data.answer;
    div.appendChild(textSpan);

    const confClass = data.confidence > 0.8 ? 'conf-high' : (data.confidence > 0.5 ? 'conf-med' : 'conf-low');
    const badge = document.createElement('span');
    badge.className = 'confidence-badge ' + confClass;
    badge.innerText = Math.round(data.confidence * 100) + '%';
    div.appendChild(badge);

    if (data.path && data.path.length > 0) {
        const pathDiv = document.createElement('div');
        pathDiv.className = 'path-viz';
        data.path.forEach((node, i) => {
            const nodeSpan = document.createElement('span');
            nodeSpan.className = 'path-node';
            nodeSpan.innerText = node;
            nodeSpan.style.cursor = 'pointer';
            nodeSpan.onclick = () => showGraph(node);
            pathDiv.appendChild(nodeSpan);
            if (i < data.path.length - 1) {
                const arrow = document.createElement('span');
                arrow.innerText = ' → ';
                pathDiv.appendChild(arrow);
            }
        });
        div.appendChild(pathDiv);
    }

    document.getElementById('messages').appendChild(div);
    div.scrollIntoView();
}

async function loadHistory() {
    const resp = await fetch(`/history?user_id=${USER_ID}`);
    const data = await resp.json();
    const list = document.getElementById('history-list');
    list.innerHTML = '';
    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.innerText = item.raw_text;
        div.onclick = () => sendQuery(item.raw_text);
        list.appendChild(div);
    });
}

async function loadHealth() {
    const resp = await fetch('/health');
    const data = await resp.json();
    document.getElementById('node-count').innerText = data.nodes;
    document.getElementById('edge-count').innerText = data.edges;
}

async function showGraph(nodeLabel) {
    const container = document.getElementById('graph-container');
    container.classList.remove('hidden');
    document.getElementById('graph-title').innerText = 'Explore: ' + nodeLabel;

    const resp = await fetch(`/graph/explore?node=${nodeLabel}&depth=2`);
    const data = await resp.json();
    renderD3(data);
}

function renderD3(data) {
    const width = document.getElementById('d3-canvas').clientWidth;
    const height = document.getElementById('d3-canvas').clientHeight;

    d3.select("#d3-canvas").selectAll("*").remove();

    const svg = d3.select("#d3-canvas")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.edges).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-200))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
        .selectAll("line")
        .data(data.edges)
        .enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", d => Math.sqrt(d.strength * 5));

    const node = svg.append("g")
        .selectAll("circle")
        .data(data.nodes)
        .enter().append("circle")
        .attr("r", 8)
        .attr("fill", d => d.label.includes('expansion') ? '#e74c3c' : '#3498db')
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    const label = svg.append("g")
        .selectAll("text")
        .data(data.nodes)
        .enter().append("text")
        .text(d => d.label)
        .attr("font-size", "12px")
        .attr("dx", 12)
        .attr("dy", 4)
        .attr("fill", "#888");

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    });

    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
}
