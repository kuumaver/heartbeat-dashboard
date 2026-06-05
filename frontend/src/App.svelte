<script>
  import { onMount, onDestroy } from 'svelte';
  import LiveView from './components/LiveView.svelte';
  import AdvancedStats from './components/AdvancedStats.svelte';

  let heartRate = 0;
  let breathRate = 0;
  let distance = 0;
  let temperature = 24.5;
  let humidity = 68;
  let targetsCount = 0;
  let gps = { lat: 14.4791, lng: 120.8980, accuracy: 3.2, altitude: 12, speed: 0, heading: 0 };
  let connected = false;
  let ws;

  let history = []; 
  let detectionHistory = [];
  let activeTab = 'live';

  const BASE_LAT = 14.479100;
  const BASE_LNG = 120.898000;
  const METERS_PER_DEGREE = 111320;

  function processGeolocationAndVitals(rLat, rLng, heading, distCm, hr, br, count) {
    const distM = distCm / 100;
    const headingRad = (heading * Math.PI) / 180;
    
    const deltaLat = (distM * Math.cos(headingRad)) / METERS_PER_DEGREE;
    const deltaLng = (distM * Math.sin(headingRad)) / (METERS_PER_DEGREE * Math.cos((rLat * Math.PI) / 180));
    
    const tLat = rLat + deltaLat;
    const tLng = rLng + deltaLng;
    
    const dy = (tLat - BASE_LAT) * METERS_PER_DEGREE;
    const dx = (tLng - BASE_LNG) * METERS_PER_DEGREE * Math.cos((BASE_LAT * Math.PI) / 180);
    const rangeFromBase = Math.sqrt(dx * dx + dy * dy);

    // CRITICAL FIX: Simplified warnings without emojis or bloated labels
    let symptoms = [];
    if (hr > 100) symptoms.push("Tachycardia");
    else if (hr < 60) symptoms.push("Bradycardia");
    if (br > 20) symptoms.push("Tachypnea");
    else if (br < 12) symptoms.push("Bradypnea");
    
    const statusText = symptoms.length === 0 ? "Stable" : symptoms.join(" + ");

    return {
      ts: Date.now(),
      lat: tLat.toFixed(6),
      lng: tLng.toFixed(6),
      range: rangeFromBase.toFixed(1),
      condition: statusText,
      hr,
      br,
      count
    };
  }

  function appendDeduplicatedLog(log) {
    if (detectionHistory.length === 0) {
      detectionHistory = [log];
      return;
    }
    
    const last = detectionHistory[0];
    const matchesLocation = Math.abs(parseFloat(log.range) - parseFloat(last.range)) < 1.5;
    const matchesHeart = Math.abs(log.hr - last.hr) <= 4.0;
    const matchesBreath = Math.abs(log.br - last.br) <= 2.0;
    const matchesCount = log.count === last.count;

    if (matchesLocation && matchesHeart && matchesBreath && matchesCount) {
      return;
    }
    
    detectionHistory = [log, ...detectionHistory].slice(0, 50);
  }

  onMount(() => {
    ws = new WebSocket(`ws://localhost:8001/ws`);
    ws.onopen = () => (connected = true);
    ws.onclose = () => (connected = false);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      heartRate    = data.heart_rate    ?? heartRate;
      breathRate   = data.breath_rate   ?? breathRate;
      distance     = data.distance      ?? distance;
      temperature  = data.temperature   ?? temperature;
      humidity     = data.humidity      ?? humidity;
      targetsCount = data.targets_count ?? targetsCount;
      if (data.gps) gps = { ...gps, ...data.gps };

      history = [...history, {
        ts: Date.now(), heartRate, breathRate, distance, temperature, humidity
      }].slice(-3600);

      if (heartRate > 0) {
        const diagnosticRecord = processGeolocationAndVitals(
          gps.lat, gps.lng, gps.heading, distance, heartRate, breathRate, targetsCount
        );
        appendDeduplicatedLog(diagnosticRecord);
      }
    };
  });

  onDestroy(() => ws?.close());
</script>

<div class="shell">
  <nav class="tab-bar">
    <div class="tab-brand">
      <span class="brand-icon">🤖</span>
      <span class="brand-name">RescueBot Core</span>
    </div>
    <div class="tabs">
      <button class="tab-btn" class:active={activeTab === 'live'} on:click={() => (activeTab = 'live')}>
        📡 Live UI Feed
      </button>
      <button class="tab-btn" class:active={activeTab === 'advanced'} on:click={() => (activeTab = 'advanced')}>
        📊 Advanced Stats
      </button>
      <button class="tab-btn" class:active={activeTab === 'history'} on:click={() => (activeTab = 'history')}>
        📜 Log ({detectionHistory.length})
      </button>
    </div>
    <div class="tab-status">
      <span class="status-dot" class:online={connected}></span>
      <span class="status-text">{connected ? 'LIVESTREAM' : 'OFFLINE'}</span>
    </div>
  </nav>

  <div class="tab-content">
    {#if activeTab === 'live'}
      <LiveView {heartRate} {breathRate} {distance} {temperature} {humidity} {gps} {connected} {targetsCount} {BASE_LAT} {BASE_LNG} />
    {:else if activeTab === 'advanced'}
      <div class="pane-scroll-box">
        <AdvancedStats {history} />
      </div>
    {:else}
      <div class="history-view pane-scroll-box">
        <div class="panel-header">Unique Target Detection Ledger</div>
        <div class="table-container">
          {#if detectionHistory.length === 0}
            <div class="empty-state">No human signatures indexed yet. Searching...</div>
          {:else}
            <table class="log-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Target Count</th>
                  <th>Estimated Coordinates</th>
                  <th>Distance from Command Base</th>
                  <th>Vitals Signature</th>
                  <th>Clinical Condition</th>
                </tr>
              </thead>
              <tbody>
                {#each detectionHistory as log}
                  <tr>
                    <td>{new Date(log.ts).toLocaleTimeString()}</td>
                    <td><span class="badge-count">{log.count} Person(s)</span></td>
                    <td class="geo-txt">{log.lat}°N, {log.lng}°E</td>
                    <td class="yellow">{log.range} meters</td>
                    <td>{log.hr} BPM / {log.br} RPM</td>
                    <td class="condition-cell">{log.condition}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; }
  :global(body) {
    margin: 0; background: #080b10; color: #fff;
    font-family: 'Courier New', 'Consolas', monospace; overflow: hidden; height: 100dvh;
  }
  .shell { display: flex; flex-direction: column; height: 100dvh; overflow: hidden; }
  .tab-bar {
    display: flex; align-items: center; gap: 1rem; padding: 0 1rem;
    background: #0b0f19; border-bottom: 1px solid rgba(0,255,136,0.15); height: 48px; flex-shrink: 0;
  }
  .tab-brand { display: flex; align-items: center; gap: 0.4rem; }
  .brand-name { font-size: 0.8rem; font-weight: bold; letter-spacing: 2px; color: #00ff88; }
  .tabs { display: flex; gap: 0.25rem; flex: 1; }
  .tab-btn {
    background: transparent; border: 1px solid transparent; color: #555;
    font-family: inherit; font-size: 0.75rem; letter-spacing: 1px;
    text-transform: uppercase; padding: 0.35rem 0.85rem; border-radius: 4px; cursor: pointer;
  }
  .tab-btn:hover { color: #aaa; background: rgba(255,255,255,0.04); }
  .tab-btn.active { color: #00ff88; background: rgba(0,255,136,0.08); border-color: rgba(0,255,136,0.2); }
  .tab-status { display: flex; align-items: center; gap: 0.4rem; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #333; }
  .status-dot.online { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
  .status-text { font-size: 0.7rem; color: #666; letter-spacing: 1px; }
  .tab-content { flex: 1; overflow: hidden; position: relative; }

  .pane-scroll-box {
    width: 100%;
    height: 100%;
    overflow-y: auto;
  }

  .history-view { padding: 1.5rem; background: #080b10; }
  .panel-header { font-size: 1rem; letter-spacing: 2px; text-transform: uppercase; color: #00ff88; margin-bottom: 1rem; }
  .table-container { background: #0e121f; border: 1px solid #1a2238; border-radius: 6px; padding: 1rem; }
  .empty-state { padding: 3rem; text-align: center; color: #44567a; font-size: 0.85rem; }
  .log-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: left; }
  .log-table th { padding: 0.75rem; border-bottom: 2px solid #1a2238; color: #44567a; text-transform: uppercase; }
  .log-table td { padding: 0.75rem; border-bottom: 1px solid #141b2d; color: #b2c0d8; }
  .geo-txt { color: #00ff88; }
  .yellow { color: #ffcc00; }
  .badge-count { background: rgba(0,200,255,0.1); border: 1px solid rgba(0,200,255,0.3); padding: 2px 6px; border-radius: 3px; color: #00c8ff; }
  .condition-cell { font-weight: bold; color: #ff4444; }

  @media (min-width: 1920px) and (min-height: 1080px) {
    :global(body) { font-size: 16px; }
    .brand-name { font-size: 1rem; }
    .tab-btn { font-size: 0.9rem; }
    .panel-header { font-size: 1.25rem; }
    .log-table { font-size: 0.9rem; }
  }
</style>