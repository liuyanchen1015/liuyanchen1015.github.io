/**
 * Click any element carrying data-video-src (a publication's thumbnail clip, or
 * the film icon in its link row) to watch that clip full size.
 */
(function () {
  var overlay = null;
  var player = null;
  var lastFocus = null;

  function build() {
    overlay = document.createElement('div');
    overlay.className = 'video-lightbox';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.innerHTML =
      '<button type="button" class="video-lightbox-close" aria-label="Close">&times;</button>' +
      '<video class="video-lightbox-player" controls loop muted playsinline></video>';
    player = overlay.querySelector('video');
    overlay.addEventListener('click', function (e) {
      // only the backdrop and the close button dismiss; clicks on the player itself
      // belong to its own controls
      if (e.target === overlay || e.target.classList.contains('video-lightbox-close')) {
        close();
      }
    });
    document.body.appendChild(overlay);
  }

  function open(src, poster) {
    if (!overlay) build();
    lastFocus = document.activeElement;
    player.src = src;
    if (poster) {
      player.poster = poster;
    } else {
      player.removeAttribute('poster');
    }
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    overlay.querySelector('.video-lightbox-close').focus();
    var p = player.play();
    if (p && p.catch) p.catch(function () {});
  }

  function close() {
    if (!overlay || !overlay.classList.contains('is-open')) return;
    overlay.classList.remove('is-open');
    player.pause();
    player.removeAttribute('src');
    player.load(); // stop the download of a clip nobody is watching any more
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  document.addEventListener('click', function (e) {
    var trigger = e.target.closest ? e.target.closest('[data-video-src]') : null;
    if (!trigger) return;
    e.preventDefault();
    open(trigger.getAttribute('data-video-src'), trigger.getAttribute('data-video-poster'));
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.key === 'Esc') close();
  });
})();
