const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#navigation');
if (toggle && nav) {
  const closeMenu = () => { toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); };
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('is-open') && !document.querySelector('dialog[open]')) { closeMenu(); toggle.focus(); } });
  nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  window.matchMedia('(min-width: 1251px)').addEventListener('change', closeMenu);
}
const result = document.querySelector('#enquiry-result');
if (result) result.focus();
const form = document.querySelector('.enquiry-form');
if (form) form.addEventListener('submit', () => {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = 'Saving your enquiry…';
});
window.addEventListener('pageshow', () => {
  const button = document.querySelector('.enquiry-form button[type="submit"]');
  if (button) { button.disabled = false; button.textContent = 'Send your enquiry ↗'; }
});
