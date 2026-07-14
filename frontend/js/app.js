'use strict';

/**
 * app.js — Application Entry Point & Bootstrap
 *
 * Defines AppState (the single source of truth for all UI state)
 * and initialises every module in the correct dependency order.
 *
 * Script load order in index.html must be:
 *   utils.js → api.js → dashboard.js → pagination.js
 *   → movie.js → modal.js → filter.js → app.js
 */

// ── AppState — Single Source of Truth ──────────────────────
/**
 * All reactive state lives here. Modules read from and write to
 * this object. No module stores its own local state for shared
 * concerns (e.g., current page, active filters).
 */
const AppState = {
  currentPage:  1,
  perPage:      12,
  totalPages:   1,
  totalMovies:  0,
  searchQuery:  '',
  filters: {
    genre:        '',
    status:       '',
    rating:       '',
    release_year: '',
  },
  sortBy:    'created_at',
  sortOrder: 'desc',
  genres:    [],
  isLoading: false,
};

// ── Bootstrap ────────────────────────────────────────────────
async function initApp() {

  // ── 1. Sidebar toggle (desktop + mobile) ──────────────────
  const sidebar     = document.getElementById('sidebar');
  const mainWrapper = document.querySelector('.main-wrapper');
  const toggleBtn   = document.getElementById('btn-sidebar-toggle');
  const backdrop    = document.getElementById('sidebar-backdrop');

  const isMobile = () => window.innerWidth <= 768;

  function openSidebar() {
    sidebar.classList.add('sidebar--open');
    sidebar.classList.remove('sidebar--collapsed');
    backdrop?.classList.add('sidebar-backdrop--visible');
    toggleBtn?.setAttribute('aria-expanded', 'true');
  }

  function closeSidebar() {
    if (isMobile()) {
      sidebar.classList.remove('sidebar--open');
      backdrop?.classList.remove('sidebar-backdrop--visible');
    } else {
      sidebar.classList.add('sidebar--collapsed');
      mainWrapper?.classList.add('main-wrapper--expanded');
    }
    toggleBtn?.setAttribute('aria-expanded', 'false');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (isMobile()) {
        sidebar.classList.contains('sidebar--open') ? closeSidebar() : openSidebar();
      } else {
        const isCollapsed = sidebar.classList.toggle('sidebar--collapsed');
        mainWrapper?.classList.toggle('main-wrapper--expanded', isCollapsed);
        toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
      }
    });
  }

  // Clicking the backdrop on mobile closes the sidebar
  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  // ── 2. "Add Movie" button ──────────────────────────────────
  document.getElementById('btn-add-movie')
    ?.addEventListener('click', () => Modal.openAdd());

  // ── 3. Initialise sub-modules ──────────────────────────────
  Modal.init();   // Wire modal events (submit, delete, close, escape)
  Filter.init();  // Wire search, genre, status, sort, year controls

  // ── 4. Backend health check ────────────────────────────────
  try {
    await API.getHealth();
  } catch (err) {
    Utils.showToast(
      'Cannot connect to the backend. Ensure Flask is running on port 5000.',
      'error',
      8000
    );
    console.error('[App] Backend health check failed:', err.message);
  }

  // ── 5. Load initial data ───────────────────────────────────
  // Run both in parallel for faster first paint
  await Promise.all([
    Dashboard.load(),
    MovieGrid.load(),
  ]);
}

// Boot when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
