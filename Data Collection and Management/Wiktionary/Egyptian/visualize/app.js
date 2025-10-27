// Egyptian Lemma Network Visualizer
let networks = [];
let currentNetwork = null;
let simulation = null;

// Build Wiktionary URL for a node
function getWiktionaryUrl(node, network) {
    // Map language codes to Wiktionary language sections
    const langMap = {
        'egy': 'Egyptian',
        'dem': 'Demotic',
        'egx-dem': 'Demotic',
        'cop': 'Coptic',
        'cop-boh': 'Coptic',
        'cop-sah': 'Coptic',
        'cop-old': 'Coptic',
        'cop-akh': 'Coptic',
        'cop-fay': 'Coptic',
        'cop-lyc': 'Coptic',
        'cop-her': 'Coptic',
        'cop-kkk': 'Coptic',
        'cop-oxy': 'Coptic',
        'cop-ply': 'Coptic',
        'cop-ppp': 'Coptic'
    };
    
    const wiktLang = langMap[node.language] || node.language;
    const form = encodeURIComponent(node.form);
    
    return `https://en.wiktionary.org/wiki/${form}#${wiktLang}`;
}

// Try to open Wiktionary page, fallback to parent if it doesn't exist
async function openWiktionaryPage(node, network) {
    const url = getWiktionaryUrl(node, network);
    
    // Try to check if the page exists by fetching it
    // Note: CORS will prevent this, so we just open in new tab
    // The browser will handle if page doesn't exist
    
    // Find parent node to use as fallback
    const parentEdge = network.edges.find(e => e.to === node.id);
    
    if (parentEdge) {
        const parentNode = network.nodes.find(n => n.id === parentEdge.from);
        if (parentNode) {
            const parentUrl = getWiktionaryUrl(parentNode, network);
            // Open both in new tabs - user can close the one that doesn't work
            // Or we show them a choice
            const message = `Opening Wiktionary page for "${node.form}".\nIf that page doesn't exist, try the parent: "${parentNode.form}"`;
            console.log(message);
        }
    }
    
    // Open the main URL
    window.open(url, '_blank');
}

// Load network data
async function loadNetworks() {
    try {
        // Try to load from parent directory first, then current directory
        let response;
        try {
            response = await fetch('../lemma_networks.json');
        } catch (e) {
            response = await fetch('lemma_networks.json');
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        networks = await response.json();
        
        document.getElementById('totalNetworks').textContent = networks.length.toLocaleString();
        document.getElementById('graph').innerHTML = '<p class="loading">Network data loaded. Search for a lemma or click "Random Network" to begin.</p>';
        
        // Enable buttons
        document.getElementById('searchBtn').disabled = false;
        document.getElementById('randomBtn').disabled = false;
        
    } catch (error) {
        document.getElementById('graph').innerHTML = `<p class="error">Error loading data: ${error.message}</p>`;
    }
}

// Search for networks
function searchNetworks(query) {
    if (!query || query.length < 2) return [];
    
    query = query.toLowerCase();
    const results = [];
    
    for (const network of networks) {
        // Search in all nodes
        for (const node of network.nodes) {
            const form = (node.form || '').toLowerCase();
            const meanings = (node.meanings || []).join(' ').toLowerCase();
            const lang = node.language || '';
            
            if (form.includes(query) || meanings.includes(query)) {
                results.push({
                    network: network,
                    node: node,
                    matchType: form.includes(query) ? 'form' : 'meaning'
                });
                
                if (results.length >= 20) break; // Limit suggestions
            }
        }
        if (results.length >= 20) break;
    }
    
    return results;
}

// Display search suggestions
function showSuggestions(results) {
    const suggestionsDiv = document.getElementById('suggestions');
    
    if (results.length === 0) {
        suggestionsDiv.style.display = 'none';
        return;
    }
    
    suggestionsDiv.innerHTML = results.map(result => {
        const node = result.node;
        const network = result.network;
        const rootForm = network.root_node.form;
        const meaning = node.meanings && node.meanings.length > 0 
            ? node.meanings[0].substring(0, 60) + (node.meanings[0].length > 60 ? '...' : '')
            : 'No meaning available';
        
        return `
            <div class="suggestion-item" onclick="selectNetwork('${network.network_id}')">
                <strong>${node.form}</strong> (${node.language})
                <small>${meaning}</small>
                <small style="color: #999;">Network root: ${rootForm}</small>
            </div>
        `;
    }).join('');
    
    suggestionsDiv.style.display = 'block';
}

// Select and visualize a network
function selectNetwork(networkId) {
    const network = networks.find(n => n.network_id === networkId);
    if (!network) return;
    
    currentNetwork = network;
    document.getElementById('suggestions').style.display = 'none';
    visualizeNetwork(network);
}

// Get color based on language
function getNodeColor(language) {
    if (language === 'egy') return '#ff6b6b';
    if (language === 'dem') return '#4ecdc4';
    if (language.startsWith('cop')) return '#95e1d3';
    return '#ddd';
}

// Get edge color based on type
function getEdgeColor(type) {
    if (type === 'EVOLVES') return '#e74c3c';
    if (type === 'DESCENDS') return '#3498db';
    if (type === 'VARIANT') return '#95a5a6';
    return '#999';
}

// Get edge style based on type
function getEdgeStyle(type) {
    if (type === 'VARIANT') return '5,5'; // Dashed
    return '0'; // Solid
}

// Visualize network using D3.js force-directed graph
function visualizeNetwork(network) {
    // Update stats
    document.getElementById('currentNodes').textContent = network.nodes.length;
    document.getElementById('currentEdges').textContent = network.edges.length;
    
    const languages = new Set(network.nodes.map(n => n.language));
    document.getElementById('languages').textContent = languages.size;
    
    // Clear previous visualization
    const container = document.getElementById('graph');
    container.innerHTML = '';
    
    // Set up SVG
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Add zoom behavior
    const g = svg.append('g');
    
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create node and link data
    const nodes = network.nodes.map(n => ({
        ...n,
        id: n.id,
        label: n.form || n.id,
        isRoot: n.id === network.root_node.id
    }));
    
    const links = network.edges.map(e => ({
        source: e.from,
        target: e.to,
        type: e.type,
        ...e
    }));
    
    // Create force simulation
    simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(d => d.type === 'VARIANT' ? 80 : 150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));
    
    // Create arrow markers for directed edges
    svg.append('defs').selectAll('marker')
        .data(['EVOLVES', 'DESCENDS', 'VARIANT'])
        .enter().append('marker')
        .attr('id', d => `arrow-${d}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => getEdgeColor(d));
    
    // Create links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('stroke', d => getEdgeColor(d.type))
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', d => getEdgeStyle(d.type))
        .attr('marker-end', d => `url(#arrow-${d.type})`);
    
    // Create nodes
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles
    node.append('circle')
        .attr('r', d => d.isRoot ? 20 : 15)
        .attr('fill', d => getNodeColor(d.language))
        .attr('stroke', d => d.isRoot ? '#ffd700' : '#333')
        .attr('stroke-width', d => d.isRoot ? 4 : 2)
        .style('cursor', 'pointer')
        .on('mouseover', showNodeInfo)
        .on('mouseout', hideNodeInfo)
        .on('click', (event, d) => {
            event.stopPropagation();
            openWiktionaryPage(d, network);
        });
    
    // Add labels
    node.append('text')
        .text(d => d.label)
        .attr('x', 0)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('font-weight', d => d.isRoot ? 'bold' : 'normal')
        .attr('fill', '#333');
    
    // Add period/dialect labels
    node.append('text')
        .text(d => d.period || d.dialect || '')
        .attr('x', 0)
        .attr('y', 45)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#666')
        .attr('font-style', 'italic');
    
    // Update positions on each tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Zoom to fit all nodes after simulation stabilizes
    simulation.on('end', () => {
        // Calculate bounding box of all nodes
        const padding = 50;
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        nodes.forEach(d => {
            if (d.x < minX) minX = d.x;
            if (d.y < minY) minY = d.y;
            if (d.x > maxX) maxX = d.x;
            if (d.y > maxY) maxY = d.y;
        });
        
        // Calculate scale to fit all nodes in viewport
        const dx = maxX - minX;
        const dy = maxY - minY;
        const scale = Math.min(
            (width - padding * 2) / dx,
            (height - padding * 2) / dy,
            2  // Don't zoom in too much for small networks
        );
        
        // Calculate translate to center the network
        const translateX = width / 2 - scale * (minX + maxX) / 2;
        const translateY = height / 2 - scale * (minY + maxY) / 2;
        
        // Apply the transform
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    });
    
    // Drag functions
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
        d.fx = null;
        d.fy = null;
    }
}

// Show node information on hover
function showNodeInfo(event, d) {
    const infoDiv = document.getElementById('nodeInfo');
    
    let html = `
        <h3>${d.form} <span style="font-size: 0.7em; color: #0066cc;">🔗 Click to view on Wiktionary</span></h3>
        <p><strong>Language:</strong> ${d.language}</p>
        <p><strong>Part of Speech:</strong> ${d.part_of_speech || 'unknown'}</p>
    `;
    
    if (d.period) {
        html += `<p><strong>Period:</strong> ${d.period}</p>`;
    }
    
    if (d.dialect) {
        html += `<p><strong>Dialect:</strong> ${d.dialect}</p>`;
    }
    
    if (d.hieroglyphs) {
        html += `<p><strong>Hieroglyphs:</strong> ${d.hieroglyphs}</p>`;
    }
    
    if (d.meanings && d.meanings.length > 0) {
        html += `<div class="meanings"><strong>Meanings:</strong><ul>`;
        d.meanings.slice(0, 3).forEach(m => {
            const cleaned = m.replace(/\{\{.*?\}\}/g, '').substring(0, 100);
            html += `<li>${cleaned}${m.length > 100 ? '...' : ''}</li>`;
        });
        html += `</ul></div>`;
    }
    
    infoDiv.innerHTML = html;
    infoDiv.style.display = 'block';
    infoDiv.style.left = (event.pageX + 15) + 'px';
    infoDiv.style.top = (event.pageY + 15) + 'px';
}

// Hide node information
function hideNodeInfo() {
    document.getElementById('nodeInfo').style.display = 'none';
}

// Show random network
function showRandomNetwork() {
    if (networks.length === 0) return;
    
    const randomIndex = Math.floor(Math.random() * networks.length);
    const network = networks[randomIndex];
    selectNetwork(network.network_id);
}

// Event listeners
document.getElementById('searchInput').addEventListener('input', (e) => {
    const query = e.target.value;
    if (query.length >= 2) {
        const results = searchNetworks(query);
        showSuggestions(results);
    } else {
        document.getElementById('suggestions').style.display = 'none';
    }
});

document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = e.target.value;
        const results = searchNetworks(query);
        if (results.length > 0) {
            selectNetwork(results[0].network.network_id);
        }
    }
});

document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value;
    const results = searchNetworks(query);
    if (results.length > 0) {
        selectNetwork(results[0].network.network_id);
    }
});

document.getElementById('randomBtn').addEventListener('click', showRandomNetwork);

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('#searchInput') && !e.target.closest('#suggestions')) {
        document.getElementById('suggestions').style.display = 'none';
    }
});

// Initialize
loadNetworks();
