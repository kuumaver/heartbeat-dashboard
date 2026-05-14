<script>
  import { onMount } from 'svelte';

  export let gps = { lat: 0, lng: 0 };
  export let baseLat = 0;
  export let baseLng = 0;

  let canvas;
  let ctx;
  let path = []; // Stores {x, y} coordinates
  const SCALE = 10; // 1 meter = 10 pixels
  const OFFSET = 150; // Center the base station in the 300px canvas

  // Convert GPS to local XY pixels relative to Base
  $: if (gps.lat && baseLat && ctx) {
    const METERS_PER_DEGREE = 111320;
    const y = (gps.lat - baseLat) * METERS_PER_DEGREE;
    const x = (gps.lng - baseLng) * METERS_PER_DEGREE * Math.cos((baseLat * Math.PI) / 180);
    
    const newPoint = { x: x * SCALE + OFFSET, y: OFFSET - (y * SCALE) };
    
    // Only add point if the robot moved significantly (e.g., > 0.5px)
    if (path.length === 0 || Math.hypot(newPoint.x - path[path.length-1].x, newPoint.y - path[path.length-1].y) > 0.5) {
      path = [...path, newPoint].slice(-500); // Keep last 500 points
      draw();
    }
  }

  function draw() {
    ctx.clearRect(0, 0, 300, 300);
    
    // Draw Grid
    ctx.strokeStyle = '#1a2238';
    ctx.lineWidth = 1;
    for(let i=0; i<=300; i+=30) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 300); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(300, i); ctx.stroke();
    }

    // Draw Base Station (Rescue HQ)
    ctx.fillStyle = '#ffcc00';
    ctx.beginPath();
    ctx.arc(OFFSET, OFFSET, 4, 0, Math.PI * 2);
    ctx.fill();

    // Draw Robot Path
    if (path.length > 1) {
      ctx.strokeStyle = '#00ff88';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]); // Dashed line for path
      ctx.beginPath();
      ctx.moveTo(path[0].x, path[0].y);
      for (let p of path) ctx.lineTo(p.x, p.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw Current Robot Position
    if (path.length > 0) {
      const current = path[path.length - 1];
      ctx.fillStyle = '#00ff88';
      ctx.shadowBlur = 10;
      ctx.shadowColor = '#00ff88';
      ctx.beginPath();
      ctx.arc(current.x, current.y, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  onMount(() => {
    ctx = canvas.getContext('2d');
    draw();
  });
</script>

<div class="minimap-container">
  <div class="map-label">📍 EXPLORATION LOG</div>
  <canvas bind:this={canvas} width="300" height="300"></canvas>
  <div class="map-footer">Scale: 1sq = 3m</div>
</div>

<style>
  .minimap-container {
    background: rgba(8, 11, 16, 0.9);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 10px;
    width: fit-content;
  }
  .map-label {
    font-size: 0.6rem;
    color: #00ff88;
    margin-bottom: 5px;
    letter-spacing: 1px;
  }
  canvas {
    background: #040712;
    border-radius: 4px;
    display: block;
  }
  .map-footer {
    font-size: 0.5rem;
    color: #44567a;
    margin-top: 5px;
    text-align: right;
  }
</style>