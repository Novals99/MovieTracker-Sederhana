'use strict';

/**
 * filter.js — Search, Genre, Status, Sort, and Year/Rating Filters
 *
 * Responsibilities:
 *  - Wire all filter/sort UI controls to AppState
 *  - Debounce live search and year inputs
 *  - Populate the genre dropdown from GET /genres
 *  - Sync sidebar status filter active state
 *  - Trigger MovieGrid.load() whenever a filter changes
 */
const Filter = (() => {

  // ── Apply & Load ────────────────────────────────────────

  /**
   * Reset to page 1 and reload the movie grid.
   * Called after any filter value changes.
   */
  async function _applyAndLoad() {
    AppState.currentPage = 1;
    await MovieGrid.load();
  }

  // ── Sidebar Status Sync ──────────────────────────────────

  /**
   * Update the active state of all sidebar status-filter nav items.
   * @param {string} status — '' means All Movies
   */
  function syncStatusHighlight(status) {
    document.querySelectorAll('.status-filter').forEach((btn) => {
      btn.classList.toggle('nav-item--active', btn.dataset.status === status);
    });
  }

  // ── Genre Dropdown ───────────────────────────────────────

  /**
   * Fetch all distinct genres from the backend and populate
   * the genre <select> dropdown.
   */
  async function _loadGenres() {
    try {
      const response = await API.getGenres();
      const genres   = response.data || [];
      AppState.genres = genres;

      const select = document.getElementById('filter-genre');
      if (!select) return;

      select.innerHTML = '<option value="">All Genres</option>';
      genres.forEach((g) => {
        const opt = document.createElement('option');
        opt.value       = g;
        opt.textContent = g;
        select.appendChild(opt);
      });
    } catch (err) {
      console.warn('[Filter] Failed to load genres:', err.message);
    }
  }

  // ── Init ────────────────────────────────────────────────

  /**
   * Wire all filter UI controls to their AppState properties.
   * Call once during app initialization.
   */
  function init() {

    // ── Search ──────────────────────────────────────────
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');

    const _onSearch = Utils.debounce((query) => {
      AppState.searchQuery = query;
      _applyAndLoad();
    }, 420);

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (searchClear) searchClear.hidden = !val.trim();
        _onSearch(val.trim());
      });
    }

    if (searchClear) {
      searchClear.addEventListener('click', () => {
        if (searchInput) {
          searchInput.value = '';
          searchInput.focus();
        }
        searchClear.hidden    = true;
        AppState.searchQuery  = '';
        _applyAndLoad();
      });
    }

    // ── Genre Filter ────────────────────────────────────
    const genreSelect = document.getElementById('filter-genre');
    if (genreSelect) {
      genreSelect.addEventListener('change', (e) => {
        AppState.filters.genre = e.target.value;
        _applyAndLoad();
      });
    }

    // ── Minimum Rating Filter ────────────────────────────
    const ratingSelect = document.getElementById('filter-rating');
    if (ratingSelect) {
      ratingSelect.addEventListener('change', (e) => {
        AppState.filters.rating = e.target.value;
        _applyAndLoad();
      });
    }

    // ── Release Year Filter (debounced) ──────────────────
    const yearInput = document.getElementById('filter-year');
    const _onYear   = Utils.debounce((val) => {
      AppState.filters.release_year = val;
      _applyAndLoad();
    }, 600);

    if (yearInput) {
      yearInput.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        // Only trigger if empty or a plausible 4-digit year
        if (val === '' || (val.length === 4 && !isNaN(Number(val)))) {
          _onYear(val);
        }
      });
    }

    // ── Sort ─────────────────────────────────────────────
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const [by, order] = e.target.value.split(':');
        AppState.sortBy    = by;
        AppState.sortOrder = order;
        AppState.currentPage = 1;
        MovieGrid.load();
      });
    }

    // ── Sidebar Status Filters ────────────────────────────
    document.querySelectorAll('.status-filter').forEach((btn) => {
      btn.addEventListener('click', () => {
        const status = btn.dataset.status; // '' = all
        AppState.filters.status = status;
        syncStatusHighlight(status);
        _applyAndLoad();
      });
    });

    // Set initial active state (All Movies = '' is active by default)
    syncStatusHighlight('');

    // Populate genre dropdown on init
    _loadGenres();
  }

  // ── Public API ──────────────────────────────────────────
  return { init, syncStatusHighlight };

})();
