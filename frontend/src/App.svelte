<script>
  import { onMount, onDestroy } from 'svelte';
  import HeartbeatGraph from './components/HeartbeatGraph.svelte';
  import BreathGraph from './components/BreathGraph.svelte';
  import DistanceGraph from './components/DistanceGraph.svelte';

  let heartRate = 0;
  let breathRate = 0;
  let distance = 0;
  let connected = false;
  let ws;

  onMount(() => {
    ws = new WebSocket(`ws://localhost:8000/ws`);
    ws.onopen = () => (connected = true);
    ws.onclose = () => (connected = false);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      heartRate = data.heart_rate;
      breathRate = data.breath_rate;
      distance = data.distance;
    };
  });

  onDestroy(() => ws?.close());
</script>

<main>
  <header>
    <h1>🤖 Vital Signs Monitor</h1>
    <span class="status" class:online={connected}>
      {connected ? '● LIVE' : '○ DISCONNECTED'}
    </span>
  </header>

  <div class="stats">
    <div class="stat red">
      <span class="label">Heart Rate</span>
      <span class="value">{heartRate}</span>
      <span class="unit">BPM</span>
    </div>
    <div class="stat blue">
      <span class="label">Breath Rate</span>
      <span class="value">{breathRate}</span>
      <span class="unit">RPM</span>
    </div>
    <div class="stat yellow">
      <span class="label">Distance</span>
      <span class="value">{distance}</span>
      <span class="unit">cm</span>
    </div>
  </div>

  <div class="graphs">
    <HeartbeatGraph {heartRate} />
    <BreathGraph {breathRate} />
    <DistanceGraph {distance} />
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    background: #0a0a0a;
    color: #fff;
    font-family: 'Courier New', monospace;
  }

  main {
    padding: 1.5rem;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #222;
    padding-bottom: 1rem;
  }

  h1 {
    margin: 0;
    font-size: 1.4rem;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  .status {
    font-size: 0.85rem;
    color: #555;
    letter-spacing: 1px;
  }

  .status.online {
    color: #00ff88;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat {
    background: #111;
    border-radius: 8px;
    padding: 1.2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    border: 1px solid #222;
  }

  .stat.red   { border-top: 3px solid #ff4444; }
  .stat.blue  { border-top: 3px solid #4488ff; }
  .stat.yellow { border-top: 3px solid #ffcc00; }

  .label {
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 0.5rem;
  }

  .value {
    font-size: 2.5rem;
    font-weight: bold;
  }

  .stat.red .value   { color: #ff4444; }
  .stat.blue .value  { color: #4488ff; }
  .stat.yellow .value { color: #ffcc00; }

  .unit {
    font-size: 0.75rem;
    color: #555;
    margin-top: 0.25rem;
  }

  .graphs {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
</style>