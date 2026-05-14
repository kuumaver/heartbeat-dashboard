<script>
  import { onMount, onDestroy } from 'svelte';
  import LiveView from './components/LiveView.svelte';
  import AdvancedStats from './components/AdvancedStats.svelte';

  let heartRate = 0;
  let breathRate = 0;
  let distance = 0;
  let temperature = 24.5;
  let humidity = 68;
  let gps = { lat: 14.4791, lng: 120.8980, accuracy: 3.2, altitude: 12, speed: 0, heading: 0 };
  let connected = false;
  let ws;

  let history = [];
  let activeTab = 'live';

  onMount(() => {
    ws = new WebSocket(`ws://localhost:8000/ws`);
    ws.onopen = () => (connected = true);
    ws.onclose = () => (connected = false);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      heartRate   = data.heart_rate   ?? heartRate;
      breathRate  = data.breath_rate  ?? breathRate;
      distance    = data.distance     ?? distance;
      temperature = data.temperature  ?? temperature;
      humidity    = data.humidity     ?? humidity;
      if (data.gps) gps = { ...gps, ...data.gps };

      history = [...history, {
        ts: Date.now(),
        heartRate,
        breathRate,
        distance,
        temperature,
        humidity,
      }].slice(-3600);
    };
  });

  onDestroy(() => ws?.close());
</script>

<div class="shell">
  <nav class="tab-bar">
    <div class="tab-brand">
      <span class="brand-icon">🤖</span>
      <span class="brand-name">LifeBot</span>
    </div>
    <div class="tabs">
      <button class="tab-btn" class:active={activeTab === 'live'} on:click={() => (activeTab = 'live')}>
        <span class="tab-icon">📡</span> Live View
      </button>
      <button class="tab-btn" class:active={activeTab === 'advanced'} on:click={() => (activeTab = 'advanced')}>
        <span class="tab-icon">📊</span> Advanced Stats
      </button>
    </div>
    <div class="tab-status">
      <span class="status-dot" class:online={connected}></span>
      <span class="status-text">{connected ? 'LIVE' : 'OFFLINE'}</span>
    </div>
  </nav>

  <div class="tab-content">
    {#if activeTab === 'live'}
      <LiveView {heartRate} {breathRate} {distance} {temperature} {humidity} {gps} {connected} />
    {:else}
      <AdvancedStats {history} />
    {/if}
  </div>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; }
  :global(body) {
    margin: 0;
    background: #080b10;
    color: #fff;
    font-family: 'Courier New', 'Consolas', monospace;
    overflow: hidden;
    height: 100dvh;
  }
  :global(#app) {
    width: 100%;
    max-width: 100%;
    margin: 0;
    border: none;
    min-height: 100dvh;
    text-align: left;
  }
  .shell {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    overflow: hidden;
  }
  .tab-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0 1rem;
    background: rgba(8,11,16,0.97);
    border-bottom: 1px solid rgba(0,255,136,0.15);
    height: 48px;
    flex-shrink: 0;
    z-index: 100;
  }
  .tab-brand { display: flex; align-items: center; gap: 0.4rem; margin-right: 0.5rem; }
  .brand-icon { font-size: 1.1rem; }
  .brand-name { font-size: 0.8rem; font-weight: bold; letter-spacing: 3px; text-transform: uppercase; color: #00ff88; }
  .tabs { display: flex; gap: 0.25rem; flex: 1; }
  .tab-btn {
    background: transparent;
    border: 1px solid transparent;
    color: #555;
    font-family: inherit;
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 0.35rem 0.85rem;
    border-radius: 4px;
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .tab-btn:hover { color: #aaa; background: rgba(255,255,255,0.04); }
  .tab-btn.active { color: #00ff88; background: rgba(0,255,136,0.08); border-color: rgba(0,255,136,0.2); }
  .tab-icon { font-size: 0.9rem; }
  .tab-status { display: flex; align-items: center; gap: 0.4rem; margin-left: auto; }
  .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #333; transition: background 0.3s; }
  .status-dot.online { background: #00ff88; box-shadow: 0 0 6px #00ff88; animation: pulse-dot 2s ease-in-out infinite; }
  @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  .status-text { font-size: 0.7rem; letter-spacing: 2px; color: #555; }
  .status-dot.online + .status-text { color: #00ff88; }
  .tab-content { flex: 1; overflow: hidden; position: relative; }
</style>