<script>
  import { onMount, onDestroy } from 'svelte';
  import Minimap from './MiniMap.svelte';

  export let heartRate = 0;
  export let breathRate = 0;
  export let distance = 0; // Incoming float from the parsed serial channel
  export let temperature = 0;
  export let humidity = 0;
  export let gps = { lat: 0, lng: 0, accuracy: 0, altitude: 0, speed: 0, heading: 0 };
  export let connected = false;
  export let targetsCount = 0;
  
  export let BASE_LAT = 0;
  export let BASE_LNG = 0;

  // Reactive calculations for target tracking matrix
  const METERS_PER_DEGREE = 111320;
  $: headingRad = (gps.heading * Math.PI) / 180;

  // --- UNIT CONVERSION FIX TRACK ---
  // If your ESP32 output line reads 'distance : 150.00' (Centimeters):
  $: distM = distance / 100; 
  
  // NOTE: If your ESP32 output line is ALREADY in meters (e.g., 'distance : 1.50'),
  // uncomment the line below and comment out the one above:
  // $: distM = distance;
  // ----------------------------------
  
  $: tLat = gps.lat + (distM * Math.cos(headingRad)) / METERS_PER_DEGREE;
  $: tLng = gps.lng + (distM * Math.sin(headingRad)) / (METERS_PER_DEGREE * Math.cos((gps.lat * Math.PI) / 180));
  
  $: dy = (tLat - BASE_LAT) * METERS_PER_DEGREE;
  $: dx = (tLng - BASE_LNG) * METERS_PER_DEGREE * Math.cos((BASE_LAT * Math.PI) / 180);
  $: rangeFromBase = Math.sqrt(dx * dx + dy * dy);

  // Clinical condition assessments
  $: isTachycardia = heartRate > 100;
  $: isBradycardia = heartRate > 0 && heartRate < 60;
  $: isTachypnea = breathRate > 20;
  $: isBradypnea = breathRate > 0 && breathRate < 12;

  $: clinicalCondition = (() => {
    let diagnoses = [];
    if (isTachycardia) diagnoses.push("Tachycardia (High Strain Pulse)");
    if (isBradycardia) diagnoses.push("Bradycardia (Weak Pulse)");
    if (isTachypnea) diagnoses.push("Tachypnea (Hyperventilation)");
    if (isBradypnea) diagnoses.push("Bradypnea (Depressed Respiration)");
    return diagnoses.length === 0 ? "Vitals Stable / Conscious" : diagnoses.join(" + ");
  })();

  const ws = new WebSocket('ws://192.168.254.200:8001/ws');

  ws.onopen = () => {
      console.log("Telemetry bridge connected successfully.");
      // Ensure this triggers your export let connected assignment!
      connected = true; 
  };

  ws.onclose = () => {
      console.log("Telemetry bridge disconnected.");
      connected = false;
  };
</script>

<div class="lv-root">
  <div class="lv-root">
    <div class="camera-bg">
      {#if !connected}
        <div class="camera-placeholder">
          <div class="placeholder-grid"></div>
          <div class="placeholder-msg">System Offline — Awaiting Live Telemetry Bridge...</div>
        </div>
      {:else}
        <img 
          src="http://{window.location.hostname}:8001/video_feed" 
          alt="Live RescueBot PiCam Feed" 
          class="camera-video active" 
        />
      {/if}
      <div class="camera-vignette"></div>
    </div>

    <div class="scanlines"></div>

    <div class="overlay-left">
      <Minimap {gps} baseLat={BASE_LAT} baseLng={BASE_LNG} />
      
      <div class="sensor-card gps-card">
        <div class="sc-header"><span class="sc-icon">🛰️</span><span class="sc-title">GPS TELEMETRY</span></div>
        <div class="sc-row"><span class="sc-key">LAT</span><span class="sc-val">{gps.lat.toFixed(5)}°</span></div>
        <div class="sc-row"><span class="sc-key">LNG</span><span class="sc-val">{gps.lng.toFixed(5)}°</span></div>
        <div class="sc-row"><span class="sc-key">HDG</span><span class="sc-val">{gps.heading.toFixed(0)}°</span></div>
        <div class="sc-row"><span class="sc-key">SPD</span><span class="sc-val">{gps.speed.toFixed(1)}m/s</span></div>
      </div>
    </div>

    {#if heartRate > 0}
      <div class="alert-banner-box" class:danger={targetsCount > 1 || isTachycardia || isTachypnea}>
        <div class="alert-flash">🚨 ALARM: SURVIVOR SIGNATURE DETECTED</div>
        <div class="alert-details">
          {#if targetsCount > 1}
            <span class="highlight-warn">⚠️ MULTIPLE PEOPLE DETECTED ({targetsCount} targets inside sensor frame)</span><br>
          {:else}
            <span>💡 Single human bio-signature detected inside the radar scanning zone</span><br>
          {/if}
          🎯 **Computed Target Location:** {tLat.toFixed(6)}°N, {tLng.toFixed(6)}°E <br>
          📏 **Distance from Deployment Station:** <span class="yellow-txt">{rangeFromBase.toFixed(1)} meters</span> away<br>
          🩺 **Clinical Condition Assessment:** <span class="cond-txt">{clinicalCondition}</span>
        </div>
      </div>
    {/if}

    {#if distance < 50.0 && connected}
      <div class="proximity-warning">⚠️ PROXIMITY CRITICAL: OBSTACLE CLOSENESS DETECTED</div>
    {/if}

    <div class="overlay-top">
      <div class="ov-pill">
        <span class="ov-label">SYS</span>
        <span class="ov-val" style="color: {connected ? '#00ff88' : '#ff4444'}">{connected ? 'ONLINE' : 'OFFLINE'}</span>
      </div>
      <div class="ov-pill center-pill">
        <span class="ov-label">🎯 RADAR RANGE</span>
        <span class="ov-val yellow">{distM.toFixed(2)}<span class="ov-unit">m</span></span>
      </div>
      <div class="ov-pill">
        <span class="ov-label">UTC</span>
        <span class="ov-val dim">{new Date().toLocaleTimeString('en-GB')}</span>
      </div>
    </div>

    <div class="overlay-right">
      <div class="vital-card heart-card">
        <div class="vc-icon">❤️</div>
        <div class="vc-label">HEART RATE</div>
        <div class="vc-value" style="color: {heartRate > 0 ? '#ff4444' : '#555'}">{heartRate.toFixed(0)}</div>
        <div class="vc-unit">BPM</div>
      </div>

      <div class="vital-card breath-card">
        <div class="vc-icon">🫁</div>
        <div class="vc-label">BREATH RATE</div>
        <div class="vc-value blue">{breathRate.toFixed(1)}</div>
        <div class="vc-unit">RPM</div>
      </div>

      <div class="sensor-card env-card">
        <div class="sc-header"><span class="sc-icon">🌡️</span><span class="sc-title">ENVIRONMENT</span></div>
        <div class="sc-row"><span class="sc-key">TEMP</span><span class="sc-val">{temperature.toFixed(1)}°C</span></div>
        <div class="sc-row"><span class="sc-key">HUM</span><span class="sc-val blue">{humidity.toFixed(0)}%</span></div>
      </div>
    </div>

    <div class="overlay-bottom">
      <div class="coord-tape">
        <span class="ct-item"><span class="ct-label">BASE</span><span class="ct-val">{BASE_LAT.toFixed(4)}, {BASE_LNG.toFixed(4)}</span></span>
        <span class="ct-sep">|</span>
        <span class="ct-item"><span class="ct-label">ROBOT</span><span class="ct-val">{gps.lat.toFixed(6)}, {gps.lng.toFixed(6)}</span></span>
        <span class="ct-sep">|</span>
        <span class="ct-item"><span class="ct-label">TARGETS COUNT</span><span class="ct-val" style="color: {targetsCount > 0 ? '#00ff88' : '#666'}">{targetsCount} found</span></span>
      </div>
    </div>
  </div>
</div>

<style>
  .lv-root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #020408; }
  .camera-bg { position: absolute; inset: 0; z-index: 1; }
  .camera-video { width: 100%; height: 100%; object-fit: cover; display: block; }
  .camera-placeholder { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: #040712; }
  .placeholder-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(0,255,136,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,136,0.03) 1px, transparent 1px); background-size: 30px 30px; }
  .placeholder-msg { font-size: 0.7rem; letter-spacing: 1.5px; color: #1e3328; text-transform: uppercase; z-index: 1; text-align: center; padding: 1rem; border: 1px dashed rgba(0,255,136,0.1); }
  .camera-vignette { position: absolute; inset: 0; background: radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.8) 100%); pointer-events: none; z-index: 3; }
  .scanlines { position: absolute; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0px, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 4px); pointer-events: none; z-index: 2; }
  
  .alert-banner-box {
    position: absolute; top: 3.5rem; left: 13rem; right: 12rem;
    background: rgba(11,25,16,0.92); border: 2px solid #00ff88; border-radius: 6px;
    padding: 0.75rem; backdrop-filter: blur(8px); z-index: 50; box-shadow: 0 0 15px rgba(0,255,136,0.2);
  }
  .alert-banner-box.danger {
    background: rgba(30,10,14,0.92); border-color: #ff4444; box-shadow: 0 0 15px rgba(255,68,68,0.2);
  }
  .alert-flash { font-weight: bold; font-size: 0.75rem; letter-spacing: 1.5px; color: #00ff88; margin-bottom: 0.3rem; animation: pulse-text 1.5s infinite; }
  .alert-banner-box.danger .alert-flash { color: #ff4444; }
  .alert-details { font-size: 0.68rem; line-height: 1.5; color: #d1dfec; }
  .highlight-warn { color: #ff3b3b; font-weight: bold; }
  .yellow-txt { color: #ffcc00; font-weight: bold; }
  .cond-txt { color: #ff5555; font-weight: bold; }
  
  .proximity-warning {
    position: absolute; bottom: 3rem; left: 13rem; right: 12rem;
    background: rgba(255,102,0,0.2); border: 1px solid #ff6600; border-radius: 4px;
    padding: 0.4rem; text-align: center; color: #ff6600; font-size: 0.65rem; font-weight: bold; letter-spacing: 1px; z-index: 40;
  }

  @keyframes pulse-text { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

  .overlay-top, .overlay-left, .overlay-right, .overlay-bottom { position: absolute; z-index: 10; pointer-events: none; }
  .overlay-top { top: 0.75rem; left: 0.75rem; right: 0.75rem; display: flex; justify-content: space-between; }
  .ov-pill { background: rgba(8,11,16,0.85); border: 1px solid rgba(0,255,136,0.15); border-radius: 4px; padding: 0.3rem 0.6rem; display: flex; gap: 0.5rem; }
  .ov-label { font-size: 0.55rem; color: #44567a; letter-spacing: 1px; }
  .ov-val { font-size: 0.75rem; font-weight: bold; }
  .ov-val.yellow { color: #ffcc00; }
  .ov-val.dim { color: #444; }
  .ov-unit { font-size: 0.55rem; color: #444; margin-left: 2px; }
  
  /* Left Sidebar configuration */
  .overlay-left { 
    top: 4.5rem; 
    left: 0.75rem; 
    height: calc(100vh - 8.5rem); /* Lock the maximum height strictly into view limits */
    display: flex; 
    flex-direction: column; 
    gap: 0.5rem; 
    width: 155px; 
    overflow-y: auto; /* Allow scrolling gracefully inside column if container wraps */
    scrollbar-width: none; /* Hide wide default scrollbars in Firefox */
  }
  .overlay-left::-webkit-scrollbar { display: none; } /* Hide scrollbars in Chrome/Safari */

  /* Right Sidebar layout panel adjustments */
  .overlay-right { 
    top: 3.5rem; 
    right: 0.75rem; 
    height: calc(100vh - 7.5rem);
    display: flex; 
    flex-direction: column; 
    gap: 0.5rem; 
    width: 170px; 
    overflow-y: auto;
    scrollbar-width: none;
  }
  .overlay-right::-webkit-scrollbar { display: none; }

  .sensor-card { 
    background: rgba(8, 11, 16, 0.85); 
    border: 1px solid rgba(0, 255, 136, 0.12); 
    border-radius: 4px; 
    padding: 0.4rem; 
  }
  .sc-header { display: flex; gap: 0.3rem; border-bottom: 1px solid rgba(0,255,136,0.1); padding-bottom: 0.25rem; margin-bottom: 0.35rem; align-items: center; }
  .sc-title { font-size: 0.5rem; letter-spacing: 1.2px; color: #00ff88; }
  .sc-row { display: flex; justify-content: space-between; padding: 0.1rem 0; font-size: 0.6rem; }
  .sc-key { color: #44567a; }
  .sc-val { font-weight: bold; color: #c3cfe2; }
  .sc-val.blue { color: #4488ff; }
  
  .vital-card { background: rgba(8,11,16,0.85); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 0.6rem; display: flex; flex-direction: column; align-items: center; }
  .heart-card { border-top: 2px solid #ff4444; }
  .breath-card { border-top: 2px solid #4488ff; }
  .vc-label { font-size: 0.55rem; color: #44567a; letter-spacing: 1px; margin-bottom: 0.2rem; }
  .vc-value { font-size: 2rem; font-weight: bold; line-height: 1; }
  .vc-value.blue { color: #4488ff; }
  .vc-unit { font-size: 0.55rem; color: #444; }
  .overlay-bottom { bottom: 0; left: 0; right: 0; }
  .coord-tape { background: #0b0f19; border-top: 1px solid rgba(0,255,136,0.12); padding: 0.4rem 1rem; display: flex; gap: 0.8rem; font-size: 0.65rem; }
  .ct-label { color: #44567a; margin-right: 0.25rem; }
  .ct-val { color: #8892b0; }
  .ct-sep { color: #1e293b; }
</style>