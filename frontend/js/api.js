'use strict';

/**
 * api.js — API Communication Layer
 *
 * All fetch() calls are centralised here.
 * No other module calls fetch() directly.
 *
 * Every function returns a Promise that resolves with the parsed
 * JSON response body on success, or rejects with an Error object
 * (with optional .errors[] array) on failure.
 */
const API = (() => {

  /** Base URL for the Flask backend. Change port here if needed. */
  const BASE_URL = 'http://localhost:5000';

  // ── Core Request Handler ────────────────────────────────

  /**
   * Universal fetch wrapper.
   * - Sets Content-Type: application/json
   * - Parses JSON response
   * - Throws descriptive errors on HTTP or network failure
   *
   * @param {string} endpoint — path relative to BASE_URL
   * @param {RequestInit} options — standard fetch options
   * @returns {Promise<object>}
   */
  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      // Backend always returns { success: bool, message: string, ... }
      if (!response.ok || !data.success) {
        const err = new Error(data.message || `HTTP ${response.status}`);
        err.errors  = data.errors  || [];
        err.status  = response.status;
        throw err;
      }

      return data;

    } catch (err) {
      // TypeError = network failure (server not running, CORS, etc.)
      if (err instanceof TypeError) {
        const netErr = new Error(
          'Cannot reach the server. Please ensure the Flask backend is running on port 5000.'
        );
        netErr.isNetworkError = true;
        throw netErr;
      }
      throw err;
    }
  }

  // ── Query String Builder ────────────────────────────────

  /**
   * Build a URL with query string from a params object.
   * Filters out empty strings, nulls, and undefined values.
   * @param {string} path
   * @param {object} params
   * @returns {string}
   */
  function buildUrl(path, params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    );
    const qs = new URLSearchParams(clean).toString();
    return qs ? `${path}?${qs}` : path;
  }

  // ── Movie Endpoints ─────────────────────────────────────

  /**
   * GET /movies — list, search, filter, sort, paginate all in one.
   * Supported params: q, genre, status, rating, release_year,
   *                   sort_by, sort_order, page, per_page
   * @param {object} params
   */
  function getMovies(params = {}) {
    return request(buildUrl('/movies', params));
  }

  /**
   * GET /movies/:id — single movie details
   * @param {number} id
   */
  function getMovieById(id) {
    return request(`/movies/${id}`);
  }

  /**
   * POST /movies — create a new movie
   * @param {object} payload
   */
  function createMovie(payload) {
    return request('/movies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * PUT /movies/:id — update an existing movie
   * @param {number} id
   * @param {object} payload
   */
  function updateMovie(id, payload) {
    return request(`/movies/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  /**
   * DELETE /movies/:id — remove a movie
   * @param {number} id
   */
  function deleteMovie(id) {
    return request(`/movies/${id}`, { method: 'DELETE' });
  }

  // ── Auxiliary Endpoints ─────────────────────────────────

  /**
   * GET /dashboard — collection statistics
   */
  function getDashboard() {
    return request('/dashboard');
  }

  /**
   * GET /genres — distinct genre list
   */
  function getGenres() {
    return request('/genres');
  }

  /**
   * GET /health — backend health check
   */
  function getHealth() {
    return request('/health');
  }

  // ── Public API ──────────────────────────────────────────
  return {
    getMovies,
    getMovieById,
    createMovie,
    updateMovie,
    deleteMovie,
    getDashboard,
    getGenres,
    getHealth,
  };

})();
