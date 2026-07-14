'use strict';

/**
 * dashboard.js — Dashboard Statistics Module
 *
 * Fetches collection stats from GET /dashboard and renders
 * animated count-up values into the stat cards in the DOM.
 */
const Dashboard = (() => {

  /** Map each DOM element ID to a function that extracts its value from the data. */
  const STAT_MAP = {
    'stat-total-value':     (d) => ({ value: d.total_movies,    isNumber: true  }),
    'stat-watching-value':  (d) => ({ value: d.watching,        isNumber: true  }),
    'stat-completed-value': (d) => ({ value: d.completed,       isNumber: true  }),
    'stat-plan-value':      (d) => ({ value: d.plan_to_watch,   isNumber: true  }),
    'stat-dropped-value':   (d) => ({ value: d.dropped,         isNumber: true  }),
    'stat-rating-value':    (d) => ({ value: d.average_rating,  isNumber: false,
                                      display: `${Number(d.average_rating).toFixed(1)}` }),
  };

  // ── Loading State ───────────────────────────────────────

  /** Show placeholder dashes while data loads. */
  function setLoading() {
    Object.keys(STAT_MAP).forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = '—';
        el.classList.add('stat-card__value--loading');
      }
    });
  }

  // ── Render ──────────────────────────────────────────────

  /**
   * Render stat values into the DOM with a count-up animation.
   * @param {object} data — response.data from GET /dashboard
   */
  function render(data) {
    Object.entries(STAT_MAP).forEach(([id, extractor]) => {
      const el = document.getElementById(id);
      if (!el) return;

      el.classList.remove('stat-card__value--loading');
      const { value, isNumber, display } = extractor(data);

      if (isNumber && typeof value === 'number') {
        _animateCount(el, value);
      } else {
        el.textContent = display !== undefined ? display : String(value);
      }
    });
  }

  /**
   * Animate a number from 0 to `target` over `duration` ms.
   * Uses ease-out-cubic for a satisfying deceleration effect.
   * @param {HTMLElement} el
   * @param {number} target
   * @param {number} duration — ms
   */
  function _animateCount(el, target, duration = 900) {
    const startTime = Date.now();

    function tick() {
      const elapsed  = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic: decelerates toward the end
      const eased    = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(target * eased);

      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }

  // ── Load ────────────────────────────────────────────────

  /**
   * Fetch dashboard data and render stats.
   * Silently handles errors (stats show "Err" without crashing the app).
   */
  async function load() {
    setLoading();
    try {
      const response = await API.getDashboard();
      render(response.data);
    } catch (err) {
      console.error('[Dashboard] Failed to load stats:', err.message);
      // Show error indicator in each stat card
      Object.keys(STAT_MAP).forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          el.textContent = '—';
          el.classList.remove('stat-card__value--loading');
        }
      });
    }
  }

  // ── Public API ──────────────────────────────────────────
  return { load, render };

})();
