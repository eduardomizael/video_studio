(() => {
  'use strict';
  const player = document.querySelector('[data-real-player]');
  if (!player) return;
  const error = document.querySelector('[data-real-player-error]');
  const showError = () => { error.hidden = false; };
  player.addEventListener('error', showError);
  player.querySelector('source')?.addEventListener('error', showError);
  player.addEventListener('loadedmetadata', () => { error.hidden = true; });
  const subtitleData = document.getElementById('active-subtitles');
  if (subtitleData) {
    const version = JSON.parse(subtitleData.textContent);
    if (version.entries.length) {
      const track = player.addTextTrack('subtitles', version.name);
      version.entries.forEach(entry => {
        const text = entry.text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        track.addCue(new VTTCue(entry.start_ms / 1000, entry.end_ms / 1000, text));
      });
      track.mode = 'showing';
    }
  }

  const formatTime = milliseconds => {
    const seconds = Math.floor(milliseconds / 1000);
    return `${String(Math.floor(seconds / 3600)).padStart(2,'0')}:${String(Math.floor(seconds / 60) % 60).padStart(2,'0')}:${String(seconds % 60).padStart(2,'0')}.${String(milliseconds % 1000).padStart(3,'0')}`;
  };
  const timeline = document.querySelector('[data-marking-timeline]');
  const slider = document.querySelector('[data-real-seek]');
  const updateTimeline = () => {
    const duration = Number.isFinite(player.duration) ? Math.round(player.duration * 1000) : Number(timeline?.dataset.durationMs || 0);
    if (slider) { slider.disabled = !duration; slider.max = duration; slider.value = Math.round(player.currentTime * 1000); }
    document.querySelectorAll('.marking-timeline-item').forEach(button => {
      const start = Number(button.dataset.markingStart), end = button.dataset.markingEnd === undefined ? start : Number(button.dataset.markingEnd);
      if (duration > 0) {
        const left = Math.min(99.5, start / duration * 100);
        button.style.left = `${left}%`;
        button.style.width = `${Math.min(100 - left, Math.max(0.5, (end - start) / duration * 100))}%`;
      }
    });
  };
  const updatePosition = () => {
    const now = Math.round(player.currentTime * 1000);
    document.querySelectorAll('[data-real-time]').forEach(el => { el.textContent = formatTime(now); });
    if (slider) slider.value = now;
    document.querySelectorAll('[data-marking-row], .marking-timeline-item').forEach(el => {
      const start = Number(el.dataset.markingStart), end = el.dataset.markingEnd === undefined ? start + 500 : Number(el.dataset.markingEnd);
      el.classList.toggle('active', now >= start && now <= end);
    });
  };
  document.addEventListener('click', event => {
    const capture = event.target.closest('[data-capture-time]');
    if (capture) {
      const input = document.getElementById(capture.dataset.captureTime);
      input.value = formatTime(Math.round(player.currentTime * 1000));
      input.dispatchEvent(new Event('input', {bubbles:true}));
    }
    const seek = event.target.closest('[data-marking-seek]');
    if (seek && !seek.disabled && player.readyState > 0) {
      player.currentTime = Math.min(player.duration, Number(seek.dataset.markingSeek) / 1000);
      updatePosition();
    }
  });
  slider?.addEventListener('input', () => { if (player.readyState > 0) player.currentTime = Number(slider.value) / 1000; });
  player.addEventListener('loadedmetadata', updateTimeline);
  player.addEventListener('durationchange', updateTimeline);
  player.addEventListener('timeupdate', updatePosition);
  player.addEventListener('seeked', updatePosition);
  updateTimeline();
  updatePosition();
})();
