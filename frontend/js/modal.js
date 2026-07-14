'use strict';

/**
 * modal.js — Modal Management Module
 *
 * Handles three modal variants:
 *  1. Details modal  — view full movie info
 *  2. Form modal     — add or edit a movie
 *  3. Confirm modal  — delete confirmation
 *
 * Public API: openDetails, openAdd, openEdit, openDelete, closeAll
 */
const Modal = (() => {

  // Internal state for the current form operation
  let _editingId    = null; // movie id when in edit mode (null = add mode)
  let _deletingId   = null; // movie id pending deletion
  let _deletingName = null; // movie title for confirmation text

  // ── Overlay Helpers ─────────────────────────────────────

  /** Open a modal overlay by its element ID. */
  function _open(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.removeAttribute('hidden');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    // Move keyboard focus inside the modal
    setTimeout(() => {
      const first = overlay.querySelector(
        'button:not([disabled]), input, select, textarea, [tabindex="0"]'
      );
      if (first) first.focus();
    }, 60);
  }

  /** Close a modal overlay by its element ID. */
  function _close(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.setAttribute('hidden', '');
    overlay.setAttribute('aria-hidden', 'true');

    // Only remove body lock when no other modals are open
    const stillOpen = document.querySelectorAll('.modal-overlay:not([hidden])');
    if (stillOpen.length === 0) document.body.classList.remove('modal-open');
  }

  /** Close all modals immediately. */
  function closeAll() {
    document.querySelectorAll('.modal-overlay').forEach((m) => {
      m.setAttribute('hidden', '');
      m.setAttribute('aria-hidden', 'true');
    });
    document.body.classList.remove('modal-open');
  }

  // ── Poster Helper ────────────────────────────────────────

  /**
   * Set the poster image or gradient placeholder in the details modal.
   * @param {object} movie
   */
  function _setPoster(movie) {
    const img         = document.getElementById('details-poster');
    const placeholder = document.getElementById('details-poster-placeholder');
    const letter      = document.getElementById('details-poster-letter');
    if (!img || !placeholder) return;

    const [from, to] = Utils.stringToGradient(movie.title);
    placeholder.style.setProperty('--grad-from', from);
    placeholder.style.setProperty('--grad-to',   to);
    if (letter) letter.textContent = movie.title.charAt(0).toUpperCase();

    if (movie.poster_url) {
      img.src   = movie.poster_url;
      img.alt   = `${movie.title} poster`;
      img.style.display = 'block';
      placeholder.setAttribute('hidden', '');

      img.onerror = () => {
        img.style.display = 'none';
        placeholder.removeAttribute('hidden');
      };
    } else {
      img.style.display = 'none';
      placeholder.removeAttribute('hidden');
    }
  }

  // ═══════════════════════════════════════════════════════
  // DETAILS MODAL
  // ═══════════════════════════════════════════════════════

  /**
   * Populate and open the details modal for a movie.
   * @param {object} movie
   */
  function openDetails(movie) {
    _setPoster(movie);

    // Status badge
    const badge = document.getElementById('details-status-badge');
    badge.textContent = movie.status;
    badge.className   = `badge badge--${Utils.getStatusClass(movie.status)}`;

    // Text fields
    document.getElementById('modal-details-title').textContent  = movie.title;
    document.getElementById('details-genre').textContent        = movie.genre;
    document.getElementById('details-year').textContent         = movie.release_year;
    document.getElementById('details-duration').textContent     = Utils.formatDuration(movie.duration);
    document.getElementById('details-rating').textContent       = Utils.formatRating(movie.rating);
    document.getElementById('details-description').textContent  = movie.description || 'No description available.';
    document.getElementById('details-created').textContent      = Utils.formatDate(movie.created_at);
    document.getElementById('details-updated').textContent      = Utils.formatDate(movie.updated_at);

    // Edit / Delete shortcuts in details view
    document.getElementById('btn-edit-from-details').onclick = () => {
      _close('modal-details');
      openEdit(movie);
    };
    document.getElementById('btn-delete-from-details').onclick = () => {
      _close('modal-details');
      openDelete(movie);
    };

    _open('modal-details');
  }

  // ═══════════════════════════════════════════════════════
  // FORM MODAL (Add / Edit)
  // ═══════════════════════════════════════════════════════

  /** Reset form to its blank state. */
  function _resetForm() {
    const form = document.getElementById('movie-form');
    if (form) form.reset();
    document.getElementById('form-movie-id').value = '';
    _clearFormErrors();
    document.querySelectorAll('.input--error, .select--error').forEach((el) => {
      el.classList.remove('input--error', 'select--error');
    });
  }

  function _clearFormErrors() {
    const errBox = document.getElementById('form-errors');
    if (errBox) {
      errBox.setAttribute('hidden', '');
      errBox.innerHTML = '';
    }
  }

  /** Open the Add Movie form modal. */
  function openAdd() {
    _editingId = null;
    _resetForm();
    document.getElementById('modal-form-title').textContent = 'Add Movie';
    document.getElementById('form-submit').textContent      = 'Add Movie';
    _open('modal-form');
  }

  /** Open the Edit Movie form modal, pre-filled with movie data. */
  function openEdit(movie) {
    _editingId = movie.id;
    _resetForm();

    document.getElementById('modal-form-title').textContent = 'Edit Movie';
    document.getElementById('form-submit').textContent      = 'Save Changes';
    document.getElementById('form-movie-id').value          = movie.id;

    // Pre-fill all fields
    document.getElementById('form-title').value       = movie.title        || '';
    document.getElementById('form-genre').value       = movie.genre        || '';
    document.getElementById('form-year').value        = movie.release_year || '';
    document.getElementById('form-duration').value    = movie.duration     || '';
    document.getElementById('form-rating').value      = movie.rating !== null && movie.rating !== undefined
                                                          ? movie.rating : '';
    document.getElementById('form-status').value      = movie.status       || '';
    document.getElementById('form-poster').value      = movie.poster_url   || '';
    document.getElementById('form-description').value = movie.description  || '';

    _open('modal-form');
  }

  /** Read all form field values into a payload object. */
  function _getFormPayload() {
    const rating = parseFloat(document.getElementById('form-rating').value);
    return {
      title:        document.getElementById('form-title').value.trim(),
      genre:        document.getElementById('form-genre').value.trim(),
      release_year: parseInt(document.getElementById('form-year').value, 10) || null,
      duration:     parseInt(document.getElementById('form-duration').value, 10) || null,
      rating:       isNaN(rating) ? null : rating,
      status:       document.getElementById('form-status').value,
      poster_url:   document.getElementById('form-poster').value.trim() || null,
      description:  document.getElementById('form-description').value.trim() || null,
    };
  }

  /** Client-side validation before hitting the API. Returns [] if valid. */
  function _validatePayload(payload) {
    const errors = [];
    if (!payload.title)                         errors.push('Title is required.');
    if (!payload.genre)                         errors.push('Genre is required.');
    if (!payload.release_year)                  errors.push('Release year is required.');
    if (!payload.duration || payload.duration < 1) errors.push('Duration must be at least 1 minute.');
    if (payload.rating === null)                errors.push('Rating is required.');
    if (!payload.status)                        errors.push('Status is required.');
    return errors;
  }

  /** Display validation or API errors inside the form. */
  function _showFormErrors(errors) {
    const box = document.getElementById('form-errors');
    if (!box) return;
    box.removeAttribute('hidden');
    box.innerHTML = errors.map((e) =>
      `<p class="form-error-item">${Utils.escapeHtml(e)}</p>`
    ).join('');
  }

  /** Handle form submit for both Add and Edit modes. */
  async function _handleSubmit(e) {
    e.preventDefault();
    _clearFormErrors();

    const submitBtn = document.getElementById('form-submit');
    const isEdit    = _editingId !== null;
    const payload   = _getFormPayload();

    // Client-side validation
    const clientErrors = _validatePayload(payload);
    if (clientErrors.length > 0) {
      _showFormErrors(clientErrors);
      return;
    }

    submitBtn.disabled    = true;
    submitBtn.textContent = isEdit ? 'Saving…' : 'Adding…';

    try {
      if (isEdit) {
        await API.updateMovie(_editingId, payload);
        Utils.showToast('Movie updated successfully!', 'success');
      } else {
        await API.createMovie(payload);
        Utils.showToast('Movie added to your collection!', 'success');
      }
      _close('modal-form');
      // Refresh both the grid and the stats
      await Promise.all([MovieGrid.load(), Dashboard.load()]);

    } catch (err) {
      console.error('[Modal] Submit error:', err);
      const apiErrors = err.errors && err.errors.length > 0
        ? err.errors
        : [err.message || 'An unexpected error occurred. Please try again.'];
      _showFormErrors(apiErrors);

    } finally {
      submitBtn.disabled    = false;
      submitBtn.textContent = isEdit ? 'Save Changes' : 'Add Movie';
    }
  }

  // ═══════════════════════════════════════════════════════
  // DELETE CONFIRMATION MODAL
  // ═══════════════════════════════════════════════════════

  /** Open the delete confirmation dialog for a movie. */
  function openDelete(movie) {
    _deletingId   = movie.id;
    _deletingName = movie.title;
    document.getElementById('delete-movie-name').textContent =
      `"${Utils.escapeHtml(movie.title)}"`;
    _open('modal-delete');
  }

  /** Handle the confirm delete button click. */
  async function _handleDeleteConfirm() {
    if (!_deletingId) return;

    const btn = document.getElementById('btn-confirm-delete');
    btn.disabled    = true;
    btn.textContent = 'Deleting…';

    try {
      await API.deleteMovie(_deletingId);
      Utils.showToast(`"${_deletingName}" has been deleted.`, 'success');
      _close('modal-delete');
      await Promise.all([MovieGrid.load(), Dashboard.load()]);

    } catch (err) {
      console.error('[Modal] Delete error:', err);
      Utils.showToast(err.message || 'Failed to delete movie.', 'error');

    } finally {
      btn.disabled    = false;
      btn.textContent = 'Delete';
      _deletingId   = null;
      _deletingName = null;
    }
  }

  // ═══════════════════════════════════════════════════════
  // INIT
  // ═══════════════════════════════════════════════════════

  /**
   * Wire all persistent modal event listeners.
   * Called once during app initialization.
   */
  function init() {
    // Form submit
    document.getElementById('movie-form')
      ?.addEventListener('submit', _handleSubmit);

    // Delete confirm button
    document.getElementById('btn-confirm-delete')
      ?.addEventListener('click', _handleDeleteConfirm);

    // [data-close] buttons close their respective modal
    document.querySelectorAll('[data-close]').forEach((btn) => {
      btn.addEventListener('click', () => _close(btn.dataset.close));
    });

    // Clicking the backdrop (overlay itself, not the modal box) closes it
    document.querySelectorAll('.modal-overlay').forEach((overlay) => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) _close(overlay.id);
      });
    });

    // Escape key closes the topmost open modal
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      const open = document.querySelector('.modal-overlay:not([hidden])');
      if (open) _close(open.id);
    });
  }

  // ── Public API ──────────────────────────────────────────
  return { init, openDetails, openAdd, openEdit, openDelete, closeAll };

})();
