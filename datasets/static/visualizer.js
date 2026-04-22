/**
 * Croissant Visualizer — JavaScript-driven renderer.
 *
 * Fetches the dataset's JSON-LD at runtime (tries metadata-augmented.json
 * first for preview data, falls back to metadata.json) and renders the full
 * UI into #app.
 *
 * External dependencies (loaded via CDN in the HTML shell):
 *   - D3.js v7       — SVG graph rendering
 *   - Prism.js       — JSON syntax highlighting
 *   - Marked.js      — Markdown rendering
 */

(function () {
  'use strict';

  // ── JSON-LD navigation helpers ────────────────────────────────────────

  function getName(entry) {
    return entry.name || entry['@id'] || 'Unnamed';
  }

  function getId(entry) {
    return entry['@id'] || entry.name || '';
  }

  function getType(entry) {
    var t = entry['@type'] || '';
    if (Array.isArray(t)) t = t.join(' ');
    if (t.includes('FileObject') || t === 'sc:FileObject') return 'FileObject';
    if (t.includes('FileSet') || t === 'sc:FileSet') return 'FileSet';
    if (t.includes('RecordSet') || t === 'cr:RecordSet') return 'RecordSet';
    return 'Unknown';
  }

  function getTypeLabel(type) {
    return type === 'FileObject' ? 'File' : type === 'FileSet' ? 'File Set' : type;
  }

  function getTypeIcon(type) {
    return type === 'FileObject' ? '📄' : type === 'FileSet' ? '📁' : '📦';
  }

  function getContainedIn(dist) {
    var ci = dist.containedIn || dist['cr:containedIn'];
    if (!ci) return [];
    var arr = Array.isArray(ci) ? ci : [ci];
    return arr.map(function (c) {
      return typeof c === 'string' ? c : (c['@id'] || '');
    }).filter(Boolean);
  }

  function getEncodingFormats(dist) {
    var ef = dist.encodingFormat || dist['sc:encodingFormat'] || '';
    if (Array.isArray(ef)) return ef;
    return ef ? [ef] : [];
  }

  function getSources(rs) {
    var sources = {};
    var fields = rs.field || rs['cr:field'] || [];
    if (!Array.isArray(fields)) fields = [fields];
    fields.forEach(function (field) {
      var src = field.source || field['cr:source'];
      if (!src) return;
      ['fileObject', 'fileSet', 'distribution', 'cr:fileObject', 'cr:fileSet', 'cr:distribution'].forEach(function (attr) {
        var ref = src[attr];
        if (!ref) return;
        var id = typeof ref === 'string' ? ref : (ref['@id'] || '');
        if (id) sources[id] = true;
      });
    });
    return Object.keys(sources);
  }

  function getFields(rs) {
    var fields = rs.field || rs['cr:field'] || [];
    if (!Array.isArray(fields)) fields = [fields];
    return fields.map(function (f) {
      var dt = f.dataType || f['cr:dataType'] || '';
      if (Array.isArray(dt)) dt = dt.join(', ');
      dt = String(dt);
      if (dt.startsWith("<class '")) dt = dt.replace("<class '", '').replace("'>", '');
      if (dt.includes('schema.org/')) dt = dt.split('/').pop();
      var rawName = getName(f);
      var shortName = rawName.includes('/') ? rawName.split('/').pop() : rawName;
      return {
        name: shortName,
        full_name: rawName,
        description: f.description || f['sc:description'] || '',
        data_type: dt,
      };
    });
  }

  function getExamples(entry) {
    return entry['cr:examples'] || entry.examples || null;
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Module state (populated by init, read by all rendering functions) ───

  var data, distributions, recordSets, distMap, metadataFields, jsonldFilename;
  var EXCLUDED_KEYS, PREFERRED_ORDER, KEY_LABEL_MAP;

  // ── Top-level data extraction (called from init) ──────────────────────

  function extractData(rawData) {
    data = rawData;

    // Determine the filename from @id or a fallback
    jsonldFilename = (data['@id'] || 'metadata.json').split('/').pop() || 'metadata.json';
    if (!jsonldFilename.endsWith('.json')) jsonldFilename = 'metadata.json';

    distributions = data.distribution || [];
    if (!Array.isArray(distributions)) distributions = [distributions];

    recordSets = data.recordSet || [];
    if (!Array.isArray(recordSets)) recordSets = [recordSets];

    // Build lookup: @id or name → distribution entry
    distMap = {};
    distributions.forEach(function (d) {
    if (d['@id']) distMap[d['@id']] = d;
    if (d.name && d.name !== d['@id']) distMap[d.name] = d;
  });

    var EXCLUDED_KEYS = new Set([
    '@context', '@type', '@id', 'name', 'description', 'url', 'version',
    'distribution', 'recordSet', 'cr:recordSet',
    // NOTE: conformsTo is intentionally NOT excluded — it is shown in the table.
  ]);

    var PREFERRED_ORDER = [
    'license', 'citeAs', 'conformsTo', 'datePublished', 'dateCreated',
    'dateModified', 'keywords', 'inLanguage', 'creators', 'creator',
    'publisher', 'sameAs',
  ];

    var KEY_LABEL_MAP = {
    citeAs: 'Cite As',
    conformsTo: 'Conforms To',
    datePublished: 'Date Published',
    dateCreated: 'Date Created',
    dateModified: 'Date Modified',
    inLanguage: 'In Language',
    keywords: 'Keywords',
    license: 'License',
    creators: 'Creators',
    creator: 'Creator',
    publisher: 'Publisher',
    sameAs: 'Same As',
    isLiveDataset: 'Is Live Dataset',
  };

    var mf = [];
    Object.keys(data).forEach(function (key) {
      if (EXCLUDED_KEYS.has(key)) return;
      var val = data[key];
      if (val === null || val === undefined) return;
      var valStr;
      if (Array.isArray(val)) {
        var items = val.map(function (v) {
          return typeof v === 'object' ? (v.name || v['@id'] || JSON.stringify(v)) : String(v);
        }).filter(Boolean);
        valStr = items.join(', ');
      } else if (typeof val === 'object') {
        valStr = val.name || val['@id'] || JSON.stringify(val);
      } else {
        valStr = String(val).trim();
      }
      // Skip empty / null-like values
      if (!valStr || valStr === 'null' || valStr === '[]' || valStr === '{}') return;
      var label = KEY_LABEL_MAP[key] || key.replace(/([A-Z])/g, ' $1').replace(/^./, function (s) { return s.toUpperCase(); });
      mf.push({ key: key, label: label, value: valStr });
    });

    // Sort to match the Python static visualizer's preferred_order:
    // preferred keys first (in declared order), then remaining keys alphabetically.
    mf.sort(function (a, b) {
      var ai = PREFERRED_ORDER.indexOf(a.key);
      var bi = PREFERRED_ORDER.indexOf(b.key);
      if (ai >= 0 && bi >= 0) return ai - bi;
      if (ai >= 0) return -1;
      if (bi >= 0) return 1;
      return a.key.localeCompare(b.key);
    });
    metadataFields = mf;
  }

  // ── Rendering helpers ─────────────────────────────────────────────────

  function plural(n, singular, pluralSuffix) {
    return n + ' ' + singular + (n === 1 ? '' : (pluralSuffix || 's'));
  }

  function renderSVGIcon(path) {
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' + path + '</svg>';
  }

  var HAMBURGER_ICON = renderSVGIcon('<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>');
  var HAMBURGER_ICON_LG = renderSVGIcon('<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>');

  // ── Sidebar ───────────────────────────────────────────────────────────

  function renderSidebar() {
    var resLinks = distributions.map(function (d) {
      var type = getType(d);
      var icon = getTypeIcon(type);
      var name = getName(d);
      return '<li><a href="#res-' + esc(name) + '">' + icon + ' ' + esc(name) + '</a></li>';
    }).join('');

    var rsLinks = recordSets.map(function (rs) {
      var name = getName(rs);
      return '<li><a href="#rs-' + esc(name) + '">📋 ' + esc(name) + '</a></li>';
    }).join('');

    return (
      '<nav class="sidebar" id="sidebar">' +
        '<div class="sidebar-inner">' +
          '<div class="sidebar-header">' +
            '<button class="sidebar-toggle" id="close-sidebar-btn" title="Close sidebar">' + HAMBURGER_ICON + '</button>' +
            '<div class="sidebar-brand">🥐 Croissant Visualizer</div>' +
          '</div>' +
          '<h4>Dataset</h4>' +
          '<ul>' +
            '<li><a href="#top">Overview</a></li>' +
            '<li><a href="#metadata">Metadata</a></li>' +
          '</ul>' +
          (distributions.length ? '<h4>Resources</h4><ul>' + resLinks + '</ul>' : '') +
          (recordSets.length ? '<h4>Record Sets</h4><ul>' + rsLinks + '</ul>' : '') +
        '</div>' +
      '</nav>'
    );
  }

  // ── Hero header ───────────────────────────────────────────────────────

  function renderHero() {
    var name = data.name || 'Untitled Dataset';
    var description = data.description || '';
    var url = data.url || data['sc:url'] || '';
    var version = data.version || '';

    var badges = '';
    if (version) badges += '<span class="hero-badge">🏷️ v' + esc(version) + '</span>';
    if (url) badges += '<span class="hero-badge">🔗 <a href="' + esc(url) + '" target="_blank">Dataset URL</a></span>';
    badges += '<span class="hero-badge">📦 ' + plural(distributions.length, 'resource') + '</span>';
    badges += '<span class="hero-badge">📋 ' + plural(recordSets.length, 'record set') + '</span>';
    badges += '<span class="hero-badge" style="cursor:pointer" id="open-modal-btn" title="View full JSON-LD source">&lt;/&gt; Source</span>';

    return (
      '<div class="hero" id="top">' +
        '<h1>🥐 ' + esc(name) + '</h1>' +
        (description ? '<div class="description markdown" data-raw="' + esc(description) + '"></div>' : '') +
        '<div class="hero-meta">' + badges + '</div>' +
      '</div>'
    );
  }

  // ── Metadata table ────────────────────────────────────────────────────

  function renderMetadata() {
    if (!metadataFields.length) return '';

    var rows = metadataFields.map(function (f) {
      var snippet = data[f.key];
      var snippetJson = (snippet !== null && snippet !== undefined)
        ? JSON.stringify({ [f.key]: snippet }, null, 2) : '';
      var jsonldToggle = snippetJson
        ? '<button class="jsonld-toggle" title="View JSON-LD">&lt;/&gt;</button>' : '';
      var jsonldPanel = snippetJson
        ? '<div class="jsonld-panel"><pre class="language-json"><code class="language-json">' + esc(snippetJson) + '</code></pre></div>' : '';

      var displayVal;
      if (f.key === 'citeAs') {
        displayVal = '<div class="cite-block">' + esc(f.value) + '</div>';
      } else if (f.value.startsWith('http')) {
        displayVal = '<a href="' + esc(f.value) + '" target="_blank">' + esc(f.value) + '</a>';
      } else {
        displayVal = esc(f.value);
      }

      return (
        '<tr>' +
          '<td class="kv-key" title="' + esc(f.key) + '">' + esc(f.label) + '</td>' +
          '<td class="kv-val">' +
            '<span style="float:right;margin-left:12px">' + jsonldToggle + '</span>' +
            displayVal +
            jsonldPanel +
          '</td>' +
        '</tr>'
      );
    }).join('');

    return (
      '<div class="card" id="metadata">' +
        '<div class="card-header"><span class="icon">ℹ️</span><h2>Metadata</h2></div>' +
        '<table class="kv-table">' + rows + '</table>' +
      '</div>'
    );
  }

  // ── Resource cards ────────────────────────────────────────────────────

  function renderResourceCard(dist) {
    var type = getType(dist);
    var typeLabel = getTypeLabel(type);
    var typeIcon = getTypeIcon(type);
    var name = getName(dist);
    var description = dist.description || dist['sc:description'] || '';
    var encFmts = getEncodingFormats(dist);
    var encStr = encFmts.join(', ');
    var examples = getExamples(dist);
    var snippetJson = JSON.stringify(
      Object.fromEntries(Object.entries(dist).filter(function (kv) { return kv[0] !== 'cr:examples' && kv[0] !== 'examples'; })),
      null, 2
    );

    // Build preview block from cr:examples
    var previewBlock = '';
    if (examples) {
      if (examples.file_list && examples.file_list.length) {
        var fileItems = examples.file_list.map(function (f) {
          return '<li>' + esc(f) + '</li>';
        }).join('');
        var moreMsg = (examples.file_count > examples.file_list.length)
          ? '<div class="file-listing-more">… and ' + (examples.file_count - examples.file_list.length) + ' more</div>'
          : '';
        previewBlock = (
          '<div class="file-listing">' +
            '<div class="file-listing-header">📂 ' + plural(examples.file_count, 'file') + '</div>' +
            '<ul class="file-list">' + fileItems + '</ul>' +
            moreMsg +
          '</div>'
        );
      } else if (examples.text_preview) {
        previewBlock = '<pre class="preview">' + esc(examples.text_preview) + '</pre>';
      } else if (examples.includes && examples.includes.length) {
        previewBlock = '<pre class="preview">Pattern: ' + esc(examples.includes.join(', ')) + '</pre>';
      }
    }

    var hasPreview = !!previewBlock;
    var actions = '';
    if (hasPreview) actions += '<button class="preview-toggle" title="View Preview">🔍</button>';
    actions += '<button class="jsonld-toggle" title="View JSON-LD">&lt;/&gt;</button>';

    return (
      '<div class="resource-card" id="res-' + esc(name) + '" data-type="' + esc(type) + '">' +
        '<div class="rc-header">' +
          '<span class="rc-icon">' + typeIcon + '</span>' +
          '<span class="rc-name">' + esc(name) + '</span>' +
          '<div class="header-actions">' + actions + '</div>' +
        '</div>' +
        '<span class="rc-type">' + esc(typeLabel) + '</span>' +
        (encStr ? ' <span class="type-badge">' + esc(encStr) + '</span>' : '') +
        (description ? '<div class="rc-desc markdown" data-raw="' + esc(description) + '"></div>' : '') +
        previewBlock +
        '<div class="jsonld-panel"><pre class="language-json"><code class="language-json">' + esc(snippetJson) + '</code></pre></div>' +
      '</div>'
    );
  }

  function renderResources() {
    if (!distributions.length) return '';
    var cards = distributions.map(renderResourceCard).join('');
    return (
      '<div class="card" id="resources">' +
        '<div class="card-header"><span class="icon">📦</span><h2>Resources</h2></div>' +
        '<div class="svg-graph-wrap" id="svg-graph-wrap"><div id="svg-graph"></div></div>' +
        '<div class="resource-list">' + cards + '</div>' +
      '</div>'
    );
  }

  // ── Record set sections ───────────────────────────────────────────────

  function renderRecordSetSection(rs, isLast) {
    var name = getName(rs);
    var description = rs.description || rs['sc:description'] || '';
    var fields = getFields(rs);
    var examples = getExamples(rs);
    var snippetJson = JSON.stringify(
      Object.fromEntries(Object.entries(rs).filter(function (kv) { return kv[0] !== 'cr:examples' && kv[0] !== 'examples'; })),
      null, 2
    );

    var fieldRows = fields.map(function (f) {
      return (
        '<tr>' +
          '<td><strong>' + esc(f.name) + '</strong></td>' +
          '<td><span class="type-badge">' + esc(f.data_type) + '</span></td>' +
          '<td>' + esc(f.description) + '</td>' +
        '</tr>'
      );
    }).join('');

    // Data preview from cr:examples
    var previewBlock = '';
    if (examples && examples.columns && examples.rows && examples.rows.length) {
      var headerCells = examples.columns.map(function (c) { return '<th>' + esc(c) + '</th>'; }).join('');
      var dataRows = examples.rows.map(function (row) {
        var cells = row.map(function (cell) {
          var s = String(cell);
          var display = s.length > 80 ? s.slice(0, 80) + '…' : s;
          return '<td title="' + esc(s) + '">' + esc(display) + '</td>';
        }).join('');
        return '<tr>' + cells + '</tr>';
      }).join('');
      previewBlock = (
        '<div class="rs-preview">' +
          '<div class="rs-preview-label">🔍 Data preview</div>' +
          '<div class="table-wrap">' +
            '<table class="preview-table">' +
              '<thead><tr>' + headerCells + '</tr></thead>' +
              '<tbody>' + dataRows + '</tbody>' +
            '</table>' +
          '</div>' +
        '</div>'
      );
    }

    var hasPreview = !!previewBlock;
    var actions = '';
    if (hasPreview) actions += '<button class="preview-toggle" title="View Preview">🔍</button>';
    actions += '<button class="jsonld-toggle" title="View JSON-LD">&lt;/&gt;</button>';

    return (
      '<div class="rs-section" id="rs-' + esc(name) + '">' +
        '<div class="rs-header">' +
          '<h3>' + esc(name) + '</h3>' +
          '<div class="header-actions">' + actions + '</div>' +
        '</div>' +
        (description ? '<div class="rs-desc markdown" data-raw="' + esc(description) + '"></div>' : '') +
        '<div class="table-wrap">' +
          '<table>' +
            '<thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>' +
            '<tbody>' + fieldRows + '</tbody>' +
          '</table>' +
        '</div>' +
        previewBlock +
        '<div class="jsonld-panel"><pre class="language-json"><code class="language-json">' + esc(snippetJson) + '</code></pre></div>' +
      '</div>' +
      (!isLast ? '<hr class="rs-divider">' : '')
    );
  }

  function renderRecordSets() {
    if (!recordSets.length) return '';
    var sections = recordSets.map(function (rs, i) {
      return renderRecordSetSection(rs, i === recordSets.length - 1);
    }).join('');
    return (
      '<div class="card card--green" id="recordsets">' +
        '<div class="card-header"><span class="icon">📋</span><h2>Record Sets</h2></div>' +
        sections +
      '</div>'
    );
  }

  // ── Full JSON-LD Modal ────────────────────────────────────────────────

  function renderModal() {
    var fullJson = JSON.stringify(data, null, 2);
    return (
      '<div class="modal-overlay" id="jsonld-modal">' +
        '<div class="modal">' +
          '<div class="modal-header">' +
            '<h2>🥐 ' + esc(jsonldFilename) + '</h2>' +
            '<div class="modal-actions">' +
              '<button class="modal-btn" id="copy-jsonld-btn">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>' +
                ' Copy' +
              '</button>' +
              '<button class="modal-btn" id="download-jsonld-btn">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>' +
                ' Download' +
              '</button>' +
            '</div>' +
            '<button class="modal-close" id="close-modal-btn" title="Close">✕</button>' +
          '</div>' +
          '<div class="modal-body">' +
            '<pre class="language-json"><code class="language-json" id="full-jsonld-code">' + esc(fullJson) + '</code></pre>' +
          '</div>' +
        '</div>' +
      '</div>'
    );
  }

  // ── Full app HTML ─────────────────────────────────────────────────────

  function renderApp() {
    return (
      '<div class="app">' +
        renderSidebar() +
        '<div class="main">' +
          '<button class="sidebar-open-btn" id="open-sidebar-btn" title="Open sidebar">' + HAMBURGER_ICON_LG + '</button>' +
          renderHero() +
          renderMetadata() +
          renderResources() +
          renderRecordSets() +
          '<div class="footer">Generated by 🥐 <strong>Croissant Visualizer</strong> · <a href="https://mlcommons.org/croissant" target="_blank">mlcommons.org/croissant</a></div>' +
        '</div>' +
      '</div>' +
      renderModal()
    );
  }

  // ── Mount + UI (called after data is loaded) ──────────────────────────

  function init(rawData) {
    extractData(rawData);
    document.getElementById('app').innerHTML = renderApp();
    document.title = (data.name || 'Dataset') + ' — Croissant Visualizer';

  // ── Markdown rendering ────────────────────────────────────────────────

  document.querySelectorAll('.markdown[data-raw]').forEach(function (el) {
    var raw = el.getAttribute('data-raw');
    if (raw && typeof marked !== 'undefined') {
      el.innerHTML = marked.parse(raw);
    }
  });

  // ── Prism syntax highlighting ─────────────────────────────────────────
  // (Defer so that panels that start hidden still get highlighted on first open)

  // ── UI Logic ─────────────────────────────────────────────────────────

  // Sidebar collapse
  document.getElementById('close-sidebar-btn').addEventListener('click', function () {
    document.getElementById('sidebar').classList.add('collapsed');
  });
  document.getElementById('open-sidebar-btn').addEventListener('click', function () {
    document.getElementById('sidebar').classList.remove('collapsed');
  });

  // JSON-LD panel toggles (delegated)
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.jsonld-toggle');
    if (!btn) return;
    var container = btn.closest('.rs-section, .resource-card, tr, .card');
    var panel = container ? container.querySelector('.jsonld-panel') : null;
    if (!panel) {
      var row = btn.closest('tr');
      if (row) panel = row.nextElementSibling && row.nextElementSibling.querySelector
        ? row.querySelector('.jsonld-panel') : null;
    }
    if (panel) {
      panel.classList.toggle('open');
      btn.classList.toggle('active');
      if (panel.classList.contains('open') && !panel.dataset.highlighted) {
        var code = panel.querySelector('code');
        if (code && typeof Prism !== 'undefined') Prism.highlightElement(code);
        panel.dataset.highlighted = 'true';
      }
      if (panel.classList.contains('open')) {
        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  });

  // Preview toggles (delegated)
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.preview-toggle');
    if (!btn) return;
    var container = btn.closest('.rs-section, .resource-card');
    var panel = container ? container.querySelector('.rs-preview, .file-listing, pre.preview') : null;
    if (panel) {
      panel.classList.toggle('open');
      btn.classList.toggle('active');
      if (panel.classList.contains('open')) {
        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  });

  // Modal open
  document.getElementById('open-modal-btn').addEventListener('click', openModal);

  function openModal() {
    var modal = document.getElementById('jsonld-modal');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    var code = document.getElementById('full-jsonld-code');
    if (code && typeof Prism !== 'undefined' && !code.dataset.highlighted) {
      Prism.highlightElement(code);
      code.dataset.highlighted = 'true';
    }
  }

  function closeModal() {
    document.getElementById('jsonld-modal').classList.remove('open');
    document.body.style.overflow = '';
  }

  document.getElementById('close-modal-btn').addEventListener('click', closeModal);
  document.getElementById('jsonld-modal').addEventListener('click', function (e) {
    if (e.target === this) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  // Copy JSON-LD
  document.getElementById('copy-jsonld-btn').addEventListener('click', function () {
    var code = document.getElementById('full-jsonld-code');
    navigator.clipboard.writeText(code.textContent).then(function () {
      var btn = document.getElementById('copy-jsonld-btn');
      btn.classList.add('copied');
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
      setTimeout(function () {
        btn.classList.remove('copied');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy';
      }, 2000);
    });
  });

  // Download JSON-LD
  document.getElementById('download-jsonld-btn').addEventListener('click', function () {
    var code = document.getElementById('full-jsonld-code');
    var blob = new Blob([code.textContent], { type: 'application/ld+json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = jsonldFilename;
    a.click();
    URL.revokeObjectURL(a.href);
  });

  // ── D3 SVG Dependency Graph ───────────────────────────────────────────
  //
  // Direct port of _build_svg_graph() from visualize.py.
  // Same two-column layout: resources (left) → recordsets (right).
  // D3 is used for SVG element creation and cubic bezier path generation.

  function renderGraph() {
    if (!distributions.length && !recordSets.length) return;

    // Layout constants (must match Python)
    var NODE_W = 180, NODE_H = 52;
    var COL_GAP = 220;
    var ROW_GAP = 24;
    var PAD_X = 60, PAD_Y = 24;
    var LEFT_X = PAD_X;
    var RIGHT_X = PAD_X + NODE_W + COL_GAP;

    // Colour palette (must match Python)
    var COLORS = {
      FileObject: { fill: '#fff7ed', stroke: '#f97316', iconBg: '#fed7aa', icon: '📄' },
      FileSet:    { fill: '#eef2ff', stroke: '#6366f1', iconBg: '#c7d2fe', icon: '📁' },
      RecordSet:  { fill: '#f0fdf4', stroke: '#22c55e', iconBg: '#bbf7d0', icon: '📋' },
    };

    // Position each resource node: name → {cx, cy}
    var resPositions = {};
    distributions.forEach(function (d, i) {
      var cy = PAD_Y + i * (NODE_H + ROW_GAP) + NODE_H / 2;
      var pos = { cx: LEFT_X + NODE_W / 2, cy: cy };
      var name = getName(d);
      resPositions[name] = pos;
      var id = getId(d);
      if (id && id !== name) resPositions[id] = pos;
    });

    // Position each recordset node: name → {cx, cy}
    var rsPositions = {};
    recordSets.forEach(function (rs, i) {
      var cy = PAD_Y + i * (NODE_H + ROW_GAP) + NODE_H / 2;
      rsPositions[getName(rs)] = { cx: RIGHT_X + NODE_W / 2, cy: cy };
    });

    // SVG dimensions
    var leftH = distributions.length ? distributions.length * (NODE_H + ROW_GAP) - ROW_GAP : 0;
    var rightH = recordSets.length ? recordSets.length * (NODE_H + ROW_GAP) - ROW_GAP : 0;
    var totalH = Math.max(leftH, rightH) + 2 * PAD_Y;
    var totalW = recordSets.length ? RIGHT_X + NODE_W + PAD_X : LEFT_X + NODE_W + PAD_X;

    var container = document.getElementById('svg-graph');
    if (!container) return;

    var svg = d3.select(container)
      .append('svg')
      .attr('xmlns', 'http://www.w3.org/2000/svg')
      .attr('xmlns:xlink', 'http://www.w3.org/1999/xlink')
      .attr('viewBox', '0 0 ' + totalW + ' ' + totalH)
      .attr('width', totalW)
      .attr('height', totalH)
      .style('max-width', '100%')
      .style('font-family', 'Inter, sans-serif');

    // Arrow-head markers
    var defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'arr').attr('markerWidth', 8).attr('markerHeight', 8)
      .attr('refX', 6).attr('refY', 3).attr('orient', 'auto')
      .append('path').attr('d', 'M0,0 L0,6 L8,3 z').attr('fill', '#94a3b8');
    defs.append('marker')
      .attr('id', 'arr2').attr('markerWidth', 8).attr('markerHeight', 8)
      .attr('refX', 6).attr('refY', 3).attr('orient', 'auto')
      .append('path').attr('d', 'M0,0 L0,6 L8,3 z').attr('fill', '#c7d2fe');

    // Column header labels
    if (distributions.length) {
      svg.append('text')
        .attr('x', LEFT_X + NODE_W / 2).attr('y', 10)
        .attr('text-anchor', 'middle').attr('font-size', 10)
        .attr('font-weight', 600).attr('fill', '#94a3b8')
        .attr('letter-spacing', '0.06em')
        .text('RESOURCES');
    }
    if (recordSets.length) {
      svg.append('text')
        .attr('x', RIGHT_X + NODE_W / 2).attr('y', 10)
        .attr('text-anchor', 'middle').attr('font-size', 10)
        .attr('font-weight', 600).attr('fill', '#94a3b8')
        .attr('letter-spacing', '0.06em')
        .text('RECORD SETS');
    }

    // Helper: draw a cubic bezier edge between two points
    function drawEdge(x1, y1, x2, y2, stroke, dash, marker) {
      var mx = (x1 + x2) / 2;
      svg.append('path')
        .attr('d', 'M' + x1 + ',' + y1 + ' C' + mx + ',' + y1 + ' ' + mx + ',' + y2 + ' ' + x2 + ',' + y2)
        .attr('fill', 'none')
        .attr('stroke', stroke || '#94a3b8')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', dash || null)
        .attr('marker-end', 'url(#' + (marker || 'arr') + ')')
        .attr('opacity', 0.7);
    }

    // Resource → resource (contained_in) arced edges on left side
    distributions.forEach(function (d) {
      var childName = getName(d);
      var childPos = resPositions[childName];
      if (!childPos) return;
      getContainedIn(d).forEach(function (parentRef) {
        var parentPos = resPositions[parentRef];
        if (!parentPos) return;
        var xStart = parentPos.cx - NODE_W / 2;
        var yStart = parentPos.cy;
        var xEnd = childPos.cx - NODE_W / 2;
        var yEnd = childPos.cy;
        var ctrlX = xStart - 40;

        svg.append('path')
          .attr('d', 'M' + xStart + ',' + yStart + ' C' + ctrlX + ',' + yStart + ' ' + ctrlX + ',' + yEnd + ' ' + xEnd + ',' + yEnd)
          .attr('fill', 'none')
          .attr('stroke', '#c7d2fe')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '5,3')
          .attr('marker-end', 'url(#arr2)')
          .attr('opacity', 0.85);
      });
    });

    // RecordSet → resource edges
    recordSets.forEach(function (rs) {
      var rsName = getName(rs);
      var rsPos = rsPositions[rsName];
      if (!rsPos) return;
      getSources(rs).forEach(function (srcRef) {
        var rPos = resPositions[srcRef];
        if (!rPos) return;
        drawEdge(rPos.cx + NODE_W / 2, rPos.cy, rsPos.cx - NODE_W / 2, rsPos.cy, '#94a3b8', null, 'arr');
      });
    });

    // Helper: draw a single node (rect + icon pill + label text)
    function drawNode(cx, cy, label, nodeType, href) {
      var c = COLORS[nodeType] || COLORS.RecordSet;
      var x = cx - NODE_W / 2;
      var y = cy - NODE_H / 2;
      var shortLabel = label.length <= 22 ? label : label.slice(0, 20) + '…';

      var g = svg.append('a')
        .attr('xlink:href', href)
        .attr('href', href);

      g.append('title').text(label);

      g.append('rect')
        .attr('x', x).attr('y', y)
        .attr('width', NODE_W).attr('height', NODE_H)
        .attr('rx', 8)
        .attr('fill', c.fill).attr('stroke', c.stroke).attr('stroke-width', 1.5);

      // Icon pill
      g.append('rect')
        .attr('x', x + 8).attr('y', cy - 12)
        .attr('width', 24).attr('height', 24)
        .attr('rx', 5).attr('fill', c.iconBg);

      g.append('text')
        .attr('x', x + 20).attr('y', cy + 5)
        .attr('text-anchor', 'middle').attr('font-size', 13)
        .text(c.icon);

      // Label
      g.append('text')
        .attr('x', x + 40).attr('y', cy + 4)
        .attr('font-size', 12).attr('font-weight', 500)
        .attr('fill', '#1e293b').attr('dominant-baseline', 'middle')
        .text(shortLabel);
    }

    // Draw resource nodes
    distributions.forEach(function (d) {
      var name = getName(d);
      var type = getType(d);
      var pos = resPositions[name];
      if (pos) drawNode(pos.cx, pos.cy, name, type, '#res-' + name);
    });

    // Draw recordset nodes
    recordSets.forEach(function (rs) {
      var name = getName(rs);
      var pos = rsPositions[name];
      if (pos) drawNode(pos.cx, pos.cy, name, 'RecordSet', '#rs-' + name);
    });
  }

    renderGraph();

    // Hide the graph container if graph is empty
    var graphWrap = document.getElementById('svg-graph-wrap');
    if (graphWrap && !graphWrap.querySelector('svg')) {
      graphWrap.style.display = 'none';
    }
  } // end init()

  // ── Bootstrap: prefer pre-loaded data, fall back to fetch ────────────
  //
  // visualizer.html includes <script src="./metadata-augmented.js"> before
  // this file. That script sets window.__CROISSANT_DATA__ synchronously and
  // works from file:// (no CORS). If the variable is already populated we
  // call init() directly without any network request.
  //
  // If window.__CROISSANT_DATA__ is not set (e.g. the page is served from an
  // HTTP server without the Python-generated side-file), we fall back to
  // fetching metadata.json directly. This won't have cr:examples preview
  // data but will render the core dataset information.

  if (window.__CROISSANT_DATA__) {
    init(window.__CROISSANT_DATA__);
  } else {
    fetch('./metadata.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(init)
      .catch(function (err) {
        document.getElementById('app').innerHTML =
          '<p style="padding:2rem;font-family:sans-serif;color:#ef4444">' +
          '\u26a0\ufe0f Could not load dataset metadata.<br>' +
          'Make sure <code>metadata-augmented.js</code> or <code>metadata.json</code> ' +
          'is in the same directory as this page.<br>' +
          '<small style="color:#6b7280">' + esc(String(err)) + '</small></p>';
      });
  }

})();
