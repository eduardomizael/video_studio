(() => {
  'use strict';
  const player = document.querySelector('[data-real-player]');
  if (!player) return;
  const error = document.querySelector('[data-real-player-error]');
  const showError = () => { error.hidden = false; };
  player.addEventListener('error', showError);
  player.querySelector('source')?.addEventListener('error', showError);
  player.addEventListener('loadedmetadata', () => { error.hidden = true; });
})();
