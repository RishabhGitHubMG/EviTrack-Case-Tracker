document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('verifyForm');
  if (!form) return;

  const button = form.querySelector('button[type="submit"]');
  const resultBox = document.getElementById('verifyResult');
  const checksList = document.getElementById('integrityChecks');

  function setResult(kind, text) {
    if (!resultBox) return;
    resultBox.replaceChildren();
    const badge = document.createElement('span');
    badge.className = `badge-ev ${kind}`;
    badge.textContent = text;
    resultBox.appendChild(badge);
  }

  function prependCheck(kind, text, checkedOn) {
    if (!checksList) return;
    const empty = checksList.querySelector('[data-empty-checks]');
    if (empty) empty.remove();
    const row = document.createElement('div');
    row.className = 'font-sm py-1';
    const badge = document.createElement('span');
    badge.className = `badge-ev ${kind}`;
    badge.textContent = text;
    const time = document.createElement('span');
    time.className = 'text-muted';
    time.textContent = ' ' + checkedOn;
    row.append(badge, time);
    checksList.prepend(row);
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    button.disabled = true;
    setResult('', 'Checking hash…');

    const token = form.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(form.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': token },
      credentials: 'same-origin',
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok || data.status === 'error') {
          const failure = new Error('Verification failed.');
          failure.serverMessage = data.message;
          throw failure;
        }
        if (data.is_valid) {
          setResult('badge-verified', 'Verified: hash matches');
          prependCheck('badge-verified', 'Verified', data.checked_on);
          if (window.EviTrack) window.EviTrack.showToast('Integrity verified. The stored hash matches.', 'success', 4000);
          return;
        }
        setResult('badge-flagged', 'Modified: hash mismatch');
        prependCheck('badge-flagged', 'Modified', data.checked_on);
        if (window.EviTrack) window.EviTrack.showToast('Integrity check failed. The case managers have been alerted.', 'danger', 6000);
        window.setTimeout(() => window.location.reload(), 2000);
      })
      .catch((error) => {
        setResult('badge-flagged', error && error.serverMessage ? error.serverMessage : 'Verification could not be completed.');
        if (window.EviTrack) window.EviTrack.showToast('Verification could not be completed. Try again.', 'warning', 4000);
      })
      .finally(() => {
        button.disabled = false;
      });
  });
});
