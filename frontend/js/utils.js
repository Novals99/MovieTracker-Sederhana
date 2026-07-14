'use strict';

/**
 * utils.js — Utility functions
 *
 * A collection of pure helper functions shared across all modules.
 * No DOM side-effects except showToast() and createSkeletonCards().
 */
const Utils = (() => {

  // ── Timing ─────────────────────────────────────────────

  /**
   * Returns a debounced version of fn that delays invocation by `delay` ms.
   * @param {Function} fn
   * @param {number} delay
   * @returns {Function}
   */
  function debounce(fn, delay) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // ── Formatting ──────────────────────────────────────────

  /**
   * Format minutes into "1h 42m" or "95m" format.
   * @param {number} minutes
   * @returns {string}
   */
  function formatDuration(minutes) {
    if (!minutes || minutes <= 0) return 'N/A';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  }

  /**
   * Format an ISO datetime string to a readable date.
   * @param {string|null} isoString
   * @returns {string}
   */
  function formatDate(isoString) {
    if (!isoString) return 'N/A';
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'N/A';
    }
  }

  /**
   * Format a numeric rating to one decimal place.
   * @param {number|null} rating
   * @returns {string}
   */
  function formatRating(rating) {
    if (rating === null || rating === undefined || isNaN(Number(rating))) return 'N/A';
    return Number(rating).toFixed(1);
  }

  // ── Status Helpers ──────────────────────────────────────

  /**
   * Map a status string to its CSS modifier class name.
   * @param {string} status
   * @returns {string}
   */
  function getStatusClass(status) {
    const map = {
      'Watching':     'watching',
      'Completed':    'completed',
      'Plan to Watch':'plan',
      'Dropped':      'dropped',
    };
    return map[status] || 'plan';
  }

  // ── Poster Placeholder ──────────────────────────────────

  /**
   * Deterministically pick a gradient color pair from a string hash.
   * Used for generating unique poster placeholder backgrounds.
   * @param {string} str
   * @returns {[string, string]} [from, to] color strings
   */
  function stringToGradient(str) {
    const palettes = [
      ['#6366f1', '#8b5cf6'], // indigo → violet
      ['#3b82f6', '#0ea5e9'], // blue → sky
      ['#10b981', '#14b8a6'], // emerald → teal
      ['#f59e0b', '#ef4444'], // amber → red
      ['#ec4899', '#8b5cf6'], // pink → violet
      ['#0ea5e9', '#6366f1'], // sky → indigo
      ['#14b8a6', '#22c55e'], // teal → green
      ['#f97316', '#dc2626'], // orange → red
    ];
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return palettes[Math.abs(hash) % palettes.length];
  }

  // ── DOM Helpers ─────────────────────────────────────────

  /**
   * Escape HTML special characters to prevent XSS.
   * @param {string} str
   * @returns {string}
   */
  function escapeHtml(str) {
    const el = document.createElement('div');
    el.textContent = String(str);
    return el.innerHTML;
  }

  // ── Loading States ──────────────────────────────────────

  /**
   * Generate HTML string for N skeleton movie cards.
   * @param {number} count
   * @returns {string}
   */
  function createSkeletonCards(count = 12) {
    return Array.from({ length: count }, () => `
      <div class="movie-card movie-card--skeleton" aria-hidden="true">
        <div class="skeleton-poster skeleton-line"></div>
        <div class="movie-card__info">
          <div class="skeleton-line skeleton-line--title"></div>
          <div class="skeleton-line skeleton-line--meta"></div>
          <div class="skeleton-line skeleton-line--meta skeleton-line--short"></div>
        </div>
      </div>
    `).join('');
  }

  /**
   * Render an empty state into a container element.
   * @param {HTMLElement} container
   * @param {string} message
   * @param {string} icon — emoji
   */
  function showEmptyState(container, message = 'No movies found', icon = '🎬') {
    container.innerHTML = `
      <div class="empty-state" role="status" aria-live="polite">
        <div class="empty-state__icon">${icon}</div>
        <h3 class="empty-state__title">${escapeHtml(message)}</h3>
        <p class="empty-state__subtitle">
          Try adjusting your filters or add a new movie to your collection.
        </p>
      </div>
    `;
  }

  /**
   * Render an error state into a container element.
   * @param {HTMLElement} container
   * @param {string} message
   */
  function showErrorState(container, message = 'Something went wrong') {
    container.innerHTML = `
      <div class="empty-state error-state" role="alert">
        <div class="empty-state__icon">⚠️</div>
        <h3 class="empty-state__title">${escapeHtml(message)}</h3>
        <p class="empty-state__subtitle">
          Please ensure the backend server is running and try again.
        </p>
        <button class="btn btn--primary" onclick="MovieGrid.load()" style="margin-top:1rem">
          Retry
        </button>
      </div>
    `;
  }

  // ── Toast Notifications ─────────────────────────────────

  /**
   * Display a toast notification.
   * @param {string} message
   * @param {'success'|'error'|'warning'|'info'} type
   * @param {number} duration — auto-dismiss delay in ms
   */
  function showToast(message, type = 'success', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.innerHTML = `
      <span class="toast__icon">${icons[type] || icons.info}</span>
      <span class="toast__message">${escapeHtml(message)}</span>
      <button class="toast__close" aria-label="Dismiss notification">×</button>
    `;

    toast.querySelector('.toast__close').addEventListener('click', () => _dismiss(toast));
    container.appendChild(toast);

    // Trigger CSS transition on next frame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => toast.classList.add('toast--visible'));
    });

    toast._timer = setTimeout(() => _dismiss(toast), duration);
    return toast;
  }

  function _dismiss(toast) {
    clearTimeout(toast._timer);
    toast.classList.remove('toast--visible');
    toast.classList.add('toast--hiding');
    setTimeout(() => toast.parentNode?.removeChild(toast), 350);
  }

  // ── Public API ──────────────────────────────────────────
  return {
    debounce,
    formatDuration,
    formatDate,
    formatRating,
    getStatusClass,
    stringToGradient,
    escapeHtml,
    createSkeletonCards,
    showEmptyState,
    showErrorState,
    showToast,
  };

})();
