'use strict';

/**
 * pagination.js — Pagination Controls Module
 *
 * Renders page number buttons with ellipsis for large page counts.
 * Wires click handlers that update AppState and reload the movie grid.
 */
const Pagination = (() => {

  /** Maximum number of visible page buttons (excluding prev/next). */
  const MAX_VISIBLE = 7;

  // ── Render ──────────────────────────────────────────────

  /**
   * Render the full pagination control.
   * @param {number} page      — current page (1-indexed)
   * @param {number} pages     — total number of pages
   * @param {number} total     — total number of records
   * @param {number} perPage   — records per page
   */
  function render(page, pages, total, perPage) {
    _updateResultsCount(page, pages, total, perPage);

    const container = document.getElementById('pagination');
    if (!container) return;

    // No pagination needed for a single page or empty result
    if (pages <= 1) {
      container.innerHTML = '';
      return;
    }

    const pageNums = _buildPageNumbers(page, pages);
    container.innerHTML = _buildHtml(page, pages, pageNums);
    _wireEvents(container, pages);
  }

  // ── Results Count ───────────────────────────────────────

  function _updateResultsCount(page, pages, total, perPage) {
    const el = document.getElementById('results-count');
    if (!el) return;

    if (total === 0) {
      el.textContent = 'No movies';
      return;
    }

    const from = (page - 1) * perPage + 1;
    const to   = Math.min(page * perPage, total);
    el.textContent = `${from}–${to} of ${total} movie${total !== 1 ? 's' : ''}`;
  }

  // ── Page Number Array ────────────────────────────────────

  /**
   * Build the array of page numbers (and '...' ellipsis markers)
   * to display. Always shows first, last, and up to MAX_VISIBLE
   * pages around the current page.
   *
   * @param {number} current — current page
   * @param {number} total   — total pages
   * @returns {Array<number|'...'>}
   */
  function _buildPageNumbers(current, total) {
    // Show all if fits within max
    if (total <= MAX_VISIBLE) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    const half   = Math.floor((MAX_VISIBLE - 2) / 2); // exclude first/last
    let start = Math.max(2, current - half);
    let end   = Math.min(total - 1, current + half);

    // Clamp if too close to start or end
    if (current - 1 <= half)          end   = MAX_VISIBLE - 2;
    if (total - current <= half)      start = total - MAX_VISIBLE + 3;

    const pages = [1];
    if (start > 2)       pages.push('...');
    for (let i = start; i <= end; i++) pages.push(i);
    if (end < total - 1) pages.push('...');
    pages.push(total);

    return pages;
  }

  // ── HTML Builder ─────────────────────────────────────────

  function _buildHtml(page, pages, pageNums) {
    const prevDisabled = page <= 1    ? 'disabled' : '';
    const nextDisabled = page >= pages ? 'disabled' : '';

    const pageButtons = pageNums.map((p) =>
      p === '...'
        ? `<span class="pagination__ellipsis" aria-hidden="true">…</span>`
        : `<button
            class="pagination__page${p === page ? ' pagination__page--active' : ''}"
            data-page="${p}"
            aria-label="Go to page ${p}"
            ${p === page ? 'aria-current="page"' : ''}
           >${p}</button>`
    ).join('');

    return `
      <div class="pagination__inner">
        <button
          class="pagination__btn"
          data-page="${page - 1}"
          ${prevDisabled}
          aria-label="Previous page"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>

        <div class="pagination__pages">${pageButtons}</div>

        <button
          class="pagination__btn"
          data-page="${page + 1}"
          ${nextDisabled}
          aria-label="Next page"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </div>
    `;
  }

  // ── Event Wiring ─────────────────────────────────────────

  function _wireEvents(container, pages) {
    container.querySelectorAll('[data-page]').forEach((btn) => {
      if (btn.disabled) return;
      btn.addEventListener('click', () => {
        const p = parseInt(btn.dataset.page, 10);
        if (isNaN(p) || p < 1 || p > pages) return;

        AppState.currentPage = p;
        MovieGrid.load();

        // Smooth scroll to movie grid
        document.getElementById('section-collection')
          ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  // ── Public API ──────────────────────────────────────────
  return { render };

})();
