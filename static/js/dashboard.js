(function () {
    const chartsUrl = document.currentScript && document.currentScript.dataset.chartsUrl;
    if (!chartsUrl || typeof Chart === 'undefined') {
        return;
    }

    const palette = ['#14213D', '#F2A900', '#2E7D32', '#C62828', '#6B7280'];

    function barChart(canvasId, dataset) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            return;
        }
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: dataset.labels,
                datasets: [{
                    data: dataset.values,
                    backgroundColor: dataset.labels.map((_, i) => palette[i % palette.length]),
                }],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

    fetch(chartsUrl, { credentials: 'same-origin' })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Chart data request failed');
            }
            return response.json();
        })
        .then((data) => {
            barChart('cases-chart', data.cases_by_status);
            barChart('evidence-chart', data.evidence_by_status);
        })
        .catch(() => {
            document.querySelectorAll('canvas').forEach((canvas) => {
                canvas.insertAdjacentHTML('afterend', '<p class="font-sm text-muted mb-0">Chart data unavailable.</p>');
                canvas.remove();
            });
        });
})();
