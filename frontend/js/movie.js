'use strict';

/**
 * movie.js — Movie Grid Module
 *
 * Responsibilities:
 *  - Build API params from AppState
 *  - Show skeleton loading state
 *  - Fetch movies from GET /movies
 *  - Render movie cards into the grid
 *  - Handle empty and error states
 *  - Wire card click (details), edit, and delete actions
 */
const MovieGrid = (() => {

  // ── Param Builder ───────────────────────────────────────

  /**
   * Build the query params object from the current AppState.
   * Only non-empty values are included — api.js will filter nulls.
   * @returns {object}
   */
  function _buildParams() {
    const { currentPage, perPage, sortBy, sortOrder, searchQuery, filters } = AppState;
    const params = {
      page:       currentPage,
      per_page:   perPage,
      sort_by:    sortBy,
      sort_order: sortOrder,
    };

    if (searchQuery)          params.q            = searchQuery;
    if (filters.genre)        params.genre        = filters.genre;
    if (filters.status)       params.status       = filters.status;
    if (filters.rating)       params.rating       = filters.rating;
    if (filters.release_year) params.release_year = filters.release_year;

    return params;
  }

  // ── Load ────────────────────────────────────────────────

  /**
   * Fetch movies using current AppState and render results.
   * Guards against concurrent calls with AppState.isLoading.
   */
  async function load() {
    if (AppState.isLoading) return;
    AppState.isLoading = true;

    const grid = document.getElementById('movie-grid');
    if (!grid) { AppState.isLoading = false; return; }

    // Immediately show skeleton cards
    grid.innerHTML = Utils.createSkeletonCards(AppState.perPage);
    grid.classList.remove('movie-grid--empty');

    try {
      const params   = _buildParams();
      const response = await API.getMovies(params);

      AppState.totalMovies = response.total;
      AppState.totalPages  = response.pages;

      if (!response.data || response.data.length === 0) {
        const emptyMsg = AppState.searchQuery
          ? `No results for "${AppState.searchQuery}"`
          : 'Your collection is empty';
        Utils.showEmptyState(grid, emptyMsg);
        grid.classList.add('movie-grid--empty');
        Pagination.render(1, 0, 0, AppState.perPage);
      } else {
        _render(grid, response.data);
        Pagination.render(response.page, response.pages, response.total, response.per_page);
      }

    } catch (err) {
      console.error('[MovieGrid] Failed to load:', err.message);
      Utils.showErrorState(grid, err.isNetworkError
        ? 'Cannot connect to the backend server'
        : err.message || 'Failed to load movies'
      );
      grid.classList.add('movie-grid--empty');
      Pagination.render(1, 0, 0, AppState.perPage);

    } finally {
      AppState.isLoading = false;
    }
  }

  // ── Render ──────────────────────────────────────────────

  /**
   * Clear the grid and insert one card per movie.
   * @param {HTMLElement} grid
   * @param {Array<object>} movies
   */
  function _render(grid, movies) {
    grid.innerHTML = '';
    const fragment = document.createDocumentFragment();
    movies.forEach((movie) => fragment.appendChild(_createCard(movie)));
    grid.appendChild(fragment);
  }

  // ── Card Builder ─────────────────────────────────────────

  /**
   * Build and return a movie card DOM element.
   * @param {object} movie
   * @returns {HTMLElement}
   */
  function _createCard(movie) {
    const card = document.createElement('article');
    card.className  = 'movie-card';
    card.setAttribute('role', 'listitem');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', `${movie.title} — ${movie.status}`);
    card.dataset.movieId = movie.id;

    const statusClass = Utils.getStatusClass(movie.status);
    const rating      = Utils.formatRating(movie.rating);
    const duration    = Utils.formatDuration(movie.duration);
    const [gradFrom, gradTo] = Utils.stringToGradient(movie.title);
    const hasPoster   = movie.poster_url && movie.poster_url.trim() !== '';
    const safeTitle   = Utils.escapeHtml(movie.title);
    const safeGenre   = Utils.escapeHtml(movie.genre);

    card.innerHTML = `
      <div class="movie-card__poster-wrap">

        ${hasPoster ? `
          <img
            class="movie-card__poster"
            src="${Utils.escapeHtml(movie.poster_url)}"
            alt="${safeTitle} poster"
            loading="lazy"
            onerror="
              this.style.display='none';
              this.nextElementSibling.style.display='flex';
            "
          >
          <div class="movie-card__poster-fallback"
               style="--grad-from:${gradFrom};--grad-to:${gradTo};display:none;">
            <span class="movie-card__poster-letter">${movie.title.charAt(0).toUpperCase()}</span>
          </div>
        ` : `
          <div class="movie-card__poster-fallback"
               style="--grad-from:${gradFrom};--grad-to:${gradTo};">
            <span class="movie-card__poster-letter">${movie.title.charAt(0).toUpperCase()}</span>
          </div>
        `}

        <span class="badge badge--${statusClass} movie-card__status"
              aria-label="Status: ${movie.status}">
          ${movie.status}
        </span>

        <div class="movie-card__overlay" aria-hidden="true">
          <button
            class="btn btn--icon btn--sm"
            data-action="edit"
            data-id="${movie.id}"
            aria-label="Edit ${safeTitle}"
            tabindex="-1"
          >
            <!-- Pencil icon -->
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button
            class="btn btn--icon btn--sm btn--danger-ghost"
            data-action="delete"
            data-id="${movie.id}"
            aria-label="Delete ${safeTitle}"
            tabindex="-1"
          >
            <!-- Trash icon -->
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
                 stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
              <path d="M10 11v6M14 11v6"/>
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="movie-card__info">
        <h3 class="movie-card__title">${safeTitle}</h3>
        <div class="movie-card__meta">
          <span class="movie-card__genre">${safeGenre}</span>
          <span class="movie-card__meta-sep">•</span>
          <span class="movie-card__year">${movie.release_year}</span>
        </div>
        <div class="movie-card__footer">
          <span class="movie-card__rating">
            <svg class="star-icon" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            ${rating}
          </span>
          <span class="movie-card__duration">${duration}</span>
        </div>
      </div>
    `;

    _wireCardEvents(card, movie);
    return card;
  }

  // ── Event Wiring ─────────────────────────────────────────

  /**
   * Attach click and keyboard events to a movie card.
   * - Card click → open details modal
   * - Edit button → open edit modal
   * - Delete button → open delete confirmation
   * @param {HTMLElement} card
   * @param {object} movie
   */
  function _wireCardEvents(card, movie) {
    // Click anywhere on card → details modal
    card.addEventListener('click', async (e) => {
      if (e.target.closest('[data-action]')) return; // handled below
      try {
        const response = await API.getMovieById(movie.id);
        Modal.openDetails(response.data);
      } catch (err) {
        Utils.showToast('Failed to load movie details.', 'error');
      }
    });

    // Keyboard: Enter or Space → same as click
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
      }
    });

    // Action buttons
    card.querySelectorAll('[data-action]').forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const { action, id } = btn.dataset;
        const movieId = parseInt(id, 10);

        if (action === 'edit') {
          try {
            const response = await API.getMovieById(movieId);
            Modal.openEdit(response.data);
          } catch (err) {
            Utils.showToast('Failed to load movie for editing.', 'error');
          }
        } else if (action === 'delete') {
          // Use the already-loaded movie object for the confirm dialog
          Modal.openDelete(movie);
        }
      });
    });
  }

  // ── Public API ──────────────────────────────────────────
  return { load };

})();
