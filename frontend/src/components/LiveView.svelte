<script>
  export let heartRate = 0;
  export let breathRate = 0;
  export let distance = 0;
  export let temperature = 0;
  export let humidity = 0;
  export let gps = { lat: 0, lng: 0, accuracy: 0, altitude: 0, speed: 0, heading: 0 };
  export let connected = false;

  /** @type {MediaStream | null} */
  let cameraStream = null;
  /** @type {HTMLVideoElement | null} */
  let videoEl = null;
  let cameraError = '';
  let cameraActive = false;

  async function startCamera() {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false
      });
      if (videoEl) videoEl.srcObject = cameraStream;
      cameraActive = true;
      cameraError = '';
    } catch (e) {
      const err = /** @type {{ name?: string }} */ (e);
      cameraError = err.name === 'NotAllowedError'
        ? 'Camera permission denied'
        : 'No camera available — showing simulated feed';
    }
  }

  /** @param {number} bpm */
  function heartStatus(bpm) {
    if (bpm === 0) return { label: 'NO DATA', color: '#555' };
    if (bpm < 60)  return { label: 'LOW', color: '#ff9900' };
    if (bpm > 100) return { label: 'HIGH', color: '#ff4444' };
    return { label: 'NORMAL', color: '#00ff88' };
  }

  /** @param {number} t */
  function tempStatus(t) {
    if (t === 0) return { label: '--', color: '#555' };
    if (t > 38)  return { label: 'HOT', color: '#ff4444' };
    if (t < 20)  return { label: 'COLD', color: '#4488ff' };
    return { label: 'OK', color: '#00ff88' };
  }

  $: hs = heartStatus(heartRate);
  $: ts = tempStatus(temperature);

  import { onMount, onDestroy } from 'svelte';
  onMount(() => startCamera());
  onDestroy(() => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(
        /** @param {MediaStreamTrack} t */ (t) => t.stop()
      );
    }
  });
</script>

<div class="lv-root">
  <!-- Camera feed -->
  <div class="camera-bg">
    {#if cameraError}
      <div class="camera-placeholder">
        <div class="placeholder-grid"></div>
        <div class="placeholder-msg">{cameraError}</div>
      </div>
    {:else}
      <!-- svelte-ignore a11y-media-has-caption -->
      <video bind:this={videoEl} autoplay playsinline muted class="camera-video" class:active={cameraActive}></video>
    {/if}
    <div class="camera-vignette"></div>
  </div>

  <!-- Scanline effect -->
  <div class="scanlines"></div>

  <!-- Top bar overlay -->
  <div class="overlay-top">
    <div class="ov-pill">
      <span class="ov-label">SYS</span>
      <span class="ov-val" style="color: {connected ? '#00ff88' : '#ff4444'}">{connected ? 'CONNECTED' : 'OFFLINE'}</span>
    </div>
    <div class="ov-pill center-pill">
      <span class="ov-label">🎯 DISTANCE</span>
      <span class="ov-val yellow">{distance.toFixed(1)}<span class="ov-unit">cm</span></span>
    </div>
    <div class="ov-pill">
      <span class="ov-label">UTC</span>
      <span class="ov-val dim">{new Date().toLocaleTimeString('en-GB')}</span>
    </div>
  </div>

  <!-- Left column overlay — GPS -->
  <div class="overlay-left">
    <div class="sensor-card gps-card">
      <div class="sc-header">
        <span class="sc-icon">🛰️</span>
        <span class="sc-title">GPS</span>
      </div>
      <div class="sc-row">
        <span class="sc-key">LAT</span>
        <span class="sc-val">{gps.lat.toFixed(5)}°</span>
      </div>
      <div class="sc-row">
        <span class="sc-key">LNG</span>
        <span class="sc-val">{gps.lng.toFixed(5)}°</span>
      </div>
      <div class="sc-row">
        <span class="sc-key">ALT</span>
        <span class="sc-val">{gps.altitude}<span class="sc-unit">m</span></span>
      </div>
      <div class="sc-row">
        <span class="sc-key">SPD</span>
        <span class="sc-val">{gps.speed.toFixed(1)}<span class="sc-unit">m/s</span></span>
      </div>
      <div class="sc-row">
        <span class="sc-key">HDG</span>
        <span class="sc-val">{gps.heading.toFixed(0)}<span class="sc-unit">°</span></span>
      </div>
      <div class="sc-row">
        <span class="sc-key">ACC</span>
        <span class="sc-val">±{gps.accuracy.toFixed(1)}<span class="sc-unit">m</span></span>
      </div>
    </div>

    <div class="sensor-card env-card">
      <div class="sc-header">
        <span class="sc-icon">🌡️</span>
        <span class="sc-title">ENVIRONMENT</span>
      </div>
      <div class="sc-row">
        <span class="sc-key">TEMP</span>
        <span class="sc-val" style="color:{ts.color}">{temperature.toFixed(1)}<span class="sc-unit">°C</span></span>
      </div>
      <div class="sc-row">
        <span class="sc-key">STATUS</span>
        <span class="sc-val" style="color:{ts.color}">{ts.label}</span>
      </div>
      <div class="sc-row">
        <span class="sc-key">HUM</span>
        <span class="sc-val blue">{humidity.toFixed(0)}<span class="sc-unit">%</span></span>
      </div>
    </div>
  </div>

  <!-- Right column overlay — Vitals -->
  <div class="overlay-right">
    <div class="vital-card heart-card">
      <div class="vc-icon">❤️</div>
      <div class="vc-label">HEART RATE</div>
      <div class="vc-value" style="color:{hs.color}">{heartRate.toFixed(0)}</div>
      <div class="vc-unit">BPM</div>
      <div class="vc-badge" style="color:{hs.color}; border-color:{hs.color}40">{hs.label}</div>
      <div class="heartbeat-line">
        <svg viewBox="0 0 120 30" preserveAspectRatio="none">
          <polyline
            points="0,15 15,15 20,5 25,25 30,10 35,20 40,15 120,15"
            fill="none"
            stroke={hs.color}
            stroke-width="1.5"
            opacity="0.7"
          />
        </svg>
      </div>
    </div>

    <div class="vital-card breath-card">
      <div class="vc-icon">🫁</div>
      <div class="vc-label">BREATH RATE</div>
      <div class="vc-value blue">{breathRate.toFixed(1)}</div>
      <div class="vc-unit">RPM</div>
      <div class="vc-badge breath-badge">
        {breathRate < 12 ? 'LOW' : breathRate > 20 ? 'HIGH' : 'NORMAL'}
      </div>
    </div>
  </div>

  <!-- Bottom bar — coordinate tape -->
  <div class="overlay-bottom">
    <div class="coord-tape">
      <span class="ct-item">
        <span class="ct-label">ROBOT POS</span>
        <span class="ct-val">{gps.lat.toFixed(6)}, {gps.lng.toFixed(6)}</span>
      </span>
      <span class="ct-sep">|</span>
      <span class="ct-item">
        <span class="ct-label">VITALS</span>
        <span class="ct-val">HR:{heartRate.toFixed(0)} BR:{breathRate.toFixed(1)} T:{temperature.toFixed(1)}°C RH:{humidity.toFixed(0)}%</span>
      </span>
      <span class="ct-sep">|</span>
      <span class="ct-item">
        <span class="ct-label">SENSOR</span>
        <span class="ct-val">{distance.toFixed(1)}cm</span>
      </span>
    </div>
  </div>

  <!-- Corner reticles -->
  <div class="reticle tl"></div>
  <div class="reticle tr"></div>
  <div class="reticle bl"></div>
  <div class="reticle br"></div>
</div>

<style>
  .lv-root {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #000;
  }

  /* ── Camera ── */
  .camera-bg {
    position: absolute;
    inset: 0;
  }
  .camera-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.5s;
  }
  .camera-video.active { opacity: 1; }

  .camera-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #050810;
  }
  .placeholder-grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(0,255,136,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,136,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
  }
  .placeholder-msg {
    font-size: 0.75rem;
    letter-spacing: 2px;
    color: #2a3a30;
    text-transform: uppercase;
    z-index: 1;
  }

  .camera-vignette {
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.75) 100%);
    pointer-events: none;
  }

  /* ── Scanlines ── */
  .scanlines {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      to bottom,
      transparent 0px,
      transparent 2px,
      rgba(0,0,0,0.08) 2px,
      rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 2;
  }

  /* ── Overlays ── */
  .overlay-top,
  .overlay-left,
  .overlay-right,
  .overlay-bottom {
    position: absolute;
    z-index: 10;
    pointer-events: none;
  }

  /* Top */
  .overlay-top {
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .ov-pill {
    background: rgba(8,11,16,0.82);
    border: 1px solid rgba(0,255,136,0.15);
    border-radius: 4px;
    padding: 0.3rem 0.7rem;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    backdrop-filter: blur(6px);
  }
  .center-pill { margin: 0 auto; }
  .ov-label { font-size: 0.6rem; letter-spacing: 2px; color: #555; text-transform: uppercase; }
  .ov-val   { font-size: 0.8rem; font-weight: bold; letter-spacing: 1px; color: #ccc; }
  .ov-val.yellow { color: #ffcc00; }
  .ov-val.dim    { color: #666; font-size: 0.75rem; }
  .ov-unit { font-size: 0.6rem; color: #555; margin-left: 2px; }

  /* Left */
  .overlay-left {
    top: 3.5rem;
    left: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 180px;
  }

  .sensor-card {
    background: rgba(8,11,16,0.82);
    border: 1px solid rgba(0,255,136,0.12);
    border-radius: 6px;
    padding: 0.6rem 0.75rem;
    backdrop-filter: blur(8px);
  }

  .sc-header {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    margin-bottom: 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(0,255,136,0.1);
  }
  .sc-icon { font-size: 0.85rem; }
  .sc-title { font-size: 0.6rem; letter-spacing: 2.5px; color: #00ff88; text-transform: uppercase; }
  .sc-row { display: flex; justify-content: space-between; align-items: center; padding: 0.15rem 0; }
  .sc-key  { font-size: 0.58rem; letter-spacing: 1.5px; color: #444; text-transform: uppercase; }
  .sc-val  { font-size: 0.72rem; color: #ccc; font-weight: bold; }
  .sc-unit { font-size: 0.55rem; color: #555; margin-left: 1px; font-weight: normal; }
  .sc-val.blue { color: #4488ff; }

  /* Right */
  .overlay-right {
    top: 3.5rem;
    right: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 160px;
  }

  .vital-card {
    background: rgba(8,11,16,0.82);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 0.7rem;
    backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .heart-card { border-top: 2px solid rgba(255,68,68,0.5); }
  .breath-card { border-top: 2px solid rgba(68,136,255,0.5); }

  .vc-icon  { font-size: 1.1rem; margin-bottom: 0.25rem; }
  .vc-label { font-size: 0.55rem; letter-spacing: 2px; color: #555; text-transform: uppercase; margin-bottom: 0.3rem; }
  .vc-value { font-size: 2.2rem; font-weight: bold; line-height: 1; }
  .vc-value.blue { color: #4488ff; }
  .vc-unit  { font-size: 0.6rem; color: #555; letter-spacing: 2px; margin-top: 0.15rem; }
  .vc-badge {
    margin-top: 0.4rem;
    font-size: 0.6rem;
    letter-spacing: 2px;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    border: 1px solid;
    text-transform: uppercase;
  }
  .breath-badge { color: #4488ff; border-color: rgba(68,136,255,0.3); }

  .heartbeat-line {
    width: 100%;
    height: 24px;
    margin-top: 0.5rem;
    opacity: 0.6;
  }

  /* Bottom */
  .overlay-bottom {
    bottom: 0;
    left: 0;
    right: 0;
  }

  .coord-tape {
    background: rgba(8,11,16,0.88);
    border-top: 1px solid rgba(0,255,136,0.12);
    padding: 0.4rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    overflow: hidden;
  }

  .ct-item { display: flex; gap: 0.4rem; align-items: center; white-space: nowrap; }
  .ct-label { font-size: 0.55rem; letter-spacing: 2px; color: #444; text-transform: uppercase; }
  .ct-val   { font-size: 0.65rem; color: #888; letter-spacing: 1px; }
  .ct-sep   { color: #222; font-size: 0.8rem; }

  /* Reticles */
  .reticle {
    position: absolute;
    width: 20px;
    height: 20px;
    z-index: 5;
    pointer-events: none;
  }
  .reticle.tl { top: 10px;    left: 10px;    border-top: 2px solid rgba(0,255,136,0.4); border-left: 2px solid rgba(0,255,136,0.4); }
  .reticle.tr { top: 10px;    right: 10px;   border-top: 2px solid rgba(0,255,136,0.4); border-right: 2px solid rgba(0,255,136,0.4); }
  .reticle.bl { bottom: 36px; left: 10px;    border-bottom: 2px solid rgba(0,255,136,0.4); border-left: 2px solid rgba(0,255,136,0.4); }
  .reticle.br { bottom: 36px; right: 10px;   border-bottom: 2px solid rgba(0,255,136,0.4); border-right: 2px solid rgba(0,255,136,0.4); }
</style>