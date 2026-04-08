// graph.js
let network = null;
let graphNodes = new vis.DataSet();
let graphEdges = new vis.DataSet();

function initGraph(simData) {
    graphNodes.clear();
    graphEdges.clear();

    const processCount = simData.processes;
    const resourceCount = simData.resources;
    
    // Add Process Nodes (Circles)
    for (let i = 0; i < processCount; i++) {
        graphNodes.add({
            id: `P${i}`,
            label: `P${i}`,
            shape: 'circle',
            color: { background: '#3b82f6', border: '#2563eb' },
            font: { color: 'white', size: 16 }
        });
    }

    // Add Resource Nodes (Squares)
    for (let j = 0; j < resourceCount; j++) {
        graphNodes.add({
            id: `R${j}`,
            label: `R${j}`,
            shape: 'square',
            color: { background: '#eab308', border: '#ca8a04' },
            font: { color: 'white', size: 16 }
        });
    }

    // Add Edges
    const needOrReq = simData.mode === 'banker' ? simData.result.need : simData.demand;

    for (let i = 0; i < processCount; i++) {
        for (let j = 0; j < resourceCount; j++) {
            // Allocation Edge: Resource -> Process
            if (simData.allocation[i][j] > 0) {
                graphEdges.add({
                    id: `alloc-R${j}-P${i}`,
                    from: `R${j}`,
                    to: `P${i}`,
                    label: simData.allocation[i][j].toString(),
                    arrows: 'to',
                    color: { color: '#22c55e' },
                    font: { align: 'middle', color: '#94a3b8' }
                });
            }

            // Need/Request Edge: Process -> Resource
            if (needOrReq[i][j] > 0) {
                graphEdges.add({
                    id: `req-P${i}-R${j}`,
                    from: `P${i}`,
                    to: `R${j}`,
                    label: needOrReq[i][j].toString(),
                    arrows: 'to',
                    color: { color: '#94a3b8' },
                    dashes: true,
                    font: { align: 'middle', color: '#94a3b8' }
                });
            }
        }
    }

    const container = document.getElementById('resource-graph');
    const data = { nodes: graphNodes, edges: graphEdges };
    
    const options = {
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04,
                damping: 0.09
            }
        },
        interaction: { hover: true }
    };
    
    network = new vis.Network(container, data, options);
}

function removeProcessFromGraph(processIndex) {
    const pId = `P${processIndex}`;
    
    // Change node color to Green (Finished)
    graphNodes.update({
        id: pId,
        color: { background: '#22c55e', border: '#16a34a' }
    });
    
    // Remove all edges connected to this process
    const edgesToRemove = graphEdges.get({
        filter: function (item) {
            return (item.from === pId || item.to === pId);
        }
    });
    
    graphEdges.remove(edgesToRemove);
}

function highlightDeadlock(deadlockedProcesses) {
    // Highlight deadlocked processes in Red
    deadlockedProcesses.forEach(i => {
        graphNodes.update({
            id: `P${i}`,
            color: { background: '#ef4444', border: '#dc2626' }
        });
    });
    
    // Highlight their request edges in Red indicating cycle
    deadlockedProcesses.forEach(i => {
        const edgesToUpdate = graphEdges.get({
            filter: function (item) {
                return (item.from === `P${i}`);
            }
        });
        
        edgesToUpdate.forEach(edge => {
            graphEdges.update({
                id: edge.id,
                color: { color: '#ef4444' },
                width: 2
            });
        });
    });
}

function resetProcessHighlights() {
    graphNodes.forEach(node => {
        if (node.id.startsWith('P')) {
            const current = node.color?.background?.toString?.() || node.color?.background;
            if (current !== '#22c55e' && current !== '#ef4444') {
                graphNodes.update({
                    id: node.id,
                    color: { background: '#3b82f6', border: '#2563eb' }
                });
            }
        }
    });

    graphEdges.forEach(edge => {
        const defaultColor = edge.dashes ? '#94a3b8' : '#22c55e';
        graphEdges.update({
            id: edge.id,
            color: { color: defaultColor },
            width: 1
        });
    });
}

function highlightActiveProcess(processIndex, status) {
    if (typeof resetProcessHighlights === 'function') {
        resetProcessHighlights();
    }
    const pId = `P${processIndex}`;
    const highlightColor = status === 'wait' ? '#f59e0b' : '#38bdf8';

    graphNodes.update({
        id: pId,
        color: { background: highlightColor, border: '#0ea5e9' }
    });

    const connectedEdges = graphEdges.get({
        filter: function (item) {
            return item.from === pId || item.to === pId;
        }
    });

    connectedEdges.forEach(edge => {
        graphEdges.update({
            id: edge.id,
            color: { color: highlightColor },
            width: 3
        });
    });
}

