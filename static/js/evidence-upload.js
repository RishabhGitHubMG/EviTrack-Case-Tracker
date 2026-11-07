(function () {
  const form = document.getElementById('evidenceUploadForm');
  if (!form) return;

  const progress = document.getElementById('uploadProgress');
  const bar = progress.querySelector('.progress-bar');
  const submit = form.querySelector('button[type="submit"]');

  function showError(message) {
    progress.classList.add('d-none');
    submit.disabled = false;
    let alert = document.getElementById('uploadError');
    if (!alert) {
      alert = document.createElement('div');
      alert.id = 'uploadError';
      alert.className = 'alert alert-danger py-2 px-3 mb-3 font-sm';
      alert.setAttribute('role', 'alert');
      progress.before(alert);
    }
    alert.textContent = message;
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const xhr = new XMLHttpRequest();
    xhr.open('POST', form.action || window.location.href);

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        bar.style.width = Math.round((e.loaded / e.total) * 100) + '%';
      }
    });
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 400 && xhr.responseURL && xhr.responseURL !== window.location.href) {
        window.location.href = xhr.responseURL;
        return;
      }
      document.open();
      document.write(xhr.responseText);
      document.close();
    });
    xhr.addEventListener('error', () => showError('Upload failed because of a network error. Try again.'));

    const alertBox = document.getElementById('uploadError');
    if (alertBox) alertBox.remove();
    bar.style.width = '0%';
    progress.classList.remove('d-none');
    submit.disabled = true;
    xhr.send(new FormData(form));
  });
})();
