(function () {
    const chartsUrl = document.currentScript && document.currentScript.dataset.chartsUrl;
    if (!chartsUrl || typeof Chart === 'undefined') {
        return;
    }

    const palette = ['#14213D', '#F2A900', '#2E7D32', '#C62828', '#6B7280', '#1B2A49', '#E8A317', '#4B5563'];

    function drawChart(canvasId, dataset, type, horizontal) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !dataset) {
            return;
        }
        const colours = dataset.labels.map((_, i) => palette[i % palette.length]);
        new Chart(canvas, {
            type: type,
            data: {
                labels: dataset.labels,
                datasets: [{
                    label: canvas.getAttribute('aria-label') || '',
                    data: dataset.values,
                    backgroundColor: type === 'line' ? palette[0] : colours,
                    borderColor: palette[0],
                    tension: 0.3,
                    fill: false,
                }],
            },
            options: {
                indexAxis: horizontal ? 'y' : 'x',
                plugins: { legend: { display: false } },
                scales: { [horizontal ? 'x' : 'y']: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

    function failChart(canvas) {
        if (!canvas) {
            return;
        }
        const note = document.createElement('p');
        note.className = 'font-sm text-muted mb-0';
        note.textContent = 'Chart data unavailable.';
        canvas.replaceWith(note);
    }

    fetch(chartsUrl, { credentials: 'same-origin' })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Chart data request failed');
            }
            return response.json();
        })
        .then((data) => {
            drawChart('cases-chart', data.cases_by_status, 'bar', false);
            drawChart('evidence-chart', data.evidence_by_status, 'bar', false);
            drawChart('cases-type-chart', data.cases_by_type, 'bar', false);
            drawChart('hearings-chart', data.hearings_per_week, 'bar', false);
            drawChart('workload-chart', data.workload_per_user, 'bar', true);
            drawChart('uploads-chart', data.evidence_uploads, 'line', false);
        })
        .catch(() => {
            document.querySelectorAll('canvas').forEach(failChart);
        });
})();
