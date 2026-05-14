<script>
  import { onMount, afterUpdate } from 'svelte';
  import { Chart } from 'chart.js/auto';

  /**
   * @typedef {{
   *   ts: number;
   *   heartRate: number;
   *   breathRate: number;
   *   distance: number;
   *   temperature: number;
   *   humidity: number;
   * }} Sample
   */

  /** @type {Sample[]} */
  export let history = [];

  // Time interval filter: '1m', '5m', '15m', '1h', 'all'
  let interval = '5m';
  const intervals = [
    { key: '1m',  label: '1 MIN' },
    { key: '5m',  label: '5 MIN' },
    { key: '15m', label: '15 MIN' },
    { key: '1h',  label: '1 HR' },
    { key: 'all', label: 'ALL' },
  ];

  /**
   * @param {'1m'|'5m'|'15m'|'1h'|'all'} key
   * @returns {number}
   */
  function msFor(key) {
    return { '1m': 60e3, '5m': 5*60e3, '15m': 15*60e3, '1h': 3600e3, 'all': Infinity }[key] ?? Infinity;
  }

  $: filtered = history.filter(h => Date.now() - h.ts <= msFor(interval));

  $: timestamps = filtered.map(h => {
    const d = new Date(h.ts);
    return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
  });

  /** @type {HTMLCanvasElement | null} */
  let hrCanvas = null;
  /** @type {HTMLCanvasElement | null} */
  let brCanvas = null;
  /** @type {HTMLCanvasElement | null} */
  let distCanvas = null;
  /** @type {HTMLCanvasElement | null} */
  let tempCanvas = null;
  /** @type {HTMLCanvasElement | null} */
  let humCanvas = null;
  /** @type {{hr?: any, br?: any, dist?: any, temp?: any, hum?: any}} */
  let charts = {};

  /**
   * @param {HTMLCanvasElement | null} canvas
   * @param {string} label
   * @param {string} color
   * @param {number} yMin
   * @param {number} yMax
   * @param {string} unit
   */
  function makeChart(canvas, label, color, yMin, yMax, unit) {
    return new Chart(canvas, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label,
          data: [],
          borderColor: color,
          backgroundColor: color.replace(')', ',0.07)').replace('rgb','rgba'),
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.3,
          fill: true,
        }]
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(8,11,16,0.92)',
            borderColor: color,
            borderWidth: 1,
            titleColor: '#888',
            bodyColor: '#fff',
            callbacks: { label: /** @param {any} ctx */ (ctx) => `${ctx.parsed?.y?.toFixed(1) ?? 0} ${unit}` }
          }
        },
        scales: {
          x: {
            ticks: { color: '#444', font: { size: 9 }, maxTicksLimit: 8 },
            grid: { color: '#111' },
          },
          y: {
            min: yMin, max: yMax,
            ticks: { color: '#555', font: { size: 9 } },
            grid: { color: '#111' },
          }
        }
      }
    });
  }

  onMount(() => {
    charts.hr   = makeChart(hrCanvas,   'Heart Rate',  'rgb(255,68,68)',   40, 120, 'BPM');
    charts.br   = makeChart(brCanvas,   'Breath Rate', 'rgb(68,136,255)',   8,  25, 'RPM');
    charts.dist = makeChart(distCanvas, 'Distance',    'rgb(255,204,0)',    0, 200, 'cm');
    charts.temp = makeChart(tempCanvas, 'Temperature', 'rgb(255,136,0)',   15,  45, '°C');
    charts.hum  = makeChart(humCanvas,  'Humidity',    'rgb(0,200,255)',    0, 100, '%');
  });

  /**
   * @param {Sample[]} data
   * @param {string[]} labels
   */
  function updateCharts(data, labels) {
    const pairs = [
      [charts.hr,   data.map(h => h.heartRate)],
      [charts.br,   data.map(h => h.breathRate)],
      [charts.dist, data.map(h => h.distance)],
      [charts.temp, data.map(h => h.temperature)],
      [charts.hum,  data.map(h => h.humidity)],
    ];
    pairs.forEach(([chart, vals]) => {
      if (!chart) return;
      chart.data.labels = labels;
      chart.data.datasets[0].data = vals;
      chart.update('none');
    });
  }

  $: if (Object.keys(charts).length) updateCharts(filtered, timestamps);

  // Summary stats
  function stats(arr) {
    if (!arr.length) return { min: 0, max: 0, avg: 0, last: 0 };
    const sorted = [...arr].sort((a,b) => a-b);
    return {
      min:  sorted[0].toFixed(1),
      max:  sorted[sorted.length-1].toFixed(1),
      avg:  (arr.reduce((s,v) => s+v, 0) / arr.length).toFixed(1),
      last: arr[arr.length-1].toFixed(1),
    };
  }

  $: hrStats   = stats(filtered.map(h => h.heartRate));
  $: brStats   = stats(filtered.map(h => h.breathRate));
  $: distStats = stats(filtered.map(h => h.distance));
  $: tempStats = stats(filtered.map(h => h.temperature));
  $: humStats  = stats(filtered.map(h => h.humidity));
</script>

<div class="as-root">
  <!-- Header -->
  <div class="as-header">
    <div class="as-title">
      <span class="as-title-icon">📊</span>
      <span>Advanced Stats</span>
      <span class="as-sample-count">{filtered.length} samples</span>
    </div>
    <div class="as-filters">
      <span class="filter-label">INTERVAL</span>
      {#each intervals as iv}
        <button
          class="filter-btn"
          class:active={interval === iv.key}
          on:click={() => (interval = iv.key)}
        >{iv.label}</button>
      {/each}
    </div>
  </div>

  <!-- Summary row -->
  <div class="summary-row">
    <div class="summary-card red">
      <div class="sum-label">❤️ Heart Rate</div>
      <div class="sum-val">{hrStats.last} <span>BPM</span></div>
      <div class="sum-sub">↓{hrStats.min} avg{hrStats.avg} ↑{hrStats.max}</div>
    </div>
    <div class="summary-card blue">
      <div class="sum-label">🫁 Breath Rate</div>
      <div class="sum-val">{brStats.last} <span>RPM</span></div>
      <div class="sum-sub">↓{brStats.min} avg{brStats.avg} ↑{brStats.max}</div>
    </div>
    <div class="summary-card yellow">
      <div class="sum-label">📏 Distance</div>
      <div class="sum-val">{distStats.last} <span>cm</span></div>
      <div class="sum-sub">↓{distStats.min} avg{distStats.avg} ↑{distStats.max}</div>
    </div>
    <div class="summary-card orange">
      <div class="sum-label">🌡️ Temperature</div>
      <div class="sum-val">{tempStats.last} <span>°C</span></div>
      <div class="sum-sub">↓{tempStats.min} avg{tempStats.avg} ↑{tempStats.max}</div>
    </div>
    <div class="summary-card cyan">
      <div class="sum-label">💧 Humidity</div>
      <div class="sum-val">{humStats.last} <span>%</span></div>
      <div class="sum-sub">↓{humStats.min} avg{humStats.avg} ↑{humStats.max}</div>
    </div>
  </div>

  <!-- Charts grid -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-label red-label">❤️ Heart Rate <span>(BPM)</span></div>
      <div class="chart-wrap"><canvas bind:this={hrCanvas}></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-label blue-label">🫁 Breath Rate <span>(RPM)</span></div>
      <div class="chart-wrap"><canvas bind:this={brCanvas}></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-label yellow-label">📏 Distance <span>(cm)</span></div>
      <div class="chart-wrap"><canvas bind:this={distCanvas}></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-label orange-label">🌡️ Temperature <span>(°C)</span></div>
      <div class="chart-wrap"><canvas bind:this={tempCanvas}></canvas></div>
    </div>
    <div class="chart-card wide">
      <div class="chart-label cyan-label">💧 Humidity <span>(%)</span></div>
      <div class="chart-wrap"><canvas bind:this={humCanvas}></canvas></div>
    </div>
  </div>

  {#if filtered.length === 0}
    <div class="no-data">
      <div class="nd-icon">📡</div>
      <div class="nd-msg">No data for selected interval.<br>Connect sensors or wait for data to accumulate.</div>
    </div>
  {/if}
</div>

<style>
  .as-root {
    height: 100%;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: #080b10;
  }

  /* ── Header ── */
  .as-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .as-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    font-weight: bold;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #ccc;
  }
  .as-title-icon { font-size: 1rem; }
  .as-sample-count {
    font-size: 0.6rem;
    color: #333;
    letter-spacing: 1px;
    margin-left: 0.25rem;
  }

  .as-filters {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }

  .filter-label {
    font-size: 0.6rem;
    letter-spacing: 2px;
    color: #444;
    margin-right: 0.25rem;
  }

  .filter-btn {
    background: transparent;
    border: 1px solid #1a1a1a;
    color: #444;
    font-family: inherit;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    padding: 0.3rem 0.6rem;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .filter-btn:hover { color: #888; border-color: #333; }
  .filter-btn.active { color: #00ff88; border-color: rgba(0,255,136,0.35); background: rgba(0,255,136,0.06); }

  /* ── Summary ── */
  .summary-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.5rem;
  }

  .summary-card {
    background: #0e1117;
    border: 1px solid #1a1a1a;
    border-radius: 6px;
    padding: 0.6rem 0.75rem;
    border-top: 2px solid;
  }
  .summary-card.red    { border-top-color: #ff4444; }
  .summary-card.blue   { border-top-color: #4488ff; }
  .summary-card.yellow { border-top-color: #ffcc00; }
  .summary-card.orange { border-top-color: #ff8800; }
  .summary-card.cyan   { border-top-color: #00c8ff; }

  .sum-label { font-size: 0.6rem; letter-spacing: 1.5px; color: #555; text-transform: uppercase; margin-bottom: 0.3rem; }
  .sum-val   { font-size: 1.3rem; font-weight: bold; color: #ccc; line-height: 1; }
  .sum-val span { font-size: 0.6rem; color: #555; }
  .sum-sub   { font-size: 0.58rem; color: #333; letter-spacing: 1px; margin-top: 0.25rem; }

  .summary-card.red    .sum-val { color: #ff4444; }
  .summary-card.blue   .sum-val { color: #4488ff; }
  .summary-card.yellow .sum-val { color: #ffcc00; }
  .summary-card.orange .sum-val { color: #ff8800; }
  .summary-card.cyan   .sum-val { color: #00c8ff; }

  /* ── Charts grid ── */
  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-auto-rows: 180px;
    gap: 0.6rem;
  }

  .chart-card {
    background: #0e1117;
    border: 1px solid #1a1a1a;
    border-radius: 6px;
    padding: 0.6rem;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .chart-card.wide {
    grid-column: span 2;
  }

  .chart-label {
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    flex-shrink: 0;
  }
  .chart-label span { color: #444; margin-left: 0.25rem; }
  .red-label    { color: #ff4444; }
  .blue-label   { color: #4488ff; }
  .yellow-label { color: #ffcc00; }
  .orange-label { color: #ff8800; }
  .cyan-label   { color: #00c8ff; }

  .chart-wrap {
    flex: 1;
    position: relative;
    min-height: 0;
  }
  .chart-wrap canvas { position: absolute; inset: 0; }

  /* ── No data ── */
  .no-data {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 3rem;
    color: #333;
  }
  .nd-icon { font-size: 2.5rem; }
  .nd-msg  { font-size: 0.75rem; letter-spacing: 1px; text-align: center; line-height: 1.8; }

  @media (max-width: 768px) {
    .summary-row { grid-template-columns: repeat(2, 1fr); }
    .summary-row .summary-card:last-child { grid-column: span 2; }
    .charts-grid { grid-template-columns: 1fr; }
    .chart-card.wide { grid-column: span 1; }
  }
</style>