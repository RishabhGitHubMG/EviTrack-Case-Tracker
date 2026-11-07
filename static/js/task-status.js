document.addEventListener('DOMContentLoaded', () => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  document.querySelectorAll('.task-status-select').forEach(select => {
    select.addEventListener('change', async () => {
      const taskId = select.dataset.taskId;
      try {
        const response = await fetch(`/hearings/tasks/${taskId}/status/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: `status=${encodeURIComponent(select.value)}`,
        });
        const data = await response.json();
        if (!data.success) {
          window.alert(data.error || 'Failed to update task status.');
          return;
        }
        const title = document.querySelector(`#task-row-${taskId} .fw-semibold`);
        if (!title) return;
        title.classList.toggle('text-decoration-line-through', data.is_completed);
        title.classList.toggle('text-muted', data.is_completed);
      } catch {
        window.alert('An error occurred updating the task status.');
      }
    });
  });
});
