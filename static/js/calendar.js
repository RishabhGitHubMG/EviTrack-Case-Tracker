(function () {
    const el = document.getElementById('calendar');
    if (!el || typeof FullCalendar === 'undefined') {
        return;
    }

    const caseSelect = document.getElementById('calendarCaseSelect');
    const scheduleForm = document.getElementById('scheduleHearingForm');
    const scheduleButton = document.getElementById('scheduleHearingButton');
    const status = document.getElementById('calendarActionStatus');

    const createHearingUrl = (date) => {
        if (!caseSelect) {
            return;
        }
        const caseId = caseSelect.value;
        if (!caseId) {
            caseSelect.focus();
            status.textContent = 'Choose a case before scheduling a hearing.';
            return;
        }
        const url = new URL(el.dataset.createUrl.replace('/0/new/', `/${caseId}/new/`), window.location.origin);
        if (date) {
            url.searchParams.set('date', `${date}T09:00`);
        }
        window.location.assign(url.toString());
    };

    if (caseSelect && scheduleForm) {
        caseSelect.addEventListener('change', () => {
            scheduleButton.disabled = !caseSelect.value;
            status.textContent = '';
        });
        scheduleForm.addEventListener('submit', (event) => {
            event.preventDefault();
            createHearingUrl();
        });
    }

    const calendar = new FullCalendar.Calendar(el, {
        initialView: 'dayGridMonth',
        height: 'auto',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek',
        },
        dateClick: function (info) {
            createHearingUrl(info.dateStr.slice(0, 10));
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
