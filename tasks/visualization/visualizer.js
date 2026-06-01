// visualizer.js - Custom D3 visualization for Croissant Tasks
// This script assumes D3.js is loaded in the global scope.

function renderVisualization(problemData, solutionData, containerSelector, alignSolutions = false, hideUnsolved = false) {
  const width = 1200;
  const height = 800;
  const margin = { top: 40, right: 100, bottom: 40, left: 100 };

  const svg = d3.select(containerSelector)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const mainGroup = svg.append("g")
    .attr("class", "main-group");

  const zoom = d3.zoom()
    .scaleExtent([0.1, 5])
    .on("zoom", (event) => {
      mainGroup.attr("transform", event.transform);
    });

  svg.call(zoom);
  svg.call(zoom.transform, d3.zoomIdentity.translate(margin.left, margin.top));

  const linkLayer = mainGroup.append("g").attr("class", "link-layer");
  const nodeLayer = mainGroup.append("g").attr("class", "node-layer");

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Process hierarchies
  const probRoot = d3.hierarchy(problemData, d => d["croissant:subTask"]);
  const solRoot = d3.hierarchy(solutionData, d => d["croissant:subTask"]);
  // Extract solved problem IDs to sort problems
  const solvedProblemIds = new Set();
  const extractSolvedIds = (node) => {
    const basedOn = node["schema:isBasedOn"];
    if (basedOn && basedOn["@id"]) {
      solvedProblemIds.add(basedOn["@id"]);
    }
    const subTasks = node["croissant:subTask"];
    if (subTasks) {
      subTasks.forEach(extractSolvedIds);
    }
  };
  extractSolvedIds(solutionData);

  // Filter out unsolved problems if requested
  if (hideUnsolved) {
    const keepNode = (node) => {
      const isSolved = solvedProblemIds.has(node.data["@id"]);
      let hasSolvedDescendant = false;
      
      if (node.children) {
        node.children = node.children.filter(keepNode);
        hasSolvedDescendant = node.children.length > 0;
      }
      
      return isSolved || hasSolvedDescendant;
    };
    keepNode(probRoot);
  }

  // Sort probRoot so solved problems come first
  probRoot.sort((a, b) => {
    const aSolved = solvedProblemIds.has(a.data["@id"]);
    const bSolved = solvedProblemIds.has(b.data["@id"]);
    if (aSolved && !bSolved) return -1;
    if (!aSolved && bSolved) return 1;
    return 0;
  });
  // Create a map from problem ID to its index in the sorted probRoot
  const problemOrder = new Map();
  if (probRoot.children) {
    probRoot.children.forEach((d, i) => {
      problemOrder.set(d.data["@id"], i);
    });
  }

  // Sort solRoot to match the order of problems
  solRoot.sort((a, b) => {
    const aProbId = a.data["schema:isBasedOn"] && a.data["schema:isBasedOn"]["@id"];
    const bProbId = b.data["schema:isBasedOn"] && b.data["schema:isBasedOn"]["@id"];
    const aIdx = problemOrder.has(aProbId) ? problemOrder.get(aProbId) : Infinity;
    const bIdx = problemOrder.has(bProbId) ? problemOrder.get(bProbId) : Infinity;
    return aIdx - bIdx;
  });

  // Layouts
  const probTree = d3.tree().size([innerHeight, innerWidth / 3]);
  const solTree = d3.tree().size([innerHeight, innerWidth / 3]);

  probTree(probRoot);
  solTree(solRoot);

  // Align solutions with problems if requested
  if (alignSolutions) {
    const probXMap = new Map();
    probRoot.descendants().forEach(d => {
      probXMap.set(d.data["@id"], d.x);
    });

    solRoot.descendants().forEach(d => {
      const basedOn = d.data["schema:isBasedOn"];
      if (basedOn && basedOn["@id"]) {
        const probX = probXMap.get(basedOn["@id"]);
        if (probX !== undefined) {
          d.x = probX;
        }
      }
    });
  }

  // Custom positioning to bring roots to the top
  const shiftTreeToTop = (root) => {
    let minX = Infinity;
    root.each(d => {
      if (d !== root && d.x < minX) minX = d.x;
    });
    // Shift all children so min among them is at least 40
    const shift = 40 - minX;
    root.each(d => {
      if (d !== root) d.x = d.x + shift;
    });
    root.x = 0; // Force root to the very top
  };

  shiftTreeToTop(probRoot);
  shiftTreeToTop(solRoot);

  // Shift solution tree to the right and flip it
  solRoot.each(d => {
    d.y = innerWidth - d.y;
  });

  // Shift problem tree slightly to the left to leave space in the middle
  probRoot.each(d => {
    d.y = d.y;
  });

  // Draw Problem Tree (Left)
  const probNodes = probRoot.descendants();
  const probLinks = probRoot.links();

  linkLayer.selectAll(".prob-link")
    .data(probLinks)
    .enter().append("path")
    .attr("class", "prob-link")
    .attr("d", d3.linkHorizontal()
      .x(d => d.y)
      .y(d => d.x))
    .attr("fill", "none")
    .attr("stroke", "#9ecae1")
    .attr("stroke-width", 2);

  const probNode = nodeLayer.selectAll(".prob-node")
    .data(probNodes)
    .enter().append("g")
    .attr("class", "prob-node")
    .attr("transform", d => `translate(${d.y},${d.x})`)
    .style("opacity", d => (d === probRoot || solvedProblemIds.has(d.data["@id"])) ? 1.0 : 0.4);

  probNode.append("circle")
    .attr("r", 6)
    .attr("fill", "#3182bd");

  probNode.append("text")
    .attr("dy", ".35em")
    .attr("x", d => d.children ? -10 : 10)
    .attr("text-anchor", d => d.children ? "end" : "start")
    .text(d => d.data["schema:name"] || d.data["@id"])
    .style("font-size", "12px")
    .style("font-family", "sans-serif");

  // Draw Solution Tree (Right)
  const solNodes = solRoot.descendants();
  const solLinks = solRoot.links();

  linkLayer.selectAll(".sol-link")
    .data(solLinks)
    .enter().append("path")
    .attr("class", "sol-link")
    .attr("d", d3.linkHorizontal()
      .x(d => d.y)
      .y(d => d.x))
    .attr("fill", "none")
    .attr("stroke", "#a1d99b")
    .attr("stroke-width", 2);

  const solNode = nodeLayer.selectAll(".sol-node")
    .data(solNodes)
    .enter().append("g")
    .attr("class", "sol-node")
    .attr("transform", d => `translate(${d.y},${d.x})`);

  solNode.append("circle")
    .attr("r", 6)
    .attr("fill", "#31a354");

  solNode.append("text")
    .attr("dy", ".35em")
    .attr("x", d => d.children ? 10 : -10)
    .attr("text-anchor", d => d.children ? "start" : "end")
    .text(d => {
      if (d.data["schema:name"]) return d.data["schema:name"];
      const id = d.data["@id"];
      if (id) {
        const hashIdx = id.lastIndexOf("#");
        if (hashIdx !== -1) return id.substring(hashIdx + 1);
        const slashIdx = id.lastIndexOf("/");
        if (slashIdx !== -1) return id.substring(slashIdx + 1);
        return id;
      }
      return "";
    })
    .style("font-size", "12px")
    .style("font-family", "sans-serif");

  // Draw cross-links between solutions and problems
  // We need to map solution nodes to problem nodes based on schema:isBasedOn
  const solMap = new Map();
  solNodes.forEach(d => {
    const basedOn = d.data["schema:isBasedOn"];
    if (basedOn && basedOn["@id"]) {
      solMap.set(d.data["@id"], { solNode: d, basedOnId: basedOn["@id"] });
    }
  });

  const probMap = new Map();
  probNodes.forEach(d => {
    probMap.set(d.data["@id"], d);
  });

  const crossLinks = [];
  solMap.forEach((val, key) => {
    const probNode = probMap.get(val.basedOnId);
    if (probNode) {
      crossLinks.push({
        source: val.solNode,
        target: probNode
      });
    }
  });

  linkLayer.selectAll(".cross-link")
    .data(crossLinks)
    .enter().append("path")
    .attr("class", "cross-link")
    .attr("d", d => {
      const sourceX = d.source.y;
      const sourceY = d.source.x;
      const targetX = d.target.y;
      const targetY = d.target.x;
      // Draw a curve between source and target
      return `M${sourceX},${sourceY}C${(sourceX+targetX)/2},${sourceY} ${(sourceX+targetX)/2},${targetY} ${targetX},${targetY}`;
    })
    .attr("fill", "none")
    .attr("stroke", "#fdae6b")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,4");

  // Add Evaluation Results
  // Solutions might have croissant:evaluation with evaluationResults
  solNodes.forEach(d => {
    const evalData = d.data["croissant:evaluation"];
    if (evalData && evalData["croissant:evaluationResults"]) {
      const results = evalData["croissant:evaluationResults"];
      results.forEach((res, i) => {
        const metric = res["croissant:metric"];
        const value = res["croissant:value"];
        
        // Add a node for the result
        const resultNode = nodeLayer.append("g")
          .attr("transform", `translate(${d.y - 40}, ${d.x + 20 + i*15})`);

        resultNode.append("rect")
          .attr("width", 80)
          .attr("height", 12)
          .attr("fill", "#fee391")
          .attr("stroke", "#fe9929")
          .attr("rx", 3);

        resultNode.append("text")
          .attr("x", 40)
          .attr("y", 9)
          .attr("text-anchor", "middle")
          .text(`${metric}: ${value}`)
          .style("font-size", "10px")
          .style("font-family", "sans-serif");

        // Draw a line from solution node to result node
        linkLayer.append("line")
          .attr("x1", d.y)
          .attr("y1", d.x)
          .attr("x2", d.y - 20)
          .attr("y2", d.x + 20 + i*15)
          .attr("stroke", "#fe9929")
          .attr("stroke-width", 1);
      });
    }
  });

  // Option A: Save as PNG
  d3.select("#save-png").on("click", () => {
    const svgNode = d3.select(containerSelector).select("svg").node();
    const svgString = new XMLSerializer().serializeToString(svgNode);
    
    const img = new Image();
    const svgBlob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(svgBlob);
    
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const bbox = svgNode.getBBox();
      
      const scale = 2; // High resolution
      canvas.width = bbox.width * scale;
      canvas.height = bbox.height * scale;
      
      const ctx = canvas.getContext("2d");
      ctx.scale(scale, scale);
      ctx.translate(-bbox.x, -bbox.y);
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      
      const a = document.createElement("a");
      a.download = "croissant_tasks_visualization.png";
      a.href = canvas.toDataURL("image/png");
      a.click();
      
      URL.revokeObjectURL(url);
    };
    
    img.src = url;
  });
}
