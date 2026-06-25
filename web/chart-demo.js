export function createChartDemo(canvasId) {
  let chart = null;
  let convert = null;
  let csvBytes = null;
  let bikeData = null;
  let modelData = null;
  let secsPerSample = 3.0;

  function loadChartJs() {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function parseTcx(tcxXml) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(tcxXml, 'text/xml');
    const points = doc.getElementsByTagName('Trackpoint');
    const data = { distance: [], watts: [], time: [] };
    for (let i = 0; i < points.length; i++) {
      const tp = points[i];
      const distEls = tp.getElementsByTagName('DistanceMeters');
      const wattEls = tp.getElementsByTagName('Watts');
      data.distance.push(distEls.length > 0 ? parseFloat(distEls[0].textContent) : 0);
      data.watts.push(wattEls.length > 0 ? parseFloat(wattEls[0].textContent) : 0);
      data.time.push(i * secsPerSample);
    }
    return data;
  }

  function computeSpeed(distances) {
    const speeds = [];
    for (let i = 0; i < distances.length; i++) {
      if (i === 0) {
        speeds.push(0);
      } else {
        const delta = distances[i] - distances[i - 1];
        speeds.push((delta / secsPerSample) * 2.23694);
      }
    }
    return speeds;
  }

  function computeData(mass) {
    const bikeResult = convert(csvBytes, null, false, false, 0, 0);
    bikeData = parseTcx(bikeResult.tcx);

    const totalTimeMatch = bikeResult.tcx.match(/<TotalTimeSeconds>([\d.]+)<\/TotalTimeSeconds>/);
    const totalTime = totalTimeMatch ? parseFloat(totalTimeMatch[1]) : 0;
    secsPerSample = bikeData.distance.length > 0
      ? totalTime / bikeData.distance.length : 3.0;

    const modelResult = convert(csvBytes, null, false, true, mass, 0);
    modelData = parseTcx(modelResult.tcx);

    const bikeDist = bikeData.distance[bikeData.distance.length - 1];
    const modelDist = modelData.distance[modelData.distance.length - 1];
    const diffPct = Math.abs(bikeDist - modelDist) / bikeDist * 100;

    return {
      bikeDist: (bikeDist / 1609.34).toFixed(1) + ' mi',
      modelDist: (modelDist / 1609.34).toFixed(1) + ' mi',
      diffPct: diffPct.toFixed(0) + '%'
    };
  }

  function getChartData(view) {
    let values1, values2, label1, label2, yLabel;

    if (view === 'speed') {
      values1 = computeSpeed(bikeData.distance);
      values2 = computeSpeed(modelData.distance);
      label1 = 'Bike reported';
      label2 = 'Physics model';
      yLabel = 'Speed (mph)';
    } else if (view === 'distance') {
      values1 = bikeData.distance.map(d => d / 1609.34);
      values2 = modelData.distance.map(d => d / 1609.34);
      label1 = 'Bike reported';
      label2 = 'Physics model';
      yLabel = 'Distance (miles)';
    } else {
      values1 = bikeData.watts;
      values2 = null;
      label1 = 'Power';
      label2 = null;
      yLabel = 'Power (watts)';
    }

    const labels = bikeData.time.map(t => {
      const m = Math.floor(t / 60);
      const s = Math.floor(t % 60);
      return m + ':' + (s < 10 ? '0' : '') + s;
    });

    const datasets = [{
      label: label1,
      data: values1,
      borderColor: values2 ? 'rgb(54, 162, 235)' : 'rgb(214, 40, 158)',
      backgroundColor: 'transparent',
      borderWidth: 2,
      pointRadius: 0,
      order: 2,
    }];

    if (values2) {
      datasets.push({
        label: label2,
        data: values2,
        borderColor: 'rgb(214, 40, 158)',
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 0,
        order: 1,
      });
    }

    return { labels, datasets, yLabel };
  }

  async function load(wasmPath, csvPath, mass) {
    await loadChartJs();
    const { default: init, convert_csv_to_tcx } = await import('./pkg/mpowertcx_wasm.js');
    await init(wasmPath);
    convert = convert_csv_to_tcx;
    const resp = await fetch(csvPath);
    csvBytes = new Uint8Array(await resp.arrayBuffer());
    return computeData(mass);
  }

  function setView(view) {
    if (typeof Chart === 'undefined' || !bikeData) return;

    const { labels, datasets, yLabel } = getChartData(view);

    if (chart) {
      chart.data.labels = labels;
      chart.data.datasets = datasets;
      chart.options.scales.y.title.text = yLabel;
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
          legend: { position: 'top' },
          tooltip: {
            callbacks: {
              title: function(items) {
                return 'Time: ' + items[0].label;
              }
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Time' },
            ticks: { maxTicksLimit: 12 }
          },
          y: {
            title: { display: true, text: yLabel },
            beginAtZero: true,
          }
        },
        elements: { line: { tension: 0.3 } }
      }
    });
  }

  function setMass(mass) {
    return computeData(mass);
  }

  return { load, setView, setMass };
}
