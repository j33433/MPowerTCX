// Ride preview for the converter page. Parses a converted TCX string,
// computes rider-friendly summary stats, and draws a single-line chart
// with a Power / Speed / Heart Rate / Cadence toggle. Chart.js is loaded
// on demand so the page stays light until a file is converted.

export function createPreviewChart(canvasId) {
  let chart = null;
  let data = null;       // parsed arrays for the current TCX
  let chartReady = false; // Chart.js + plugins loaded

  function loadChartJs() {
    if (typeof Chart !== 'undefined') return Promise.resolve();
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function zoomRegistered() {
    try {
      return typeof Chart !== 'undefined' &&
        Chart.registry.plugins.get('zoom') != null;
    } catch (e) {
      return false;
    }
  }

  async function loadChartDeps() {
    if (typeof Chart !== 'undefined') {
      if (!zoomRegistered()) {
        if (typeof self !== 'undefined' && self.ChartZoom) {
          Chart.register(self.ChartZoom);
        } else {
          const mod = await import('https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0/+esm');
          Chart.register(mod.default);
        }
      }
      chartReady = true;
      return;
    }
    await loadChartJs();
    const { default: zoomPlugin } = await import('https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0/+esm');
    Chart.register(zoomPlugin);
    chartReady = true;
  }

  function parseTcx(tcxXml) {
    const doc = new DOMParser().parseFromString(tcxXml, 'text/xml');

    const totalMatch = tcxXml.match(/<TotalTimeSeconds>([\d.]+)<\/TotalTimeSeconds>/);
    const totalTime = totalMatch ? parseFloat(totalMatch[1]) : 0;

    const points = doc.getElementsByTagName('Trackpoint');
    const n = points.length;
    const secsPerSample = n > 1 ? totalTime / (n - 1) : 1;

    const out = { time: [], watts: [], cadence: [], hr: [], distance: [], altitude: [], secsPerSample };
    for (let i = 0; i < n; i++) {
      const tp = points[i];
      const num = (tag) => {
        const el = tp.getElementsByTagName(tag)[0];
        return el ? parseFloat(el.textContent) || 0 : 0;
      };
      out.watts.push(num('Watts'));
      out.cadence.push(num('Cadence'));
      out.hr.push(num('Value')); // first <Value> in a trackpoint is HR
      out.distance.push(num('DistanceMeters'));
      const altEl = tp.getElementsByTagName('AltitudeMeters')[0];
      out.altitude.push(altEl ? parseFloat(altEl.textContent) || 0 : null);
      out.time.push(i * secsPerSample);
    }
    return out;
  }

  let currentUnits = 'kg'; // 'kg' = metric, 'lbs' = imperial

  function speedSeries(d) {
    const spm = d.secsPerSample || 1;
    const factor = currentUnits === 'lbs' ? 2.23694 : 3.6; // m/s -> mph or km/h
    return d.distance.map((v, i) => {
      if (i === 0) return 0;
      const delta = v - d.distance[i - 1];
      return Math.max(0, (delta / spm) * factor);
    });
  }

  function fmtDuration(secs) {
    const s = Math.round(secs);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    return `${m}:${String(sec).padStart(2, '0')}`;
  }

  function avg(arr, skipZero) {
    const vals = skipZero ? arr.filter((v) => v > 0) : arr;
    if (vals.length === 0) return 0;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }

  function computeStats(d) {
    const speeds = speedSeries(d);
    const lastDist = d.distance[d.distance.length - 1] || 0;
    const duration = d.time[d.time.length - 1] || 0;
    const hasAlt = d.altitude.some((v) => v !== null);
    let elevGain = 0;
    if (hasAlt) {
      for (let i = 1; i < d.altitude.length; i++) {
        const prev = d.altitude[i - 1];
        const cur = d.altitude[i];
        if (prev !== null && cur !== null && cur > prev) {
          elevGain += cur - prev;
        }
      }
    }

    const metric = currentUnits === 'kg';
    const distStr = metric
      ? (lastDist / 1000).toFixed(2) + ' km'
      : (lastDist / 1609.34).toFixed(1) + ' mi';
    const speedStr = avg(speeds, false).toFixed(1) + (metric ? ' km/h' : ' mph');
    const elevStr = hasAlt
      ? (metric ? Math.round(elevGain) + ' m' : Math.round(elevGain * 3.28084) + ' ft')
      : '--';

    return {
      duration: fmtDuration(duration),
      distance: distStr,
      avgPower: Math.round(avg(d.watts, false)) + ' W',
      maxPower: Math.round(Math.max(0, ...d.watts)) + ' W',
      avgHr: d.hr.some((v) => v > 0) ? Math.round(avg(d.hr, true)) + ' bpm' : '--',
      maxHr: d.hr.some((v) => v > 0) ? Math.round(Math.max(0, ...d.hr)) + ' bpm' : '--',
      avgCadence: Math.round(avg(d.cadence, true)) + ' rpm',
      avgSpeed: speedStr,
      hasAltitude: hasAlt,
      elevGain: elevStr,
    };
  }

  const VIEWS = {
    power:   { label: 'Power',      y: 'Power (watts)',  color: 'rgb(214, 40, 158)',  series: (d) => d.watts },
    speed:   { label: 'Speed',      y: 'Speed (mph)',    color: 'rgb(54, 162, 235)',  series: speedSeries },
    hr:      { label: 'Heart rate', y: 'Heart rate (bpm)', color: 'rgb(235, 77, 75)', series: (d) => d.hr },
    cadence: { label: 'Cadence',    y: 'Cadence (rpm)',  color: 'rgb(46, 174, 122)',  series: (d) => d.cadence },
    elevation: { label: 'Elevation', y: 'Elevation (m)', color: 'rgb(139, 105, 20)', series: (d) => d.altitude.map(v => v === null ? 0 : v) },
  };

  function viewConfig(view) {
    const v = VIEWS[view] || VIEWS.power;
    if (view === 'speed') {
      const metric = currentUnits === 'kg';
      return { ...v, y: metric ? 'Speed (km/h)' : 'Speed (mph)' };
    }
    if (view === 'elevation') {
      const metric = currentUnits === 'kg';
      return {
        ...v,
        y: metric ? 'Elevation (m)' : 'Elevation (ft)',
        series: (d) => d.altitude.map((val) => {
          if (val === null) return 0;
          return metric ? val : val * 3.28084;
        }),
      };
    }
    return v;
  }

  function chartData(view) {
    const v = viewConfig(view);
    const labels = data.time.map((t) => {
      const m = Math.floor(t / 60);
      const s = Math.floor(t % 60);
      return m + ':' + (s < 10 ? '0' : '') + s;
    });
    return {
      labels,
      yLabel: v.y,
      datasets: [{
        label: v.label,
        data: v.series(data),
        borderColor: v.color,
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
      }],
    };
  }

  function drawChart(view) {
    if (!chartReady || !data) return;
    const { labels, datasets, yLabel } = chartData(view);

    if (chart) {
      chart.data.labels = labels;
      chart.data.datasets = datasets;
      chart.options.scales.y.title.text = yLabel;
      chart.resetZoom();
      chart.update('none');
      return;
    }

    const ctx = document.getElementById(canvasId).getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: { title: (items) => 'Time: ' + items[0].label },
          },
          zoom: {
            zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' },
            pan: { enabled: true, mode: 'x' },
          },
        },
        scales: {
          x: { ticks: { maxTicksLimit: 12 } },
          y: { title: { display: true, text: yLabel }, beginAtZero: true },
        },
        elements: { line: { tension: 0.3 } },
        animation: false,
      },
    });
  }

  // Parse + compute stats immediately (no Chart.js needed), then draw the
  // chart once Chart.js is available. Returns { stats, charted } where
  // `charted` is false if the chart library could not be loaded.
  async function render(tcxXml, view, units) {
    currentUnits = units || 'kg';
    data = parseTcx(tcxXml);
    const stats = computeStats(data);

    let charted = true;
    try {
      if (!chartReady) {
        await loadChartDeps();
      }
      drawChart(view || 'power');
    } catch (e) {
      console.error('Preview chart failed to load:', e);
      charted = false;
    }
    return { stats, charted };
  }

  function setView(view, units) {
    if (units) currentUnits = units;
    drawChart(view);
  }

  function resetZoom() {
    if (chart) chart.resetZoom();
  }

  return { render, setView, resetZoom };
}
