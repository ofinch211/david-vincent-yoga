/* Apply saved appearance before styles paint; no server data or tracking. */
(() => {
  const storageKey = 'dv-yoga-appearance';
  const themes = ['forest', 'coastal', 'terracotta', 'lavender', 'olive'];
  const names = {forest: 'Forest & ivory', coastal: 'Coastal blue', terracotta: 'Warm terracotta', lavender: 'Soft lavender', olive: 'Olive & sand'};
  let preference = {mode: 'day', theme: 'forest'};
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved && ['day', 'dark'].includes(saved.mode)) preference.mode = saved.mode;
    if (saved && themes.includes(saved.theme)) preference.theme = saved.theme;
  } catch (_) { /* Private browsing or unavailable storage: use the defaults. */ }
  const apply = () => {
    document.documentElement.dataset.mode = preference.mode;
    document.documentElement.dataset.theme = preference.theme;
  };
  apply();

  document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.querySelector('#appearance-settings');
    const toggle = document.querySelector('#mode-toggle');
    const open = document.querySelector('#settings-toggle');
    const sync = () => {
      apply();
      toggle.setAttribute('aria-label', preference.mode === 'day' ? 'Switch to dark mode' : 'Switch to day mode');
      toggle.setAttribute('aria-pressed', String(preference.mode === 'dark'));
      toggle.title = preference.mode === 'day' ? 'Switch to dark mode' : 'Switch to day mode';
      dialog.querySelectorAll('[data-mode-choice]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.modeChoice === preference.mode)));
      dialog.querySelectorAll('input[name="colour-theme"]').forEach(input => { input.checked = input.value === preference.theme; });
      document.querySelector('#appearance-status').textContent = `${names[preference.theme]} · ${preference.mode === 'day' ? 'Day' : 'Dark'} mode`;
      const colour = getComputedStyle(document.documentElement).getPropertyValue('--ivory').trim();
      document.querySelector('meta[name="theme-color"]').content = colour;
    };
    const save = () => {
      sync();
      try { localStorage.setItem(storageKey, JSON.stringify(preference)); } catch (_) { /* Selection still works for this page. */ }
    };
    toggle.addEventListener('click', () => { preference.mode = preference.mode === 'day' ? 'dark' : 'day'; save(); });
    open.addEventListener('click', () => { dialog.showModal(); });
    dialog.querySelector('.settings-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
    dialog.querySelectorAll('[data-mode-choice]').forEach(button => button.addEventListener('click', () => { preference.mode = button.dataset.modeChoice; save(); }));
    dialog.querySelectorAll('input[name="colour-theme"]').forEach(input => input.addEventListener('change', () => { preference.theme = input.value; save(); }));
    dialog.querySelector('#appearance-reset').addEventListener('click', () => { preference = {mode: 'day', theme: 'forest'}; save(); });
    window.addEventListener('storage', event => {
      if (event.key !== storageKey) return;
      try {
        const saved = JSON.parse(event.newValue);
        if (saved && themes.includes(saved.theme) && ['day', 'dark'].includes(saved.mode)) { preference = saved; sync(); }
        else if (!saved) { preference = {mode: 'day', theme: 'forest'}; sync(); }
      } catch (_) { /* Ignore malformed preferences from another tab. */ }
    });
    sync();
    document.querySelectorAll('.appearance-control').forEach(button => { button.hidden = false; });
  });
})();
