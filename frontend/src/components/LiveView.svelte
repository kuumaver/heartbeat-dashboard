<script>
  import { onMount, onDestroy } from 'svelte';

  export let heartRate = 0;
  export let breathRate = 0;
  export let distance = 0;
  
  export let gps = { lat: 0, lng: 0, accuracy: 0, altitude: 0, speed: 0, heading: 0 };
  export let connected = false;
  export let targetsCount = 0;
  export let detectionHistory = [];
  
  export let BASE_LAT = 0;
  export let BASE_LNG = 0;

  const METERS_PER_DEGREE = 111320;
  $: headingRad = (gps.heading * Math.PI) / 180;
  $: distM = distance / 100;
  
  $: tLat = gps.lat + (distM * Math.cos(headingRad)) / METERS_PER_DEGREE;
  $: tLng = gps.lng + (distM * Math.sin(headingRad)) / (METERS_PER_DEGREE * Math.cos((gps.lat * Math.PI) / 180));
  $: dy = (tLat - BASE_LAT) * METERS_PER_DEGREE;
  $: dx = (tLng - BASE_LNG) * METERS_PER_DEGREE * Math.cos((BASE_LAT * Math.PI) / 180);
  $: rangeFromBase = Math.sqrt(dx * dx + dy * dy);

  $: isTachycardia = heartRate > 100;
  $: isBradycardia = heartRate > 0 && heartRate < 60;
  $: isTachypnea = breathRate > 20;
  $: isBradypnea = breathRate > 0 && breathRate < 12;

  $: clinicalCondition = (() => {
    let diagnoses = [];
    if (isTachycardia) diagnoses.push("Tachycardia");
    if (isBradycardia) diagnoses.push("Bradycardia");
    if (isTachypnea) diagnoses.push("Tachypnea");
    if (isBradypnea) diagnoses.push("Bradypnea");
    return diagnoses.length === 0 ? "Stable" : diagnoses.join(" + ");
  })();

  $: alertState = (targetsCount > 0 && heartRate > 0) ? 'confirmed' :
                  (targetsCount === 0 && heartRate > 0) ? 'possible' :
                  (targetsCount > 0 && heartRate === 0) ? 'nopulse' : 'none';
</script>

<div class="lv-root">
  <div class="video-ratio-container">
    <div class="camera-bg">
      {#if !connected}
        <div class="camera-placeholder">
          <div class="placeholder-grid"></div>
          <div class="placeholder-msg">System Offline — Awaiting Live Telemetry...</div>
        </div>
      {:else}
        <img 
          src="http://{window.location.hostname}:8001/video_feed" 
          alt="Live Video Feed" 
          class="camera-video active" 
        />
      {/if}
      <div class="camera-vignette"></div>
    </div>
    <div class="scanlines"></div>
  </div>

  <div class="overlay-top">
    <div class="ov-pill">
      <span class="ov-label">SYS</span>
      <span class="ov-val" style="color: {connected ? '#00ff88' : '#ff4444'}">{connected ? 'ONLINE' : 'OFFLINE'}</span>
    </div>
    <div class="ov-pill center-pill">
      <span class="ov-label">RADAR RANGE</span>
      <span class="ov-val yellow">{distM.toFixed(2)}<span class="ov-unit">m</span></span>
    </div>
    <div class="ov-pill">
      <span class="ov-label">UTC</span>
      <span class="ov-val dim">{new Date().toLocaleTimeString('en-GB')}</span>
    </div>
  </div>

  <div class="overlay-left">
    <div class="scroller-inner">
      {#each detectionHistory.slice(0, 8) as log}
        <div class="sensor-card log-card">
          <div class="sc-row"><span class="sc-key">TIME</span><span class="sc-val">{new Date(log.ts).toLocaleTimeString()}</span></div>
          <div class="sc-row"><span class="sc-key">TARGETS</span><span class="sc-val" style="color:#00ff88">{log.count} count</span></div>
          <div class="sc-row"><span class="sc-key">LAT</span><span class="sc-val">{log.lat}°N</span></div>
          <div class="sc-row"><span class="sc-key">LNG</span><span class="sc-val">{log.lng}°E</span></div>
        </div>
      {:else}
        <div class="sensor-card log-card">
          <div class="sc-row"><span class="sc-key" style="color:#44567a">No targets logged yet</span></div>
        </div>
      {/each}
    </div>
  </div>

  {#if alertState !== 'none'}
    <div class="alert-banner-box {alertState}">
      <div class="alert-flash">
        {#if alertState === 'possible'}
          WARNING: POSSIBLE TARGET DETECTED
        {:else if alertState === 'confirmed'}
          ALERT: TARGET FOUND
        {:else if alertState === 'nopulse'}
          TARGET FOUND BUT NO PULSE
        {/if}
      </div>
      <div class="alert-details">
        {#if heartRate > 0}
          <!-- Status: <span class="cond-txt">{clinicalCondition}</span> -->
        {:else}
          <span class="cond-txt">Vital signs absent</span>
        {/if}
      </div>
    </div>
  {/if}

  {#if distance < 50.0 && connected}
    <!-- <div class="proximity-warning">WARNING: PROXIMITY CRITICAL</div> -->
  {/if}

  <div class="overlay-right">
    <div class="scroller-inner">
      <div class="vital-card heart-card">
        <div class="vc-label">HEART RATE</div>
        <div class="vc-value" style="color: {heartRate > 0 ? '#ff4444' : '#555'}">{heartRate.toFixed(0)}</div>
        <div class="vc-unit">BPM</div>
      </div>

      <div class="vital-card breath-card">
        <div class="vc-label">BREATH RATE</div>
        <div class="vc-value blue">{breathRate.toFixed(1)}</div>
        <div class="vc-unit">RPM</div>
      </div>
    </div>
  </div>

  <div class="overlay-bottom">
    <div class="coord-tape">
      <span class="ct-sep">|</span>
      <span class="ct-sep">|</span>
      <span class="ct-item"><span class="ct-label">TARGETS</span><span class="ct-val" style="color: {targetsCount > 0 ? '#00ff88' : '#666'}">{targetsCount} count</span></span>
    </div>
  </div>
</div>

<style>
  .lv-root { 
    position: relative; 
    width: 100%; 
    height: 100%; 
    overflow: hidden; 
    background: #020408;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .video-ratio-container {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: calc(100vh - 48px);
    aspect-ratio: 16 / 9;
    position: relative;
    background: #040712;
    overflow: hidden;
  }

  .camera-bg { position: absolute; inset: 0; z-index: 1; }
  .camera-video { width: 100%; height: 100%; object-fit: cover; display: block; }
  .camera-placeholder { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: #040712; }
  .placeholder-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(0,255,136,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,136,0.03) 1px, transparent 1px); background-size: 30px 30px; }
  .placeholder-msg { font-size: 0.7rem; letter-spacing: 1.5px; color: #1e3328; text-transform: uppercase; z-index: 1; text-align: center; padding: 1rem; border: 1px dashed rgba(0,255,136,0.1); }
  .camera-vignette { position: absolute; inset: 0; background: radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.8) 100%); pointer-events: none; z-index: 3; }
  .scanlines { position: absolute; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0px, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 4px); pointer-events: none; z-index: 2; }
  
  .alert-banner-box {
    position: absolute; top: 4.5rem; left: 50%;
    transform: translateX(-50%);
    width: 320px; border-radius: 4px;
    padding: 0.6rem; backdrop-filter: blur(8px); z-index: 50;
    border: 1px solid transparent;
  }

  .alert-banner-box.possible { background: rgba(25, 15, 0, 0.95); border-color: #ffaa00; }
  .alert-banner-box.possible .alert-flash, .alert-banner-box.possible .cond-txt { color: #ffaa00; }

  .alert-banner-box.confirmed { background: rgba(11, 25, 16, 0.95); border-color: #00ff88; }
  .alert-banner-box.confirmed .alert-flash { color: #00ff88; }
  .alert-banner-box.confirmed .cond-txt { color: #ff5555; }

  .alert-banner-box.nopulse { background: rgba(30, 10, 14, 0.95); border-color: #ff4444; }
  .alert-banner-box.nopulse .alert-flash, .alert-banner-box.nopulse .cond-txt { color: #ff4444; }

  .alert-flash { font-weight: bold; font-size: 0.7rem; letter-spacing: 1px; margin-bottom: 0.2rem; }
  .alert-details { font-size: 0.65rem; line-height: 1.4; color: #d1dfec; }
  .cond-txt { font-weight: bold; }

  .overlay-top, .overlay-left, .overlay-right, .overlay-bottom { 
    position: absolute; 
    z-index: 10; 
    pointer-events: none;
  }
  
  .overlay-top { top: 0.75rem; left: 0.75rem; right: 0.75rem; display: flex; justify-content: space-between; }
  .ov-pill { background: rgba(8,11,16,0.9); border: 1px solid rgba(0,255,136,0.15); border-radius: 4px; padding: 0.3rem 0.6rem; display: flex; gap: 0.5rem; pointer-events: auto; }
  .ov-label { font-size: 0.55rem; color: #44567a; letter-spacing: 1px; }
  .ov-val { font-size: 0.75rem; font-weight: bold; }
  .ov-val.yellow { color: #ffcc00; }
  .ov-val.dim { color: #444; }
  .ov-unit { font-size: 0.55rem; color: #444; margin-left: 2px; }
  
  .overlay-left { 
    top: 3.5rem; 
    left: 0.75rem;
    bottom: 2.5rem;
    width: 322px;
    display: flex;
    flex-direction: column;
  }

  .overlay-right { 
    top: 3.5rem;
    right: 0.75rem; 
    bottom: 2.5rem;
    width: 170px; 
    display: flex; 
    flex-direction: column;
  }

  .scroller-inner {
    width: 100%;
    max-height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    pointer-events: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-right: 4px;
  }

  .scroller-inner::-webkit-scrollbar { width: 4px; }
  .scroller-inner::-webkit-scrollbar-track { background: transparent; }
  .scroller-inner::-webkit-scrollbar-thumb { background: rgba(0, 255, 136, 0.2); border-radius: 2px; }

  .sensor-card { background: rgba(8, 11, 16, 0.9); border: 1px solid rgba(0, 255, 136, 0.12); border-radius: 4px; padding: 0.4rem; width: 45%; }
  .sc-header { display: flex; gap: 0.3rem; border-bottom: 1px solid rgba(0,255,136,0.1); padding-bottom: 0.25rem; margin-bottom: 0.35rem; align-items: center; }
  .sc-title { font-size: 0.5rem; letter-spacing: 1.2px; color: #00ff88; }
  .sc-row { display: flex; justify-content: space-between; font-size: 0.6rem; }
  .sc-key { color: #44567a; }
  .sc-val { font-weight: bold; color: #c3cfe2; }
  .sc-val.blue { color: #4488ff; }
  
  .vital-card { background: rgba(8,11,16,0.9); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 0.6rem; display: flex; flex-direction: column; align-items: center; width: 100%; }
  .heart-card { border-top: 2px solid #ff4444; }
  .breath-card { border-top: 2px solid #4488ff; }
  .vc-label { font-size: 0.55rem; color: #44567a; letter-spacing: 1px; margin-bottom: 0.2rem; }
  .vc-value { font-size: 2rem; font-weight: bold; line-height: 1; }
  .vc-value.blue { color: #4488ff; }
  .vc-unit { font-size: 0.55rem; color: #444; }
  
  .overlay-bottom { bottom: 0; left: 0; right: 0; }
  .coord-tape { background: #0b0f19; border-top: 1px solid rgba(0,255,136,0.12); padding: 0.4rem 1rem; display: flex; gap: 0.8rem; font-size: 0.65rem; pointer-events: auto; }
  .ct-label { color: #44567a; margin-right: 0.25rem; }
  .ct-val { color: #8892b0; }
  .ct-sep { color: #1e293b; }
</style>