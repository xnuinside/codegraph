// Panel drag and collapse functionality
document.querySelectorAll('.panel').forEach(panel => {
    const header = panel.querySelector('.panel-header');
    const toggleBtn = panel.querySelector('.panel-toggle');
    let isDragging = false;
    let startX, startY, startLeft, startTop;

    // Collapse/expand
    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('collapsed');
        toggleBtn.textContent = panel.classList.contains('collapsed') ? '+' : '−';
        toggleBtn.title = panel.classList.contains('collapsed') ? 'Expand' : 'Collapse';
    });

    // Drag functionality
    header.addEventListener('mousedown', (e) => {
        if (e.target === toggleBtn) return;
        isDragging = true;
        const rect = panel.getBoundingClientRect();
        startX = e.clientX;
        startY = e.clientY;
        startLeft = rect.left;
        startTop = rect.top;
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
        panel.style.left = startLeft + 'px';
        panel.style.top = startTop + 'px';
        document.body.style.cursor = 'move';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        panel.style.left = (startLeft + dx) + 'px';
        panel.style.top = (startTop + dy) + 'px';
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        document.body.style.cursor = '';
    });
});

// Calculate stats
const moduleCount = graphData.nodes.filter(n => n.type === 'module').length;
const entityCount = graphData.nodes.filter(n => n.type === 'entity').length;
const moduleLinks = graphData.links.filter(l => l.type === 'module-module').length;
document.getElementById('stats-content').innerHTML = `
    <p>Modules: ${moduleCount}</p>
    <p>Entities: ${entityCount}</p>
    <p>Module connections: ${moduleLinks}</p>
`;

// Calculate links count for each node
const nodeLinksMap = {};
graphData.nodes.forEach(n => {
    nodeLinksMap[n.id] = { linksIn: 0, linksOut: 0 };
});
graphData.links.forEach(l => {
    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
    if (nodeLinksMap[sourceId]) nodeLinksMap[sourceId].linksOut++;
    if (nodeLinksMap[targetId]) nodeLinksMap[targetId].linksIn++;
});

// Populate unlinked modules panel
const unlinkedModules = graphData.unlinkedModules || [];
document.getElementById('unlinked-count').textContent = `(${unlinkedModules.length})`;
if (unlinkedModules.length > 0) {
    document.getElementById('unlinked-list').innerHTML = `
        <ul>
            ${unlinkedModules.map(m => `
                <li data-module-id="${m.id}" title="${m.fullPath}">
                    ${m.id}
                    <span class="path">${m.fullPath}</span>
                </li>
            `).join('')}
        </ul>
    `;
} else {
    document.getElementById('unlinked-list').innerHTML = '<p style="color: #888; padding: 5px;">No unlinked modules</p>';
}

// Tab switching for unlinked panel
document.querySelectorAll('.unlinked-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.unlinked-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.unlinked-tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Links count filter function
function updateLinksCount() {
    const threshold = parseInt(document.getElementById('links-threshold').value) || 0;
    const countIn = document.getElementById('links-in-check').checked;
    const countOut = document.getElementById('links-out-check').checked;

    const nodesWithLinks = graphData.nodes
        .filter(n => n.type === 'module' || n.type === 'entity')
        .map(n => {
            const links = nodeLinksMap[n.id] || { linksIn: 0, linksOut: 0 };
            let total = 0;
            if (countIn && countOut) total = links.linksIn + links.linksOut;
            else if (countIn) total = links.linksIn;
            else if (countOut) total = links.linksOut;
            return { ...n, linksIn: links.linksIn, linksOut: links.linksOut, totalLinks: total };
        })
        .filter(n => n.totalLinks > threshold)
        .sort((a, b) => b.totalLinks - a.totalLinks);

    document.getElementById('links-count').textContent = `(${nodesWithLinks.length})`;

    if (nodesWithLinks.length > 0) {
        document.getElementById('links-count-content').innerHTML = `
            <ul>
                ${nodesWithLinks.map(n => `
                    <li data-node-id="${n.id}" title="${n.type === 'module' ? n.fullPath : n.parent}">
                        <span class="links-count">${n.totalLinks}</span> ${n.label || n.id}
                        <span class="entity-type">${n.type === 'module' ? 'module' : n.entityType}</span>
                    </li>
                `).join('')}
            </ul>
        `;

        // Add click handlers for links count items
        document.querySelectorAll('#links-count-content li').forEach(li => {
            li.addEventListener('click', () => {
                const nodeId = li.dataset.nodeId;
                highlightNode(nodeId);
            });
        });
    } else {
        document.getElementById('links-count-content').innerHTML = '<p style="color: #888;">No matching nodes</p>';
    }
}

// Initialize links count and add event listeners
document.getElementById('links-in-check').addEventListener('change', updateLinksCount);
document.getElementById('links-out-check').addEventListener('change', updateLinksCount);
document.getElementById('links-threshold').addEventListener('input', updateLinksCount);
updateLinksCount();

// Size scaling state
let sizeByCode = true;

// Calculate max lines for scaling
const maxLines = Math.max(...graphData.nodes.map(n => n.lines || 0), 1);

// Function to get node size based on lines of code
function getNodeSize(d, baseSize) {
    if (!sizeByCode || !d.lines) return baseSize;
    // Scale between baseSize and baseSize * 3 based on lines
    const scale = 1 + (d.lines / maxLines) * 2;
    return baseSize * scale;
}

// Function to update massive objects list
function updateMassiveObjects() {
    const threshold = parseInt(document.getElementById('massive-threshold').value) || 50;
    const showModules = document.getElementById('filter-modules').checked;
    const showClasses = document.getElementById('filter-classes').checked;
    const showFunctions = document.getElementById('filter-functions').checked;

    const massiveNodes = graphData.nodes
        .filter(n => (n.type === 'entity' || n.type === 'module') && n.lines >= threshold)
        .filter(n => {
            if (n.type === 'module') return showModules;
            if (n.entityType === 'class') return showClasses;
            if (n.entityType === 'function') return showFunctions;
            return true;
        })
        .sort((a, b) => b.lines - a.lines);

    document.getElementById('massive-count').textContent = `(${massiveNodes.length})`;
    document.getElementById('massive-list').innerHTML = massiveNodes.map(n => `
        <li data-node-id="${n.id}" title="${n.type === 'module' ? n.fullPath : n.parent}">
            <span class="lines">${n.lines}</span> ${n.label || n.id}
            <span class="entity-type">${n.type === 'module' ? 'module' : n.entityType}</span>
        </li>
    `).join('');

    // Add click handlers
    document.querySelectorAll('#massive-list li').forEach(li => {
        li.addEventListener('click', () => {
            const nodeId = li.dataset.nodeId;
            highlightNode(nodeId);
        });
    });
}

// Add event listeners for massive objects filters
document.getElementById('filter-modules').addEventListener('change', updateMassiveObjects);
document.getElementById('filter-classes').addEventListener('change', updateMassiveObjects);
document.getElementById('filter-functions').addEventListener('change', updateMassiveObjects);
document.getElementById('massive-threshold').addEventListener('input', updateMassiveObjects);

// Initial population
updateMassiveObjects();

const width = window.innerWidth;
const height = window.innerHeight;

// Create SVG
const svg = d3.select("#graph")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// Add zoom behavior
const g = svg.append("g");

const zoom = d3.zoom()
    .scaleExtent([0.05, 4])
    .on("zoom", (event) => {
        g.attr("transform", event.transform);
    });

svg.call(zoom);

// Tooltip
const tooltip = d3.select("#tooltip");

// Track collapsed nodes (modules and entities)
const collapsedNodes = new Set();

// Create arrow markers for different link types
const defs = svg.append("defs");

// Module-module arrow (orange)
defs.append("marker")
    .attr("id", "arrow-module-module")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25)
    .attr("refY", 0)
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("orient", "auto")
    .append("path")
    .attr("fill", "#ff9800")
    .attr("d", "M0,-5L10,0L0,5");

// Module-entity arrow (green)
defs.append("marker")
    .attr("id", "arrow-module-entity")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 18)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("fill", "#009c2c")
    .attr("d", "M0,-5L10,0L0,5");

// Dependency arrow (red)
defs.append("marker")
    .attr("id", "arrow-dependency")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 18)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("fill", "#d94a4a")
    .attr("d", "M0,-5L10,0L0,5");

// Scale spacing based on number of nodes
const nodeCount = graphData.nodes.length;
const scaleFactor = nodeCount > 40 ? 1 + (nodeCount - 40) / 50 : 1;

// Create force simulation with adjusted parameters for better spacing
const simulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(d => {
        const base = d.type === 'module-module' ? 300 : d.type === 'module-entity' ? 100 : 120;
        return base * scaleFactor;
    }).strength(0.3 / scaleFactor))
    .force("charge", d3.forceManyBody().strength(d => {
        const base = d.type === 'module' ? -800 : -300;
        return base * scaleFactor;
    }))
    .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05 / scaleFactor))
    .force("collision", d3.forceCollide().radius(d => {
        const base = d.type === 'module' ? 80 : 40;
        return base * scaleFactor;
    }).strength(1));

// Create links (module-module first so they appear behind)
const link = g.append("g")
    .selectAll("line")
    .data(graphData.links.sort((a, b) => {
        const order = {'module-module': 0, 'module-entity': 1, 'dependency': 2};
        return (order[a.type] || 2) - (order[b.type] || 2);
    }))
    .join("line")
    .attr("class", d => `link link-${d.type}`)
    .attr("marker-end", d => `url(#arrow-${d.type})`);

// Create nodes
const node = g.append("g")
    .selectAll("g")
    .data(graphData.nodes)
    .join("g")
    .attr("class", "node")
    .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

// Add shapes based on node type with size based on lines of code
node.each(function(d) {
    const el = d3.select(this);
    if (d.type === "module") {
        const size = getNodeSize(d, 30);
        el.append("rect")
            .attr("class", "node-module")
            .attr("width", size)
            .attr("height", size)
            .attr("x", -size / 2)
            .attr("y", -size / 2)
            .attr("rx", 4);
    } else if (d.type === "entity") {
        const r = getNodeSize(d, 10);
        el.append("circle")
            .attr("class", "node-entity")
            .attr("r", r);
    } else {
        el.append("circle")
            .attr("class", "node-external")
            .attr("r", 7);
    }
});

// Function to update node sizes
function updateNodeSizes() {
    node.each(function(d) {
        const el = d3.select(this);
        if (d.type === "module") {
            const size = getNodeSize(d, 30);
            el.select("rect")
                .attr("width", size)
                .attr("height", size)
                .attr("x", -size / 2)
                .attr("y", -size / 2);
        } else if (d.type === "entity") {
            const r = getNodeSize(d, 10);
            el.select("circle").attr("r", r);
        }
    });
    // Update labels position
    labels.attr("dy", d => {
        if (d.type === "module") {
            return getNodeSize(d, 30) / 2 + 15;
        }
        return getNodeSize(d, 10) + 10;
    });
}

// Size toggle event listener
document.getElementById('size-by-code').addEventListener('change', function() {
    sizeByCode = this.checked;
    updateNodeSizes();
});

// Display filter state
const displayFilters = {
    showModules: true,
    showClasses: true,
    showFunctions: true,
    showExternal: true,
    showLinkModule: true,
    showLinkEntity: true,
    showLinkDependency: true
};

// Display filter event listeners
document.getElementById('show-modules').addEventListener('change', function() {
    displayFilters.showModules = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-classes').addEventListener('change', function() {
    displayFilters.showClasses = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-functions').addEventListener('change', function() {
    displayFilters.showFunctions = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-external').addEventListener('change', function() {
    displayFilters.showExternal = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-link-module').addEventListener('change', function() {
    displayFilters.showLinkModule = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-link-entity').addEventListener('change', function() {
    displayFilters.showLinkEntity = this.checked;
    updateDisplayFilters();
});
document.getElementById('show-link-dependency').addEventListener('change', function() {
    displayFilters.showLinkDependency = this.checked;
    updateDisplayFilters();
});

// Check if node should be hidden by display filter
function isNodeFilteredOut(nodeData) {
    if (nodeData.type === 'module') return !displayFilters.showModules;
    if (nodeData.type === 'external') return !displayFilters.showExternal;
    if (nodeData.type === 'entity') {
        if (nodeData.entityType === 'class') return !displayFilters.showClasses;
        if (nodeData.entityType === 'function') return !displayFilters.showFunctions;
    }
    return false;
}

// Check if link should be hidden by display filter
function isLinkFilteredOut(linkData) {
    if (linkData.type === 'module-module') return !displayFilters.showLinkModule;
    if (linkData.type === 'module-entity') return !displayFilters.showLinkEntity;
    if (linkData.type === 'dependency') return !displayFilters.showLinkDependency;
    return false;
}

// Update display based on filters
function updateDisplayFilters() {
    // Update node visibility
    node.classed("node-hidden", d => isNodeFilteredOut(d) || isNodeHidden(d));

    // Update label visibility
    labels.classed("label-hidden", d => isNodeFilteredOut(d) || isNodeHidden(d));

    // Update link visibility
    link.classed("link-hidden", d => {
        // First check display filter
        if (isLinkFilteredOut(d)) return true;

        // Check if connected nodes are filtered out
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
        const targetId = typeof d.target === 'object' ? d.target.id : d.target;
        const sourceNode = graphData.nodes.find(n => n.id === sourceId);
        const targetNode = graphData.nodes.find(n => n.id === targetId);

        if (sourceNode && isNodeFilteredOut(sourceNode)) return true;
        if (targetNode && isNodeFilteredOut(targetNode)) return true;

        // Then check collapse state
        if (d.type === 'module-module') return false;
        if (sourceNode && isNodeHidden(sourceNode)) return true;
        if (targetNode && isNodeHidden(targetNode)) return true;
        if (d.type === 'module-entity' && collapsedNodes.has(sourceId)) return true;
        if (d.type === 'dependency' && collapsedNodes.has(sourceId)) return true;

        return false;
    });
}

// Add labels with dynamic positioning based on node size
const labels = g.append("g")
    .selectAll("text")
    .data(graphData.nodes)
    .join("text")
    .attr("class", d => `label ${d.type === 'module' ? 'label-module' : ''}`)
    .attr("dy", d => {
        if (d.type === "module") {
            return getNodeSize(d, 30) / 2 + 15;
        }
        return getNodeSize(d, 10) + 10;
    })
    .attr("text-anchor", "middle")
    .text(d => d.label || d.id);

// Node interactions
node.on("mouseover", function(event, d) {
    // Highlight connected links
    link.style("stroke-opacity", l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;
        return (sourceId === d.id || targetId === d.id) ? 1 : 0.2;
    });

    // Count connections
    const outgoing = graphData.links.filter(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        return sourceId === d.id;
    }).length;
    const incoming = graphData.links.filter(l => {
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;
        return targetId === d.id;
    }).length;

    tooltip
        .style("opacity", 1)
        .style("left", (event.pageX + 15) + "px")
        .style("top", (event.pageY - 15) + "px")
        .html(`
            <strong>${d.label || d.id}</strong><br>
            Type: ${d.entityType || d.type}<br>
            ${d.lines ? 'Lines of code: ' + d.lines + '<br>' : ''}
            ${d.fullPath ? 'Full Path: ' + d.fullPath + '<br>' : ''}
            ${d.parent ? 'Module: ' + d.parent + '<br>' : ''}
            <div class="links-info">
                <span class="links-out">Links out: ${outgoing}</span>
                <span class="links-in">Links in: ${incoming}</span>
            </div>
            ${collapsedNodes.has(d.id) ? '<em>(collapsed)</em>' : ''}
        `);
})
.on("mouseout", function() {
    link.style("stroke-opacity", 0.6);
    tooltip.style("opacity", 0);
})
.on("click", function(event, d) {
    if (d.type === "module" || d.type === "entity") {
        toggleCollapse(d);
    }
})
.on("dblclick", function(event, d) {
    event.stopPropagation();
    // If node is pinned (was dragged), release it
    if (d.fx !== null || d.fy !== null) {
        d.fx = null;
        d.fy = null;
        simulation.alpha(0.3).restart();
    } else {
        // Focus on this node (zoom to it)
        const scale = 1.5;
        svg.transition()
            .duration(500)
            .call(zoom.transform, d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(scale)
                .translate(-d.x, -d.y));
    }
});

function toggleCollapse(targetNode) {
    const nodeId = targetNode.id;

    if (collapsedNodes.has(nodeId)) {
        collapsedNodes.delete(nodeId);
    } else {
        collapsedNodes.add(nodeId);
    }

    // Update node visual to show collapsed state
    node.select("rect, circle")
        .classed("collapsed", d => collapsedNodes.has(d.id));

    updateVisibility();
}

function getChildNodes(nodeId, nodeType) {
    // Get all nodes that are direct children of this node
    const children = new Set();

    if (nodeType === 'module') {
        // Module's children are entities with this module as parent
        graphData.nodes.forEach(n => {
            if (n.parent === nodeId) {
                children.add(n.id);
            }
        });
    } else if (nodeType === 'entity') {
        // Entity's children are nodes it links to via dependency
        graphData.links.forEach(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            if (sourceId === nodeId && l.type === 'dependency') {
                children.add(targetId);
            }
        });
    }

    return children;
}

function isNodeHidden(nodeData) {
    // Module nodes are never hidden
    if (nodeData.type === 'module') return false;

    // Check if parent module is collapsed
    if (nodeData.parent && collapsedNodes.has(nodeData.parent)) {
        return true;
    }

    // Check if this is a dependency of a collapsed entity
    for (const link of graphData.links) {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (targetId === nodeData.id && link.type === 'dependency') {
            // Check if source entity is collapsed or hidden
            const sourceNode = graphData.nodes.find(n => n.id === sourceId);
            if (sourceNode) {
                if (collapsedNodes.has(sourceId)) return true;
                if (sourceNode.parent && collapsedNodes.has(sourceNode.parent)) return true;
            }
        }
    }

    return false;
}

function updateVisibility() {
    // Use updateDisplayFilters which handles both collapse state and display filters
    updateDisplayFilters();
}

// Simulation tick
simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node.attr("transform", d => `translate(${d.x},${d.y})`);

    labels
        .attr("x", d => d.x)
        .attr("y", d => d.y);
});

// Drag functions - nodes stay where you drag them
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
    // Keep node at dragged position (don't reset fx/fy to null)
    // Double-click to release node back to simulation
}

// Initial zoom to fit content
simulation.on("end", () => {
    // Calculate bounds for ALL nodes
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    graphData.nodes.forEach(n => {
        minX = Math.min(minX, n.x);
        maxX = Math.max(maxX, n.x);
        minY = Math.min(minY, n.y);
        maxY = Math.max(maxY, n.y);
    });

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    const padding = 100;
    const graphWidth = maxX - minX + padding * 2;
    const graphHeight = maxY - minY + padding * 2;

    // Calculate scale to fit all nodes
    const fitScale = Math.min(width / graphWidth, height / graphHeight);

    // For larger graphs (>20 nodes), zoom out more aggressively
    const nodeCount = graphData.nodes.length;
    let maxZoom = 0.7;
    if (nodeCount > 20) {
        // Reduce max zoom based on node count: 0.7 -> down to 0.4 for 120+ nodes
        maxZoom = Math.max(0.4, 0.7 - (nodeCount - 20) * 0.003);
    }

    const scale = Math.min(fitScale * 0.85, maxZoom);

    svg.transition()
        .duration(500)
        .call(zoom.transform, d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(scale)
            .translate(-centerX, -centerY));
});

// ==================== SEARCH FUNCTIONALITY ====================

const searchInput = document.getElementById('searchInput');
const searchClear = document.getElementById('searchClear');
const autocompleteList = document.getElementById('autocompleteList');
const highlightInfo = document.getElementById('highlightInfo');
const highlightText = document.getElementById('highlightText');
const clearHighlightBtn = document.getElementById('clearHighlight');

let selectedAutocompleteIndex = -1;
let currentHighlightedNode = null;
let filteredNodes = [];

// Build searchable index
const searchIndex = graphData.nodes.map(n => ({
    id: n.id,
    label: n.label || n.id,
    type: n.type,
    parent: n.parent || null,
    searchText: ((n.label || n.id) + ' ' + (n.parent || '')).toLowerCase()
}));

// Get connected nodes for a given node
function getConnectedNodes(nodeId) {
    const connected = new Set();
    connected.add(nodeId);

    graphData.links.forEach(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;

        if (sourceId === nodeId) {
            connected.add(targetId);
        }
        if (targetId === nodeId) {
            connected.add(sourceId);
        }
    });

    return connected;
}

// Get connected links for a given node
function getConnectedLinks(nodeId) {
    return graphData.links.filter(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;
        return sourceId === nodeId || targetId === nodeId;
    });
}

// Highlight a node and its connections
function highlightNode(nodeId) {
    const connectedNodes = getConnectedNodes(nodeId);
    currentHighlightedNode = nodeId;

    // Update nodes
    node.classed('dimmed', d => !connectedNodes.has(d.id))
        .classed('highlighted', d => connectedNodes.has(d.id) && d.id !== nodeId)
        .classed('highlighted-main', d => d.id === nodeId);

    // Update links
    link.classed('dimmed', d => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
        const targetId = typeof d.target === 'object' ? d.target.id : d.target;
        return sourceId !== nodeId && targetId !== nodeId;
    })
    .classed('highlighted', d => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
        const targetId = typeof d.target === 'object' ? d.target.id : d.target;
        return sourceId === nodeId || targetId === nodeId;
    });

    // Update labels
    labels.classed('dimmed', d => !connectedNodes.has(d.id));

    // Show highlight info
    const nodeData = graphData.nodes.find(n => n.id === nodeId);
    highlightText.textContent = `Highlighting: ${nodeData.label || nodeData.id} (${connectedNodes.size} connected)`;
    highlightInfo.classList.add('visible');

    // Zoom to the node
    const targetNode = graphData.nodes.find(n => n.id === nodeId);
    if (targetNode) {
        const scale = 1.2;
        svg.transition()
            .duration(500)
            .call(zoom.transform, d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(scale)
                .translate(-targetNode.x, -targetNode.y));
    }
}

// Clear all highlighting
function clearHighlight() {
    currentHighlightedNode = null;

    node.classed('dimmed', false)
        .classed('highlighted', false)
        .classed('highlighted-main', false);

    link.classed('dimmed', false)
        .classed('highlighted', false);

    labels.classed('dimmed', false);

    highlightInfo.classList.remove('visible');
    searchInput.value = '';
    searchClear.classList.remove('visible');
    hideAutocomplete();
}

// Filter nodes based on search query
function filterNodes(query) {
    if (!query) return [];
    const lowerQuery = query.toLowerCase();
    return searchIndex
        .filter(n => n.searchText.includes(lowerQuery))
        .slice(0, 10); // Limit to 10 results
}

// Render autocomplete list
function renderAutocomplete(results) {
    if (results.length === 0) {
        hideAutocomplete();
        return;
    }

    filteredNodes = results;
    selectedAutocompleteIndex = -1;

    autocompleteList.innerHTML = results.map((n, i) => `
        <div class="autocomplete-item" data-index="${i}" data-id="${n.id}">
            <span class="node-type ${n.type}">${n.type}</span>
            <span class="node-name">${n.label}</span>
            ${n.parent ? `<span class="node-parent">${n.parent}</span>` : ''}
        </div>
    `).join('');

    autocompleteList.classList.add('visible');

    // Add click handlers
    autocompleteList.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            selectNode(item.dataset.id);
        });
    });
}

// Hide autocomplete
function hideAutocomplete() {
    autocompleteList.classList.remove('visible');
    filteredNodes = [];
    selectedAutocompleteIndex = -1;
}

// Select a node from autocomplete
function selectNode(nodeId) {
    const nodeData = searchIndex.find(n => n.id === nodeId);
    if (nodeData) {
        searchInput.value = nodeData.label;
        hideAutocomplete();
        highlightNode(nodeId);
    }
}

// Update selected item in autocomplete
function updateSelectedItem() {
    const items = autocompleteList.querySelectorAll('.autocomplete-item');
    items.forEach((item, i) => {
        item.classList.toggle('selected', i === selectedAutocompleteIndex);
    });

    // Scroll into view
    if (selectedAutocompleteIndex >= 0 && items[selectedAutocompleteIndex]) {
        items[selectedAutocompleteIndex].scrollIntoView({ block: 'nearest' });
    }
}

// Search input event handlers
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    searchClear.classList.toggle('visible', query.length > 0);

    if (query.length > 0) {
        const results = filterNodes(query);
        renderAutocomplete(results);
    } else {
        hideAutocomplete();
    }
});

searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (filteredNodes.length > 0) {
            selectedAutocompleteIndex = Math.min(selectedAutocompleteIndex + 1, filteredNodes.length - 1);
            updateSelectedItem();
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (filteredNodes.length > 0) {
            selectedAutocompleteIndex = Math.max(selectedAutocompleteIndex - 1, 0);
            updateSelectedItem();
        }
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedAutocompleteIndex >= 0 && filteredNodes[selectedAutocompleteIndex]) {
            selectNode(filteredNodes[selectedAutocompleteIndex].id);
        } else if (filteredNodes.length > 0) {
            selectNode(filteredNodes[0].id);
        }
    } else if (e.key === 'Escape') {
        if (autocompleteList.classList.contains('visible')) {
            hideAutocomplete();
        } else {
            clearHighlight();
        }
        searchInput.blur();
    }
});

searchInput.addEventListener('focus', () => {
    const query = searchInput.value.trim();
    if (query.length > 0) {
        const results = filterNodes(query);
        renderAutocomplete(results);
    }
});

// Clear button
searchClear.addEventListener('click', () => {
    clearHighlight();
});

// Clear highlight button
clearHighlightBtn.addEventListener('click', () => {
    clearHighlight();
});

// Close autocomplete when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-container')) {
        hideAutocomplete();
    }
});

// Keyboard shortcut to focus search (Ctrl+F or Cmd+F)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
    }
    if (e.key === 'Escape' && currentHighlightedNode) {
        clearHighlight();
    }
});

// Orphan modules click handler - navigate to module node
document.querySelectorAll('#unlinked-list li').forEach(li => {
    li.addEventListener('click', () => {
        const moduleId = li.dataset.moduleId;
        const targetNode = graphData.nodes.find(n => n.id === moduleId);
        if (targetNode) {
            // Zoom and pan to the node
            const scale = 1.5;
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(width / 2 - targetNode.x * scale, height / 2 - targetNode.y * scale)
                    .scale(scale));

            // Highlight the node temporarily
            node.selectAll("rect, circle")
                .style("filter", n => n.id === moduleId ? "brightness(2) drop-shadow(0 0 10px #ff9800)" : "none");

            // Reset highlight after 2 seconds
            setTimeout(() => {
                node.selectAll("rect, circle").style("filter", "none");
            }, 2000);
        }
    });
});
