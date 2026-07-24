let dashChart;

function statusBadge(status){ return '<span class="badge '+status+'">'+status+'</span>'; }

function renderDashLineChart(trend){
  if (dashChart) dashChart.destroy();
  const labels = (trend||[]).map(t=>t.date.slice(5));
  const values = (trend||[]).map(t=>t.responses);
  dashChart = new Chart(document.getElementById('chart-dash-line'), {
    type:'line',
    data:{ labels: labels.length?labels:['—'], datasets:[{ data: values.length?values:[0], borderColor:'#2C5AA0', backgroundColor:'rgba(44,90,160,0.08)', fill:true, tension:0.35, pointRadius:0, borderWidth:2 }] },
    options:{ plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#EFEBDD'}} } }
  });
}

async function loadDashboard(){
  document.getElementById('dash-forms-body').innerHTML = skeletonRows(3,4);
  try {
    const data = await api('/dashboard/summary');

    document.getElementById('stat-row').innerHTML =
      '<div class="stat-card"><div class="label">Total forms</div><div class="val">'+data.totalForms+'</div></div>' +
      '<div class="stat-card"><div class="label">Total responses</div><div class="val">'+data.totalResponses+'</div></div>' +
      '<div class="stat-card"><div class="label">Active forms</div><div class="val">'+data.activeForms+'</div></div>' +
      '<div class="stat-card"><div class="label">Draft forms</div><div class="val">'+(data.totalForms-data.activeForms)+'</div></div>';

    renderDashLineChart(data.responseTrend);

    if (data.recentForms.length === 0) {
      document.getElementById('dash-forms-body').innerHTML =
        '<tr><td colspan="4"><div class="empty-state" style="padding:24px 0;"><h3>No forms yet</h3><p>Create your first form to see it here.</p></div></td></tr>';
      document.getElementById('activity-list').innerHTML = '<p style="color:var(--ink-soft);">Nothing yet — publish a form to start seeing activity.</p>';
    } else {
      document.getElementById('dash-forms-body').innerHTML = data.recentForms.map(f=>
        '<tr><td><a href="/app/builder/'+f.id+'" style="font-weight:600;">'+f.title+'</a></td><td>'+statusBadge(f.status)+'</td><td>'+f.responseCount+'</td><td>'+ (f.updatedAt||'').slice(0,16) +'</td></tr>'
      ).join('');
      document.getElementById('activity-list').innerHTML = data.recentForms.slice(0,4).map(f=>
        '<div style="padding:9px 0;border-bottom:1px solid var(--paper-line);"><b>'+f.title+'</b> — '+f.responseCount+' response(s), last edited '+ (f.updatedAt||'').slice(0,16) +'</div>'
      ).join('');
    }
  } catch (err) {
    document.getElementById('dash-forms-body').innerHTML =
      '<tr><td colspan="4" style="color:var(--ink-soft);">Couldn\'t load your forms. '+err.message+'</td></tr>';
  }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
