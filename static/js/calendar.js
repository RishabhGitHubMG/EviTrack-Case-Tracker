(function () {
    const el = document.getElementById('calendar');
    if (!el || typeof FullCalendar === 'undefined') {
        return;
    }

    const calendar = new FullCalendar.Calendar(el, {
        initialView: 'dayGridMonth',
        height: 'auto',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek',
        },
        events: {
            url: el.dataset.eventsUrl,
            failure: function () {
                el.insertAdjacentHTML('beforebegin', '<p class="font-sm text-danger">Could not load calendar events.</p>');
            },
        },
    });
    calendar.render();
})();
