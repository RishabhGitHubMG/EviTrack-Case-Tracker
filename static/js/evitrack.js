/**
 * EviTrack - Digital Evidence & Case Management System
 * Core Client-Side Utilities & Interactivity
 *
 * Modules:
 * 1. CSRF Helper
 * 2. Dark Mode Toggle
 * 3. Sidebar Collapsible & Mobile Drawer
 * 4. Session Inactivity & Auto-Logout Watchdog
 * 5. Toast Notification System
 * 6. Alert Auto-Dismissal
 * 7. Live Notification Bell Polling
 * 8. Live Global Search & Keyboard Shortcuts
 * 9. Drag-and-Drop File Upload Dropzone
 * 10. Confirmation Dialogs for Destructive Actions
 * 11. Hash Display & Copy-to-Clipboard
 * 12. Table Sorting & Filtering Utilities
 * 13. Relative Date & Time Formatter
 * 14. Multi-digit OTP Input Controller
 */

(function (window, document) {
  'use strict';

  // Global namespace
  const EviTrack = window.EviTrack || {};

  // Configuration defaults (can be overridden via window.EviTrackConfig in templates)
  const bodyData = document.body ? document.body.dataset : {};
  const Config = Object.assign(
    {
      csrfCookieName: 'csrftoken',
      themeStorageKey: 'evitrack_theme',
      sidebarStorageKey: 'evitrack_sidebar_collapsed',
      sessionWarningMinutes: 13,
      sessionTimeoutMinutes: 15,
      notificationPollIntervalMs: 30000,
    },
    {
      logoutUrl: bodyData.logoutUrl,
      sessionPingUrl: bodyData.sessionPingUrl,
      notificationCountUrl: bodyData.notificationCountUrl,
      searchApiUrl: bodyData.searchUrl,
      themeToggleUrl: bodyData.themeUrl,
      isAuthenticated: bodyData.authenticated === 'true',
    }
  );

  /* ==========================================================================
     1. CSRF HELPER
     ========================================================================== */

  /**
   * Retrieves the CSRF token from cookie or DOM element.
   * @returns {string} The CSRF token string.
   */
  EviTrack.getCsrfToken = function () {
    // 1. Try reading from cookie
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, Config.csrfCookieName.length + 1) === Config.csrfCookieName + '=') {
          cookieValue = decodeURIComponent(cookie.substring(Config.csrfCookieName.length + 1));
          break;
        }
      }
    }
    if (cookieValue) return cookieValue;

    // 2. Try meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.getAttribute('content')) {
      return metaTag.getAttribute('content');
    }

    // 3. Try hidden input
    const inputTag = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inputTag && inputTag.value) {
      return inputTag.value;
    }

    return '';
  };

  /* ==========================================================================
     2. DARK MODE TOGGLE
     ========================================================================== */

  /**
   * Applies the theme to the body and updates toggle icon.
   * @param {'light'|'dark'} theme
   * @param {boolean} persistRemote
   */
  EviTrack.setTheme = function (theme, persistRemote = true) {
    const isDark = theme === 'dark';
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem(Config.themeStorageKey, theme);

    // Update toggle icons in UI
    const themeIcons = document.querySelectorAll('.theme-toggle-icon');
    themeIcons.forEach((icon) => {
      if (isDark) {
        icon.classList.remove('bi-moon-stars');
        icon.classList.add('bi-sun-fill');
      } else {
        icon.classList.remove('bi-sun-fill');
        icon.classList.add('bi-moon-stars');
      }
    });

    // Notify listeners / custom event
    window.dispatchEvent(new CustomEvent('evitrack:themechange', { detail: { theme } }));

    // Send preference to server if user is authenticated
    if (persistRemote && Config.isAuthenticated && Config.themeToggleUrl) {
      fetch(Config.themeToggleUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': EviTrack.getCsrfToken(),
        },
        body: JSON.stringify({ theme: theme }),
      }).catch(() => {
        // Silently tolerate if server endpoint not yet mounted
      });
    }
  };

  /**
   * Initializes theme on load.
   */
  EviTrack.initTheme = function () {
    const savedTheme = localStorage.getItem(Config.themeStorageKey);
    const bodyTheme = document.body.getAttribute('data-theme');

    let activeTheme = 'light';
    if (savedTheme) {
      activeTheme = savedTheme;
    } else if (bodyTheme) {
      activeTheme = bodyTheme;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      activeTheme = 'dark';
    }

    EviTrack.setTheme(activeTheme, false);

    // Bind theme toggle buttons
    const toggleButtons = document.querySelectorAll('[data-action="toggle-theme"], #themeToggleBtn');
    toggleButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        EviTrack.setTheme(newTheme, true);
      });
    });
  };

  /* ==========================================================================
     3. SIDEBAR TOGGLE & MOBILE DRAWER
     ========================================================================== */

  EviTrack.initSidebar = function () {
    const appWrapper = document.querySelector('.app-wrapper');
    if (!appWrapper) return;

    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const mobileToggleBtn = document.getElementById('mobileSidebarToggle');
    const backdrop = document.querySelector('.sidebar-backdrop');

    // Restore desktop collapsed state
    const isCollapsed = localStorage.getItem(Config.sidebarStorageKey) === 'true';
    if (isCollapsed && window.innerWidth >= 992) {
      appWrapper.classList.add('sidebar-collapsed');
    }

    // Toggle desktop collapse
    if (collapseBtn) {
      collapseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const collapsed = appWrapper.classList.toggle('sidebar-collapsed');
        localStorage.setItem(Config.sidebarStorageKey, collapsed ? 'true' : 'false');
      });
    }

    // Toggle mobile drawer
    if (mobileToggleBtn) {
      mobileToggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        appWrapper.classList.toggle('sidebar-mobile-open');
      });
    }

    // Close mobile drawer on backdrop click
    if (backdrop) {
      backdrop.addEventListener('click', () => {
        appWrapper.classList.remove('sidebar-mobile-open');
      });
    }

    // Close mobile drawer when resizing back to desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 992 && appWrapper.classList.contains('sidebar-mobile-open')) {
        appWrapper.classList.remove('sidebar-mobile-open');
      }
    });
  };

  /* ==========================================================================
     4. SESSION INACTIVITY & AUTO-LOGOUT WATCHDOG
     ========================================================================== */

  EviTrack.initSessionWatchdog = function () {
    if (!Config.isAuthenticated) return;

    const warningMs = Config.sessionWarningMinutes * 60 * 1000;
    const timeoutMs = Config.sessionTimeoutMinutes * 60 * 1000;
    const modalEl = document.getElementById('sessionTimeoutModal');
    const countdownEl = document.getElementById('sessionCountdown');
    const progressBar = document.getElementById('sessionProgressBar');
    const staySignedInBtn = document.getElementById('sessionStaySignedInBtn');

    let lastActivityTime = Date.now();
    let isWarningShown = false;
    let modalInstance = null;

    // Initialize Bootstrap modal instance if Bootstrap is loaded
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
      modalInstance = new window.bootstrap.Modal(modalEl, {
        backdrop: 'static',
        keyboard: false,
      });
    }

    function recordActivity() {
      lastActivityTime = Date.now();
      if (isWarningShown && modalInstance) {
        modalInstance.hide();
        isWarningShown = false;
      }
    }

    // Throttled activity listener
    let activityThrottleTimer = null;
    ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach((evtName) => {
      window.addEventListener(
        evtName,
        () => {
          if (!activityThrottleTimer) {
            activityThrottleTimer = setTimeout(() => {
              recordActivity();
              activityThrottleTimer = null;
            }, 1000);
          }
        },
        { passive: true }
      );
    });

    if (staySignedInBtn) {
      staySignedInBtn.addEventListener('click', () => {
        recordActivity();
        // Optional ping to keep server session alive
        fetch(Config.sessionPingUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': EviTrack.getCsrfToken() },
        }).catch(() => {});
      });
    }

    // Watchdog ticker: checks every 1000ms
    setInterval(() => {
      const now = Date.now();
      const elapsed = now - lastActivityTime;
      const remainingTotal = timeoutMs - elapsed;

      if (elapsed >= timeoutMs) {
        // Auto-logout
        window.location.href = Config.logoutUrl + '?timeout=1';
        return;
      }

      if (elapsed >= warningMs) {
        const remainingSeconds = Math.max(0, Math.floor(remainingTotal / 1000));
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        if (countdownEl) {
          countdownEl.textContent = formattedTime;
        }

        if (progressBar) {
          const warningDuration = timeoutMs - warningMs;
          const currentWarningElapsed = elapsed - warningMs;
          const progressPercent = Math.max(0, 100 - (currentWarningElapsed / warningDuration) * 100);
          progressBar.style.width = `${progressPercent}%`;
        }

        if (!isWarningShown && modalInstance) {
          modalInstance.show();
          isWarningShown = true;
        }
      }
    }, 1000);
  };

  /* ==========================================================================
     5. TOAST NOTIFICATION SYSTEM
     ========================================================================== */

  /**
   * Displays a floating toast notification.
   * @param {string} message The text content or HTML string.
   * @param {'success'|'danger'|'warning'|'info'} type The alert type.
   * @param {number} duration Duration in milliseconds before auto-dismissal.
   */
  EviTrack.showToast = function (message, type = 'info', duration = 5000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `ev-toast toast-${type}`;

    let iconClass = 'bi-info-circle-fill';
    if (type === 'success') iconClass = 'bi-check-circle-fill';
    else if (type === 'danger' || type === 'error') iconClass = 'bi-exclamation-triangle-fill';
    else if (type === 'warning') iconClass = 'bi-exclamation-circle-fill';

    toast.innerHTML = `
      <div class="ev-toast-body">
        <i class="bi ${iconClass} ev-toast-icon"></i>
        <div class="ev-toast-message">${message}</div>
        <button type="button" class="ev-toast-close" aria-label="Close">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      <div class="ev-toast-progress"></div>
    `;

    container.appendChild(toast);

    const progressBar = toast.querySelector('.ev-toast-progress');
    if (progressBar && duration > 0) {
      progressBar.style.transition = `transform ${duration}ms linear`;
      requestAnimationFrame(() => {
        progressBar.style.transform = 'scaleX(0)';
      });
    }

    function removeToast() {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 250);
    }

    let timer = null;
    if (duration > 0) {
      timer = setTimeout(removeToast, duration);
    }

    const closeBtn = toast.querySelector('.ev-toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        if (timer) clearTimeout(timer);
        removeToast();
      });
    }
  };

  // Expose showToast globally for convenience
  window.showToast = EviTrack.showToast;

  /* ==========================================================================
     6. ALERT AUTO-DISMISSAL
     ========================================================================== */

  EviTrack.initAlertDismissal = function () {
    const alerts = document.querySelectorAll('.alert-dismissible:not(.alert-permanent)');
    alerts.forEach((alert) => {
      setTimeout(() => {
        alert.classList.add('fade');
        setTimeout(() => {
          if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
          }
        }, 300);
      }, 5000);
    });
  };

  /* ==========================================================================
     7. LIVE NOTIFICATION BELL POLLING
     ========================================================================== */

  EviTrack.initNotificationPolling = function () {
    if (!Config.isAuthenticated) return;

    const badge = document.querySelector('.topbar-badge-pulse');
    if (!badge) return;

    function pollUnread() {
      fetch(Config.notificationCountUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error('Network error');
        })
        .then((data) => {
          const count = typeof data.unread_count === 'number' ? data.unread_count : 0;
          if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        })
        .catch(() => {
          // Silent polling failure fallback
        });
    }

    // Poll periodically
    setInterval(pollUnread, Config.notificationPollIntervalMs);
  };

  /* ==========================================================================
     8. LIVE GLOBAL SEARCH & KEYBOARD SHORTCUTS
     ========================================================================== */

  EviTrack.initGlobalSearch = function () {
    const searchInput = document.getElementById('topbarSearchInput');
    const dropdown = document.getElementById('searchResultsDropdown');

    // Global keyboard shortcut: '/' to focus search input
    window.addEventListener('keydown', (e) => {
      if (
        e.key === '/' &&
        document.activeElement !== searchInput &&
        !['input', 'textarea', 'select'].includes(document.activeElement.tagName.toLowerCase()) &&
        !document.activeElement.isContentEditable
      ) {
        e.preventDefault();
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }
    });

    if (!searchInput || !dropdown) return;

    let debounceTimer = null;

    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      clearTimeout(debounceTimer);

      if (query.length < 2) {
        dropdown.classList.remove('show');
        dropdown.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`${Config.searchApiUrl}?q=${encodeURIComponent(query)}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
          .then((res) => res.json())
          .then((data) => {
            renderSearchResults(data, query);
          })
          .catch(() => {
            dropdown.innerHTML = `
              <div class="p-3 text-muted text-center font-sm">
                Search service momentarily unavailable.
              </div>
            `;
            dropdown.classList.add('show');
          });
      }, 250);
    });

    function renderSearchResults(data, query) {
      const results = data.results || [];
      if (results.length === 0) {
        dropdown.innerHTML = `
          <div class="p-3 text-center text-muted" style="font-size:0.85rem;">
            No records found for "<strong>${escapeHtml(query)}</strong>"
          </div>
        `;
        dropdown.classList.add('show');
        return;
      }

      // Group by category (e.g., Cases, Evidence, Persons)
      const grouped = {};
      results.forEach((item) => {
        const category = item.category || 'General';
        if (!grouped[category]) grouped[category] = [];
        grouped[category].push(item);
      });

      let html = '';
      for (const [category, items] of Object.entries(grouped)) {
        html += `<div class="search-result-group"><div class="search-result-group-title">${escapeHtml(category)}</div>`;
        items.forEach((item) => {
          html += `
            <a href="${item.url || '#'}" class="search-result-item">
              <i class="bi ${item.icon || 'bi-file-earmark'} text-muted"></i>
              <div class="d-flex flex-column">
                <span class="fw-semibold">${escapeHtml(item.title)}</span>
                <small class="text-muted">${escapeHtml(item.subtitle || '')}</small>
              </div>
            </a>
          `;
        });
        html += `</div>`;
      }

      dropdown.innerHTML = html;
      dropdown.classList.add('show');
    }

    // Close search dropdown on click outside or Esc key
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        dropdown.classList.remove('show');
        searchInput.blur();
      }
    });
  };

  /* ==========================================================================
     9. DRAG-AND-DROP FILE UPLOAD DROPZONE
     ========================================================================== */

  EviTrack.initDropzones = function () {
    const dropzones = document.querySelectorAll('.upload-dropzone, [data-dropzone]');

    dropzones.forEach((dropzone) => {
      const fileInput = dropzone.querySelector('input[type="file"]') || document.getElementById(dropzone.dataset.inputTarget);
      const previewList = dropzone.querySelector('.file-preview-list') || document.querySelector(dropzone.dataset.previewTarget);

      ['dragenter', 'dragover'].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('dragover');
        });
      });

      dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (fileInput && files.length) {
          fileInput.files = files;
          renderFiles(files, previewList);
        }
      });

      dropzone.addEventListener('click', (e) => {
        if (e.target !== fileInput && !e.target.closest('.file-preview-item')) {
          if (fileInput) fileInput.click();
        }
      });

      if (fileInput) {
        fileInput.addEventListener('change', () => {
          renderFiles(fileInput.files, previewList);
        });
      }
    });

    function renderFiles(files, container) {
      if (!container) return;
      container.innerHTML = '';

      Array.from(files).forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-preview-item';
        item.innerHTML = `
          <div class="d-flex align-items-center gap-2 overflow-hidden">
            <i class="bi bi-file-earmark-arrow-up text-amber"></i>
            <span class="text-truncate fw-medium">${escapeHtml(file.name)}</span>
            <span class="text-muted font-sm">(${formatFileSize(file.size)})</span>
          </div>
          <button type="button" class="btn btn-sm text-danger p-0 border-0" data-remove-index="${index}" title="Remove file">
            <i class="bi bi-x-circle-fill"></i>
          </button>
        `;
        container.appendChild(item);
      });
    }

    function formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
  };

  /* ==========================================================================
     10. CONFIRMATION DIALOGS FOR DESTRUCTIVE ACTIONS
     ========================================================================== */

  /**
   * Shows a confirmation modal/dialog before performing sensitive actions.
   * @param {Object} options Options containing title, message, confirmText, callback
   */
  EviTrack.confirmAction = function (options) {
    const title = options.title || 'Confirm Action';
    const message = options.message || 'Are you sure you want to proceed? This action may be irreversible.';
    const confirmText = options.confirmText || 'Confirm';
    const cancelText = options.cancelText || 'Cancel';
    const isDanger = options.danger !== false;

    // Build modal element dynamically
    const modalId = 'evConfirmationModal_' + Date.now();
    const modalDiv = document.createElement('div');
    modalDiv.className = 'modal fade';
    modalDiv.id = modalId;
    modalDiv.setAttribute('tabindex', '-1');
    modalDiv.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title ${isDanger ? 'text-danger' : ''}">${escapeHtml(title)}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p class="mb-0 text-secondary">${escapeHtml(message)}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-ev-outline" data-bs-dismiss="modal">${escapeHtml(cancelText)}</button>
            <button type="button" class="btn ${isDanger ? 'btn-danger' : 'btn-ev-primary'}" id="${modalId}_confirmBtn">${escapeHtml(confirmText)}</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modalDiv);

    if (window.bootstrap && window.bootstrap.Modal) {
      const modal = new window.bootstrap.Modal(modalDiv);
      modal.show();

      const confirmBtn = document.getElementById(`${modalId}_confirmBtn`);
      confirmBtn.addEventListener('click', () => {
        modal.hide();
        if (typeof options.onConfirm === 'function') {
          options.onConfirm();
        }
      });

      modalDiv.addEventListener('hidden.bs.modal', () => {
        modalDiv.remove();
      });
    } else {
      // Fallback
      if (window.confirm(`${title}\n\n${message}`)) {
        if (typeof options.onConfirm === 'function') {
          options.onConfirm();
        }
      }
    }
  };

  // Wire up [data-confirm] buttons automatically
  EviTrack.initConfirmTriggers = function () {
    document.addEventListener('click', (e) => {
      const target = e.target.closest('[data-confirm]');
      if (!target) return;

      e.preventDefault();
      const message = target.getAttribute('data-confirm');
      const title = target.getAttribute('data-confirm-title') || 'Confirm Action';
      const isDanger = target.getAttribute('data-confirm-danger') !== 'false';

      EviTrack.confirmAction({
        title: title,
        message: message,
        danger: isDanger,
        onConfirm: () => {
          if (target.tagName.toLowerCase() === 'a') {
            window.location.href = target.href;
          } else if (target.type === 'submit' && target.form) {
            target.form.submit();
          }
        },
      });
    });
  };

  /* ==========================================================================
     11. HASH DISPLAY & COPY-TO-CLIPBOARD
     ========================================================================== */

  EviTrack.initHashHelpers = function () {
    document.addEventListener('click', (e) => {
      const copyBtn = e.target.closest('.hash-copy-btn, [data-copy-hash]');
      if (!copyBtn) return;

      e.preventDefault();
      const targetHash = copyBtn.getAttribute('data-hash') || copyBtn.closest('.evidence-hash-box')?.querySelector('.hash-display')?.textContent?.trim();

      if (targetHash && navigator.clipboard) {
        navigator.clipboard
          .writeText(targetHash)
          .then(() => {
            const icon = copyBtn.querySelector('i');
            if (icon) {
              const originalClass = icon.className;
              icon.className = 'bi bi-check2 text-success';
              setTimeout(() => {
                icon.className = originalClass;
              }, 1500);
            }
            EviTrack.showToast('Evidence hash copied to clipboard.', 'success', 3000);
          })
          .catch(() => {
            EviTrack.showToast('Unable to copy hash to clipboard.', 'warning', 3000);
          });
      }
    });
  };

  /* ==========================================================================
     12. TABLE SORTING & FILTERING UTILITIES
     ========================================================================== */

  EviTrack.initTableSorting = function () {
    const sortableHeaders = document.querySelectorAll('th.sortable[data-sort-key]');
    sortableHeaders.forEach((th) => {
      th.addEventListener('click', () => {
        const url = new URL(window.location.href);
        const sortKey = th.getAttribute('data-sort-key');
        const currentSort = url.searchParams.get('sort');

        if (currentSort === sortKey) {
          url.searchParams.set('sort', `-${sortKey}`);
        } else if (currentSort === `-${sortKey}`) {
          url.searchParams.delete('sort');
        } else {
          url.searchParams.set('sort', sortKey);
        }

        window.location.href = url.toString();
      });
    });
  };

  /* ==========================================================================
     13. RELATIVE DATE & TIME FORMATTER
     ========================================================================== */

  EviTrack.timeAgo = function (dateInput) {
    const date = new Date(dateInput);
    if (isNaN(date.getTime())) return '';

    const seconds = Math.floor((new Date() - date) / 1000);
    const intervals = [
      { label: 'year', seconds: 31536000 },
      { label: 'month', seconds: 2592000 },
      { label: 'day', seconds: 86400 },
      { label: 'hour', seconds: 3600 },
      { label: 'minute', seconds: 60 },
      { label: 'second', seconds: 1 },
    ];

    if (seconds < 5) return 'Just now';

    for (let i = 0; i < intervals.length; i++) {
      const interval = intervals[i];
      const count = Math.floor(seconds / interval.seconds);
      if (count >= 1) {
        return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
      }
    }
    return 'Just now';
  };

  EviTrack.formatRelativeDates = function () {
    const timeElements = document.querySelectorAll('[data-relative-time]');
    timeElements.forEach((el) => {
      const rawDate = el.getAttribute('data-relative-time');
      if (rawDate) {
        el.textContent = EviTrack.timeAgo(rawDate);
      }
    });
  };

  /* ==========================================================================
     14. MULTI-DIGIT OTP INPUT CONTROLLER
     ========================================================================== */

  EviTrack.initOtpInputs = function () {
    const otpGroups = document.querySelectorAll('.otp-input-group');
    otpGroups.forEach((group) => {
      const inputs = group.querySelectorAll('.otp-digit');

      inputs.forEach((input, index) => {
        // Auto-advance on input
        input.addEventListener('input', (e) => {
          const val = e.target.value;
          if (val.length === 1 && index < inputs.length - 1) {
            inputs[index + 1].focus();
          }
        });

        // Backspace to previous
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Backspace' && !input.value && index > 0) {
            inputs[index - 1].focus();
          }
        });

        // Paste whole 6-digit OTP
        input.addEventListener('paste', (e) => {
          e.preventDefault();
          const pastedData = (e.clipboardData || window.clipboardData).getData('text').trim();
          if (/^\d{6}$/.test(pastedData)) {
            pastedData.split('').forEach((char, i) => {
              if (inputs[i]) inputs[i].value = char;
            });
            inputs[inputs.length - 1].focus();
          }
        });
      });
    });
  };

  /* ==========================================================================
     HELPER: HTML ESCAPER
     ========================================================================== */

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /* ==========================================================================
     GLOBAL INITIALIZATION ON DOM READY
     ========================================================================== */

  document.addEventListener('DOMContentLoaded', () => {
    EviTrack.initTheme();
    EviTrack.initSidebar();
    EviTrack.initSessionWatchdog();
    EviTrack.initAlertDismissal();
    EviTrack.initNotificationPolling();
    EviTrack.initGlobalSearch();
    EviTrack.initDropzones();
    EviTrack.initConfirmTriggers();
    EviTrack.initHashHelpers();
    EviTrack.initTableSorting();
    EviTrack.formatRelativeDates();
    EviTrack.initOtpInputs();

    // Re-format relative dates every 60 seconds
    setInterval(EviTrack.formatRelativeDates, 60000);
  });

  // Attach to window
  window.EviTrack = EviTrack;
})(window, document);
