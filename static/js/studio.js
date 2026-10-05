/* Presentation interactions. Real catalog forms are submitted to Django with CSRF. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  let toastTimeout, playbackTimer, editingChapter = null;
  const selectedVideos = new Set();
  let videoData = $('#demo-videos') ? JSON.parse($('#demo-videos').textContent) : [];
  const player = $('[data-player]');
  const seek = $('[data-seek]');
  const duration = Number(player?.dataset.duration || 0);
  let gridMode = 'grid';
  let activeInspection = videoData[0]?.id || 1;

  function toast(message) {
    const target = $('#toast');
    target.textContent = message;
    target.hidden = false;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => { target.hidden = true; }, 5000);
  }
  function dirty() {
    $$('[data-save-status]').forEach(el => { el.textContent = 'Alterações na prévia · ainda não persistidas'; });
  }
  function closePopovers() {
    $$('[data-popover]').forEach(button => {
      button.setAttribute('aria-expanded', 'false');
      document.getElementById(button.dataset.popover).hidden = true;
    });
  }
  function openDialog(id) {
    closePopovers();
    const dialog = document.getElementById(id);
    if (id === 'chapter-dialog') {
      editingChapter = null;
      $('[data-chapter-dialog-title]').textContent = 'Nova marcação temporal';
      $('#chapter-title').value = '';
      $('#chapter-start').value = timecode(Number(seek?.value || 0));
      $('#chapter-end').value = '';
      $('[data-chapter-error]').hidden = true;
    }
    dialog.showModal();
  }
  function timecode(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remaining = Math.floor(seconds % 60);
    if (minutes >= 60) return `${String(Math.floor(minutes / 60)).padStart(2,'0')}:${String(minutes % 60).padStart(2,'0')}:${String(remaining).padStart(2,'0')}`;
    return `${String(minutes).padStart(2,'0')}:${String(remaining).padStart(2,'0')}`;
  }
  function parseTime(value) {
    if (!/^\d{1,3}:\d{2}(?::\d{2})?(?:\.\d{1,3})?$/.test(value.trim())) return NaN;
    const parts = value.trim().split(':').map(Number);
    if (parts.slice(1).some(part => part >= 60)) return NaN;
    return parts.reduce((sum, part) => sum * 60 + part, 0);
  }
  function position(seconds) {
    if (!seek) return;
    seek.value = Math.max(0, Math.min(duration, seconds));
    $$('[data-current-time]').forEach(el => { el.textContent = timecode(Number(seek.value)); });
    const timeline = $('[data-timeline-seek]');
    if (timeline) timeline.value = seek.value;
    const rows = $$('[data-chapter-row]');
    const current = rows.filter(row => Number(row.dataset.seconds) <= Number(seek.value)).at(-1);
    rows.forEach(row => row.classList.toggle('active', row === current));
    const caption = $('[data-player-caption]');
    if (caption && $('.subtitle-list')) {
      const subtitleRows = $$('.subtitle-row');
      const active = subtitleRows.find(row => {
        const inputs = $$('input',row);
        return inputs.length === 2 && parseTime(inputs[0].value) <= Number(seek.value) && parseTime(inputs[1].value) > Number(seek.value);
      });
      const enabled = $('[aria-label="Versão ativa"]')?.checked;
      caption.textContent = enabled && active ? $('textarea',active).value : '';
      subtitleRows.forEach(row => row.classList.toggle('active', enabled && row === active));
    }
  }
  function pause() {
    clearInterval(playbackTimer);
    playbackTimer = null;
    player?.classList.remove('playing');
    $$('[data-play]').forEach(button => {
      $('use', button)?.setAttribute('href', '#icon-play');
      button.setAttribute('aria-label', 'Simular reprodução da linha do tempo');
    });
  }
  function togglePlayback() {
    if (!seek || !duration) { toast('Este ativo não possui linha do tempo para reprodução.'); return; }
    if (playbackTimer) { pause(); return; }
    if (Number(seek.value) >= duration) position(0);
    player.classList.add('playing');
    $$('[data-play]').forEach(button => { $('use', button)?.setAttribute('href', '#icon-pause'); button.setAttribute('aria-label', 'Pausar simulação'); });
    playbackTimer = setInterval(() => {
      const speed = parseFloat($('[data-playback-rate]')?.value || '1');
      position(Number(seek.value) + speed);
      if (Number(seek.value) >= duration) pause();
    }, 1000);
  }
  function updateSelection() {
    $$('[data-select-video]').forEach(input => { input.checked = selectedVideos.has(Number(input.dataset.selectVideo)); });
    const bar = $('#selection-bar');
    if (!bar) return;
    bar.hidden = selectedVideos.size === 0;
    $('#selection-count').textContent = `${selectedVideos.size} ${selectedVideos.size === 1 ? 'item selecionado' : 'itens selecionados'}`;
  }
  function inspect(id) {
    const video = videoData.find(item => item.id === id);
    if (!video) return;
    activeInspection = id;
    const mapping = { title: 'title', codec: 'codec', resolution: 'resolution', duration: 'duration', size: 'size', status: 'status' };
    Object.entries(mapping).forEach(([field, property]) => { const target = $(`#inspector-${field}`); if (target) target.textContent = video[property]; });
    $('#inspector-status').classList.toggle('green-text', video.tone === 'green');
    $('#inspector-preview').className = `inspector-preview thumb-${video.thumb}`;
    const image = $('#inspector-thumbnail');
    if (image) { image.hidden = !video.thumbnail_url; if (video.thumbnail_url) image.src = video.thumbnail_url; else image.removeAttribute('src'); }
    $('#inspector-editor-link').href = video.editor_url;
    $('#inspector-preview-link').href = video.editor_url;
    if ($('#inspector-chapters-link')) $('#inspector-chapters-link').href = video.chapters_url;
    $('#inspector-tags').replaceChildren(...video.tags.map(tag => {
      const span = document.createElement('span'); span.className = 'badge purple'; span.textContent = tag; return span;
    }));
    $$('[data-media-card]').forEach(card => { card.classList.toggle('selected', Number(card.dataset.mediaCard) === id); });
    toast(`Inspetor: ${video.title}`);
  }
  function chip(label, list, person = false) {
    const clean = label.trim();
    if (!clean) return;
    const existing = $$('.tag-chip', list).some(el => el.textContent.replace(/×\s*$/, '').trim().toLocaleLowerCase('pt-BR') === clean.toLocaleLowerCase('pt-BR'));
    if (existing) { toast('Esse item já está associado.'); return; }
    const span = document.createElement('span');
    span.className = `tag-chip${person ? ' person-chip' : ''}`;
    span.append(document.createTextNode(clean));
    const button = document.createElement('button'); button.type = 'button'; button.dataset.removeChip = ''; button.setAttribute('aria-label', `Remover associação de ${clean}`); button.textContent = '×';
    span.append(button); list.append(span); dirty();
  }
  function renderChapterRow(title, start, end) {
    const row = document.createElement('div'); row.className = 'chapter-row'; row.dataset.chapterRow = ''; row.dataset.seconds = start;
    if (end !== null) row.dataset.end = end;
    const jump = document.createElement('button'); jump.type = 'button'; jump.className = 'chapter-seek'; jump.dataset.jump = start; jump.setAttribute('aria-label', `Ir para ${timecode(start)} — ${title}`); jump.textContent = `▷ ${timecode(start)}`;
    const label = document.createElement('span'); label.className = 'chapter-title'; label.textContent = title;
    const length = document.createElement('span'); length.className = 'mono muted-text chapter-length'; length.textContent = end === null ? 'Ponto' : timecode(end - start);
    const edit = document.createElement('button'); edit.type = 'button'; edit.className = 'icon-button'; edit.dataset.editChapter = ''; edit.setAttribute('aria-label', `Editar ${title}`); edit.textContent = '✎';
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'icon-button danger'; remove.dataset.removeChapter = ''; remove.setAttribute('aria-label', `Remover marcação ${title}`); remove.textContent = '×';
    row.append(jump, label, length, edit, remove); return row;
  }
  function sortChapters() {
    const list = $('[data-chapter-list]');
    if (!list) return;
    const rows = $$('[data-chapter-row]', list).sort((a,b) => Number(a.dataset.seconds) - Number(b.dataset.seconds));
    rows.forEach(row => list.append(row));
    const count = $('[data-chapter-count]'); if (count) count.textContent = `${rows.length} marcadores`;
    position(Number(seek?.value || 0));
  }
  document.addEventListener('click', event => {
    const popoverButton = event.target.closest('[data-popover]');
    if (popoverButton) {
      const open = popoverButton.getAttribute('aria-expanded') !== 'true'; closePopovers();
      popoverButton.setAttribute('aria-expanded', String(open)); document.getElementById(popoverButton.dataset.popover).hidden = !open; return;
    }
    if (!event.target.closest('.popover')) closePopovers();
    const trigger = event.target.closest('[data-dialog]'); if (trigger) openDialog(trigger.dataset.dialog);
    if (event.target.closest('[data-close-dialog]')) event.target.closest('dialog').close();
    const note = event.target.closest('[data-toast]'); if (note) toast(note.dataset.toast);
    if (event.target.closest('[data-demo-save]')) { toast('Prévia conferida. As alterações ainda não são gravadas no banco.'); $$('[data-save-status]').forEach(el => { el.textContent = 'Prévia conferida · sem persistência'; }); }
    if (event.target.closest('[data-demo-reset]')) window.location.reload();
    const view = event.target.closest('[data-view]'); if (view) {
      gridMode = view.dataset.view; $('[data-media-grid]')?.classList.toggle('list-view', gridMode === 'list');
      $$('[data-view]').forEach(button => { button.classList.toggle('active', button === view); button.setAttribute('aria-pressed', String(button === view)); });
    }
    const category = event.target.closest('[data-category]'); if (category) {
      const form = $('#library-filters'); $('input[name=category]', form).value = category.dataset.category;
      $$('[data-category]').forEach(button => { button.classList.toggle('active', button === category); button.setAttribute('aria-pressed', String(button === category)); });
      form.requestSubmit();
    }
    const inspection = event.target.closest('[data-inspect]'); if (inspection) inspect(Number(inspection.dataset.inspect));
    if (event.target.closest('[data-clear-selection]')) { selectedVideos.clear(); updateSelection(); }
    const removeChip = event.target.closest('[data-remove-chip]'); if (removeChip) { removeChip.closest('.tag-chip').remove(); dirty(); }
    const addChip = event.target.closest('[data-add-chip]'); if (addChip) chip(addChip.dataset.addChip, $('.tag-list', addChip.closest('[data-tag-editor]')));
    const thumbnail = event.target.closest('[data-thumbnail]'); if (thumbnail) { $$('[data-thumbnail]').forEach(button => { button.classList.toggle('active', button === thumbnail); button.setAttribute('aria-pressed', String(button === thumbnail)); }); dirty(); }
    if (event.target.closest('[data-play]')) togglePlayback();
    const step = event.target.closest('[data-step]'); if (step) position(Number(seek.value) + Number(step.dataset.step));
    const jump = event.target.closest('[data-jump]'); if (jump) position(Number(jump.dataset.jump));
    if (event.target.closest('[data-player-expand]')) player.classList.toggle('expanded');
    const removeChapter = event.target.closest('[data-remove-chapter]'); if (removeChapter) { removeChapter.closest('[data-chapter-row]').remove(); sortChapters(); dirty(); toast('Marcação removida apenas da prévia.'); }
    const editChapter = event.target.closest('[data-edit-chapter]'); if (editChapter) {
      const row = editChapter.closest('[data-chapter-row]'); openDialog('chapter-dialog'); editingChapter = row;
      $('[data-chapter-dialog-title]').textContent = 'Editar marcação temporal'; $('#chapter-title').value = $('.chapter-title', row).textContent; $('#chapter-start').value = timecode(Number(row.dataset.seconds)); $('#chapter-end').value = row.dataset.end ? timecode(Number(row.dataset.end)) : '';
    }
    const tab = event.target.closest('[data-tab]'); if (tab) {
      $$('[data-tab]').forEach(button => { button.classList.toggle('active', button === tab); button.setAttribute('aria-selected', String(button === tab)); button.tabIndex = button === tab ? 0 : -1; document.getElementById(button.dataset.tab).hidden = button !== tab; });
    }
    const readAll = event.target.closest('[data-read-all]'); if (readAll) { $$('.notification-item', readAll.closest('.panel, .popover')).forEach(el => el.classList.add('read')); readAll.textContent = 'Todas lidas'; $('.notification-dot').hidden = true; toast('Notificações da prévia marcadas como lidas.'); }
    const notificationFilter = event.target.closest('[data-notification-filter]'); if (notificationFilter) {
      const parent = notificationFilter.closest('.panel, .popover');
      $$('[data-notification-filter]', parent).forEach(button => { button.classList.toggle('active', button === notificationFilter); button.setAttribute('aria-pressed', String(button === notificationFilter)); });
      $$('[data-notification-group]', parent).forEach(item => { item.hidden = notificationFilter.dataset.notificationFilter !== 'all' && item.dataset.notificationGroup !== notificationFilter.dataset.notificationFilter; });
    }
    if (event.target.closest('[data-mark-person]')) {
      const name = $('#person-marker').value; const row = document.createElement('div'); row.className = 'person-marker';
      const avatar = document.createElement('span'); avatar.className = 'initial-avatar'; avatar.textContent = name[0];
      const content = document.createElement('div'); const label = document.createElement('strong'); label.textContent = name; const time = document.createElement('small'); time.textContent = `Ponto · ${timecode(Number(seek.value))}`; content.append(label,time);
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'icon-button'; remove.dataset.removeMarker = ''; remove.textContent = '×'; remove.setAttribute('aria-label',`Remover marcação de ${name}`);
      row.append(avatar,content,remove); $('[data-person-markers]').append(row); dirty();
    }
    const removeMarker = event.target.closest('[data-remove-marker]'); if (removeMarker) { removeMarker.closest('.person-marker').remove(); dirty(); }
    if (event.target.closest('[data-add-subtitle]')) {
      const list = $('.subtitle-list'); const source = $('.subtitle-row', list) || $('#empty-subtitle').content.firstElementChild; const copy = source.cloneNode(true); const number = $$('.subtitle-row', list).length + 1;
      $('textarea', copy).value = ''; $('textarea', copy).id = `subtitle-${number}`; $('.sr-only', copy).htmlFor = `subtitle-${number}`; $('.sr-only', copy).textContent = `Texto da legenda ${number}`;
      $$('input', copy).forEach((input,index) => { input.value = '00:00:00.000'; input.setAttribute('aria-label', `${index === 0 ? 'Início' : 'Fim'} da legenda ${number}`); });
      $('.badge',copy).textContent = 'Nova entrada'; list.append(copy); $('textarea',copy).focus(); dirty();
    }
  });
  document.addEventListener('input', event => {
    if (event.target.closest('[data-marking-form]')) document.querySelector('[data-marking-save-status]').textContent = 'Alterações não salvas. Salve a marcação para gravar.';
    if (event.target.matches('[data-choice-filter]')) {
      const select = document.getElementById(event.target.dataset.choiceFilter);
      const query = event.target.value.toLocaleLowerCase('pt-BR');
      [...select.options].forEach(option => { option.hidden = !option.selected && !option.textContent.toLocaleLowerCase('pt-BR').includes(query); });
    }
    if (event.target.closest('[data-persistent-form]') && event.target.matches('input, textarea, select') && !event.target.matches('[data-choice-filter]') && !event.target.closest('video')) {
      $('[data-persist-status]').textContent = 'Alterações não salvas. Clique em Salvar para gravar.';
    }
    if (event.target.matches('[data-counter]')) document.getElementById(event.target.dataset.counter).textContent = `${event.target.value.length}/${event.target.maxLength}`;
    if (event.target.matches('[data-seek], [data-timeline-seek]')) position(Number(event.target.value));
    if (event.target.closest('[data-dirty-scope]')) dirty();
    if (event.target.closest('.subtitle-row')) position(Number(seek?.value || 0));
  });
  document.addEventListener('change', event => {
    if (event.target.closest('[data-persistent-form]') && event.target.matches('input, textarea, select') && !event.target.closest('video')) $('[data-persist-status]').textContent = 'Alterações não salvas. Clique em Salvar para gravar.';
    if (event.target.matches('[data-select-video]')) { const id = Number(event.target.dataset.selectVideo); event.target.checked ? selectedVideos.add(id) : selectedVideos.delete(id); updateSelection(); }
    if (event.target.matches('[data-theme-toggle]')) { document.body.classList.toggle('light', !event.target.checked); $$('[data-theme-toggle]').forEach(input => { input.checked = event.target.checked; }); }
    if (event.target.matches('[data-caption-size]')) $('[data-player-caption]').style.fontSize = `${event.target.value}px`;
    if (event.target.matches('[data-caption-background]')) $('[data-player-caption]').style.background = event.target.checked ? '' : 'transparent';
    if (event.target.matches('[data-subtitle-version]')) toast('Versão selecionada na prévia. O conteúdo de exemplo permanece o mesmo.');
    if (event.target.matches('[aria-label="Versão ativa"]')) position(Number(seek?.value || 0));
  });
  document.addEventListener('submit', event => {
    if (event.target.matches('[data-demo-form]')) { event.preventDefault(); event.target.closest('dialog').close(); toast('Dados conferidos na demonstração. Nenhum arquivo foi enviado ou registro criado.'); }
    if (event.target.matches('[data-person-form]')) { event.preventDefault(); chip($('#person-name').value, $('[data-people-list]'), true); event.target.closest('dialog').close(); event.target.reset(); }
    if (event.target.matches('[data-chapter-form]')) {
      event.preventDefault(); const start = parseTime($('#chapter-start').value); const end = $('#chapter-end').value.trim() ? parseTime($('#chapter-end').value) : null; const title = $('#chapter-title').value.trim();
      const error = $('[data-chapter-error]');
      if (!title || !Number.isFinite(start) || (end !== null && (!Number.isFinite(end) || end <= start)) || start > duration || (end !== null && end > duration)) {
        error.textContent = 'Informe um título e tempos válidos (MM:SS ou HH:MM:SS), dentro da duração. O fim deve ser posterior ao início.'; error.hidden = false; return;
      }
      const row = renderChapterRow(title,start,end); if (editingChapter) editingChapter.replaceWith(row); else $('[data-chapter-list]').append(row);
      sortChapters(); event.target.closest('dialog').close(); dirty(); toast('Marcação aplicada apenas à prévia.');
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { closePopovers(); player?.classList.remove('expanded'); }
    const tab = event.target.closest('[data-tab]');
    if (tab && ['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
      event.preventDefault(); const tabs = $$('[data-tab]'); const index = tabs.indexOf(tab); const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length; tabs[next].click(); tabs[next].focus(); return;
    }
    if (event.target.matches('[data-tag-input]') && event.key === 'Enter') { event.preventDefault(); chip(event.target.value, $('.tag-list',event.target.closest('[data-tag-editor]'))); event.target.value = ''; return; }
    if (event.target.matches('input, textarea, select') || event.target.isContentEditable || $('dialog[open]')) return;
    if (event.key === '/') { event.preventDefault(); $('.global-search input').focus(); }
    if (event.key === '?') { event.preventDefault(); openDialog('shortcuts-dialog'); }
    if (event.code === 'Space' && player && !event.target.closest('button, a')) { event.preventDefault(); togglePlayback(); }
  });
  document.addEventListener('htmx:afterSwap', () => {
    if ($('#demo-videos')) { videoData = JSON.parse($('#demo-videos').textContent); activeInspection = videoData[0]?.id || 1; }
    $('[data-media-grid]')?.classList.toggle('list-view', gridMode === 'list'); updateSelection();
    $$('[data-media-card]').forEach(card => card.classList.toggle('selected', Number(card.dataset.mediaCard) === activeInspection));
  });
  document.addEventListener('htmx:responseError', () => toast('Não foi possível atualizar o acervo. Tente novamente.'));
  position(Number(seek?.value || 0));
})();
