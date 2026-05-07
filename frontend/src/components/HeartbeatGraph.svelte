<script>
  import { onMount } from 'svelte';
  import { Chart } from 'chart.js/auto';

  export let heartRate = 0;

  let canvas;
  let chart;
  const MAX = 60;
  let labels = Array(MAX).fill('');
  let dataPoints = Array(MAX).fill(0);

  $: if (chart && heartRate) {
    dataPoints.push(heartRate);
    dataPoints = dataPoints.slice(-MAX);
    chart.data.datasets[0].data = [...dataPoints];
    chart.update('none');
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: Array(MAX).fill(''),
        datasets: [{
          label: 'Heart Rate',
          data: [...dataPoints],
          borderColor: '#ff4444',
          backgroundColor: 'rgba(255,68,68,0.08)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.4,
          fill: true,
        }]
      },
      options: {
        animation: false,
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: {
            min: 40, max: 120,
            ticks: { color: '#666' },
            grid: { color: '#1a1a1a' }
          }
        }
      }
    });
  });
</script>

<div class="graph-card">
  <div class="graph-label">❤️ Heart Rate (BPM)</div>
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .graph-card {
    background: #111;
    border: 1px solid #222;
    border-left: 3px solid #ff4444;
    border-radius: 8px;
    padding: 1rem;
  }
  .graph-label {
    font-size: 0.75rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 0.75rem;
  }
</style>