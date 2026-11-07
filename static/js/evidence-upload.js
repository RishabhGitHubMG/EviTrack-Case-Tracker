(function () {
  const form = document.getElementById('evidenceUploadForm');
  if (!form) return;

  const dropzone = document.getElementById('evDropzone');
  const input = form.querySelector('input[type="file"]');
  const queue = document.getElementById('uploadQueue');
  const submit = document.getElementById('uploadSubmit');
  const errorBox = document.getElementById('uploadError');
  const doneUrl = form.dataset.doneUrl;

  let items = [];

  function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + ' ' + units[i];
  }

  function statusLabel(item) {
    if (item.status === 'uploading') return `Uploading ${item.progress}%`;
    if (item.status === 'done') return 'Uploaded';
    if (item.status === 'failed') return item.message || 'Failed';
    return 'Waiting';
  }

  function buildRow(item, index) {
    const li = document.createElement('li');
    li.className = 'ev-upload-item';

    const head = document.createElement('div');
    head.className = 'd-flex align-items-center justify-content-between gap-2';

    const name = document.createElement('div');
    name.className = 'text-truncate fw-medium';
    name.textContent = item.file.name;
    const size = document.createElement('span');
    size.className = 'text-muted font-sm ms-2';
    size.textContent = formatSize(item.file.size);
    name.appendChild(size);

    const status = document.createElement('span');
    status.className = 'font-sm text-muted text-nowrap';
    status.dataset.role = 'status';
    status.textContent = statusLabel(item);

    head.append(name, status);

    const bar = document.createElement('div');
    bar.className = 'progress mt-2';
    bar.style.height = '6px';
    bar.setAttribute('role', 'progressbar');
    bar.setAttribute('aria-label', `Upload progress for ${item.file.name}`);
    const fill = document.createElement('div');
    fill.className = 'progress-bar';
    fill.style.width = item.progress + '%';
    bar.appendChild(fill);

    li.append(head, bar);

    if (!submit.disabled && item.status === 'queued') {
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'btn btn-link btn-sm p-0 text-danger font-sm';
      remove.textContent = 'Remove';
      remove.addEventListener('click', () => {
        items.splice(index, 1);
        render();
      });
      head.appendChild(remove);
    }

    item.refs = { status, fill, li };
    return li;
  }

  function render() {
    queue.replaceChildren();
    items.forEach((item, index) => queue.appendChild(buildRow(item, index)));
    submit.disabled = items.length === 0;
  }

  function update(item, changes) {
    Object.assign(item, changes);
    if (!item.refs) return;
    item.refs.status.textContent = statusLabel(item);
    item.refs.fill.style.width = item.progress + '%';
    item.refs.li.classList.toggle('is-failed', item.status === 'failed');
  }

  function setFiles(fileList) {
    items = Array.from(fileList).map((file) => ({ file, status: 'queued', progress: 0, message: '' }));
    render();
    errorBox.classList.add('d-none');
  }

  function showError(text) {
    errorBox.textContent = text;
    errorBox.classList.remove('d-none');
  }

  function messageText(doc, selector) {
    const node = doc.querySelector(selector);
    return node ? node.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function uploadOne(item, total) {
    return new Promise((resolve) => {
      const data = new FormData(form);
      data.delete('file');
      if (total > 1) data.delete('title');
      data.append('file', item.file, item.file.name);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', form.action);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          update(item, { status: 'uploading', progress: Math.round((e.loaded / e.total) * 100) });
        }
      });

      xhr.addEventListener('load', () => {
        const doc = new DOMParser().parseFromString(xhr.responseText || '', 'text/html');
        let path = '';
        try {
          path = new URL(xhr.responseURL).pathname;
        } catch (err) {
          path = '';
        }
        const succeeded = xhr.status >= 200 && xhr.status < 400 && /^\/evidence\/\d+\/$/.test(path);
        if (succeeded) {
          update(item, { status: 'done', progress: 100 });
          resolve({ ok: true, url: xhr.responseURL, item });
          return;
        }
        const reason = messageText(doc, '.messages-container .alert-danger') || 'Rejected by the server.';
        update(item, { status: 'failed', message: reason });
        resolve({ ok: false, item, message: reason });
      });

      xhr.addEventListener('error', () => {
        update(item, { status: 'failed', message: 'Network error. Try again.' });
        resolve({ ok: false, item, message: 'Network error. Try again.' });
      });

      update(item, { status: 'uploading', progress: 0 });
      xhr.send(data);
    });
  }

  input.addEventListener('change', () => setFiles(input.files));

  dropzone.addEventListener('click', () => input.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      input.click();
    }
  });
  ['dragenter', 'dragover'].forEach((type) => {
    dropzone.addEventListener(type, (e) => {
      e.preventDefault();
      dropzone.classList.add('is-dragover');
    });
  });
  ['dragleave', 'drop'].forEach((type) => {
    dropzone.addEventListener(type, (e) => {
      e.preventDefault();
      dropzone.classList.remove('is-dragover');
    });
  });
  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length) setFiles(e.dataTransfer.files);
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const pending = items.filter((item) => item.status !== 'done');
    if (!pending.length) return;

    submit.disabled = true;
    errorBox.classList.add('d-none');
    const total = pending.length;
    const results = [];
    for (const item of pending) {
      results.push(await uploadOne(item, total));
    }

    const failures = results.filter((result) => !result.ok);
    if (!failures.length) {
      const last = results[results.length - 1];
      window.location.href = total === 1 ? last.url : doneUrl;
      return;
    }

    const succeeded = results.length - failures.length;
    showError(
      `${succeeded} of ${total} file(s) uploaded. ${failures.length} failed: ` +
      failures.map((failure) => `${failure.item.file.name} (${failure.message})`).join('; ') +
      '. Retry the failed files or continue to the evidence list.'
    );
    submit.disabled = false;
  });
})();
