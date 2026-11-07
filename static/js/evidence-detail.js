document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('verifyForm');
  if (!form) return;
  form.addEventListener('submit', event => {
    event.preventDefault();
    const token = form.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(form.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': token },
      credentials: 'same-origin',
    })
      .then(() => window.location.reload())
      .catch(() => window.location.reload());
  });
});
