let chartRefs = {};
function destroyChart(key){ if(chartRefs[key]){ chartRefs[key].destroy(); } }

async function loadAnalyticsPage(){
  try {
    const data = await api('/forms');
    const sel = document.getElementById('analytics-form-select');
    const publishable = data.forms.filter(f=>f.status!=='draft');
    if (publishable.length === 0) {
      sel.innerHTML = '<option>No published forms</option>';
      document.getElementById('analytics-stat-row').innerHTML =
        '<div class="empty-state" style="grid-column:1/-1;"><h3>No data yet</h3><p>Publish a form to start collecting analytics.</p></div>';
      return;
    }
    sel.innerHTML = publishable.map(f=>'<option value="'+f.id+'">'+f.title+'</option>').join('');
    sel.onchange = renderAnalyticsCharts;

    const params = new URLSearchParams(window.location.search);
    const preselect = params.get('form');
    if (preselect && publishable.some(f=>String(f.id)===preselect)) sel.value = preselect;

    renderAnalyticsCharts();
  } catch (err) { /* toast shown */ }
}

async function renderAnalyticsCharts(){
  const formId = document.getElementById('analytics-form-select').value;
  if (!formId) return;
  let data;
  try { data = await api('/forms/'+formId+'/analytics'); }
  catch(err){ return; }

  document.getElementById('analytics-stat-row').innerHTML =
    '<div class="stat-card"><div class="label">Total views</div><div class="val">'+data.totalViews+'</div></div>' +
    '<div class="stat-card"><div class="label">Total responses</div><div class="val">'+data.totalResponses+'</div></div>' +
    '<div class="stat-card"><div class="label">Submission rate</div><div class="val">'+data.submissionRate+'%</div></div>' +
    '<div class="stat-card"><div class="label">Devices tracked</div><div class="val">'+Object.keys(data.deviceBreakdown).length+'</div></div>';

  destroyChart('area'); destroyChart('donut'); destroyChart('bar'); destroyChart('pie');

  const trendLabels = data.responseTrend.map(t=>t.date.slice(5));
  const trendValues = data.responseTrend.map(t=>t.responses);

  chartRefs.area = new Chart(document.getElementById('chart-analytics-area'), {
    type:'line',
    data:{ labels: trendLabels.length?trendLabels:['—'], datasets:[{ label:'Responses', data: trendValues.length?trendValues:[0], borderColor:'#2C5AA0', backgroundColor:'rgba(44,90,160,0.12)', fill:true, tension:0.3 }] },
    options:{ plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#EFEBDD'}} } }
  });

  const deviceLabels = Object.keys(data.deviceBreakdown);
  const deviceValues = Object.values(data.deviceBreakdown);
  chartRefs.donut = new Chart(document.getElementById('chart-analytics-donut'), {
    type:'doughnut',
    data:{ labels: deviceLabels.length?deviceLabels:['No data'], datasets:[{ data: deviceValues.length?deviceValues:[1], backgroundColor:['#2C5AA0','#E0982F','#5C8374'] }] },
    options:{ plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}}, cutout:'62%' }
  });

  chartRefs.bar = new Chart(document.getElementById('chart-analytics-bar'), {
    type:'bar',
    data:{ labels: trendLabels.length?trendLabels:['—'], datasets:[{ data: trendValues.length?trendValues:[0], backgroundColor:'#2C5AA0', borderRadius:3 }] },
    options:{ plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#EFEBDD'}} } }
  });

  const sourceLabels = Object.keys(data.sourceBreakdown);
  const sourceValues = Object.values(data.sourceBreakdown);
  chartRefs.pie = new Chart(document.getElementById('chart-analytics-pie'), {
    type:'pie',
    data:{ labels: sourceLabels.length?sourceLabels:['No data'], datasets:[{ data: sourceValues.length?sourceValues:[1], backgroundColor:['#2C5AA0','#E0982F','#5C8374','#B84C3E'] }] },
    options:{ plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:11}}}} }
  });
}

document.addEventListener('DOMContentLoaded', loadAnalyticsPage);
