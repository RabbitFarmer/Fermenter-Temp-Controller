<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Fermenter - Chart (Plotly)</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="stylesheet" href="/static/styles.css">
  <style>
    /* local adjustments to ensure chart area spacing is friendly */
    #chart-wrapper { width:100%; margin-top: 6px; background:#fff; border-radius:8px; padding:14px; box-sizing:border-box; }
    #chart { width:100%; height:520px; }
    @media (max-width:900px) { #chart { height:420px; } }
    @media (max-width:600px) { #chart { height:320px; } }
  </style>
  <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
</head>
<body>
  <div class="chart-page">

    <!-- Put the lightweight centered page title here (not the Plotly title) -->
    <div class="chart-page-header-title">Temperature &amp; Gravity — Brew Overview</div>

    <!-- Legend / Controls box (upper-right on wide screens, flows on narrow screens) -->
    <div class="chart-legend-box" id="chartLegendBox" role="region" aria-label="Chart legend and controls">
      <div class="chart-legend-row" style="align-items:flex-start;">
        <div class="chart-legend-left">
          <span class="legend-marker" style="background:#e04b4b"></span> <span>Temp (°F)</span>
          <span style="width:10px"></span>
          <span class="legend-marker" style="background:rgba(42,157,143,0.85)"></span> <span>Gravity (SG)</span>
        </div>
      </div>

      <div class="chart-legend-row">
        <div class="chart-meta-small">Matched: <span id="metaMatched">0</span>  Truncated: <span id="metaTruncated">no</span></div>
        <div class="chart-meta-small">Loaded: <span id="metaLoaded">0</span></div>
      </div>

      <div class="chart-legend-row">
        <div class="controls" aria-label="chart controls">
          <label for="limit" style="font-weight:700; color:var(--ribbon-green); margin-right:6px;">Points:</label>
          <select id="limit" aria-label="Points to fetch">
            <option value="50">50</option>
            <option value="100" selected>100</option>
            <option value="250">250</option>
            <option value="500">500</option>
          </select>
          <button id="reload" aria-label="Reload chart">Reload</button>
        </div>
      </div>
    </div>

    <!-- Chart card -->
    <div id="chart-wrapper" role="main">
      <div id="chart" role="img" aria-label="Temperature and Gravity chart"></div>
    </div>
  </div>

  <!-- server-injected values -->
  <script>
    window.tiltColor = "{{ tilt_color }}";
    window.brewName = "{{ brew_name | e }}";
    window.brewId = "{{ brewid | default('') | e }}";
  </script>

  <script src="/static/js/chart_plotly.js"></script>

  <script>
    // small DOM hookup to keep the legend box values in sync with the plot code
    (function(){
      function setLegendMeta(matched, truncated, loadedTemp, loadedGrav) {
        const mEl = document.getElementById('metaMatched');
        const tEl = document.getElementById('metaTruncated');
        const lEl = document.getElementById('metaLoaded');
        if (mEl) mEl.textContent = matched || 0;
        if (tEl) tEl.textContent = truncated ? 'yes' : 'no';
        if (lEl) lEl.textContent = (loadedTemp || 0) + ' temp points, ' + (loadedGrav || 0) + ' gravity points';
      }

      // Expose helper so chart_plotly.js can call it after loading data
      window._chartLegendUpdate = setLegendMeta;
    })();
  </script>
</body>
</html>