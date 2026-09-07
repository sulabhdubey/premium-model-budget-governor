(() => {
  const tabs = [...document.querySelectorAll('[data-tour]')];
  if (!tabs.length) return;
  const views = [
    { name: 'direct', label: 'Direct preview', description: 'Start with Astra. Review the selected evidence and estimated spend before authorizing a read-only task.' },
    { name: 'prepared', label: 'Prepared workflow', description: 'Choose preparation only when it earns its place. Sol prepares, Astra receives the original evidence, and the estimate includes both stages.' },
    { name: 'focused', label: 'Focused discovery', description: 'Opt into a smaller skill catalog for compatible tasks. This experiment can omit useful guidance; inherited discovery remains the default.' },
  ];
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const play = document.querySelector('#tour-play');
  const panel = document.querySelector('#tour-panel');
  const narrow = window.matchMedia('(max-width: 560px)');
  const stacked = window.matchMedia('(max-width: 820px)');
  let current = 0;
  let timer = null;
  function updateLayout() {
    document.querySelector('#tour-full-image').href = `assets/tour-${views[current].name}-${narrow.matches ? 'mobile' : 'desktop'}.png`;
    document.querySelector('.tour-tabs').setAttribute('aria-orientation', stacked.matches ? 'horizontal' : 'vertical');
  }
  function stop() {
    clearInterval(timer);
    timer = null;
    play.textContent = 'Play tour';
    play.setAttribute('aria-pressed', 'false');
  }
  function select(index, focus = false) {
    current = (index + views.length) % views.length;
    const view = views[current];
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === current));
      tab.tabIndex = i === current ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', tabs[current].id);
    document.querySelector('#tour-description').textContent = view.description;
    document.querySelector('#tour-view-label').textContent = `0${current + 1} / ${view.label}`;
    document.querySelector('#tour-mobile').srcset = `assets/tour-${view.name}-mobile.png`;
    const img = document.querySelector('#tour-image');
    img.src = `assets/tour-${view.name}-desktop.png`;
    img.alt = `${view.label}: development Workbench capture before any model execution`;
    document.querySelector('.tour-panel picture').scrollTop = 0;
    updateLayout();
    if (!reduced.matches) {
      panel.getAnimations().forEach(animation => animation.cancel());
      panel.animate([{ opacity: 0.45, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 260, easing: 'cubic-bezier(.2,.7,.2,1)' });
    }
    if (focus) tabs[current].focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => { stop(); select(index); });
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = current + 1;
      if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = current - 1;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = views.length - 1;
      if (next !== undefined) { event.preventDefault(); stop(); select(next, true); }
    });
  });
  play.addEventListener('click', () => {
    if (timer) return stop();
    play.textContent = 'Pause tour';
    play.setAttribute('aria-pressed', 'true');
    timer = setInterval(() => select(current + 1), 5000);
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
  document.querySelector('#tour').addEventListener('keydown', event => { if (event.key === 'Escape') stop(); });
  reduced.addEventListener('change', () => { stop(); panel.getAnimations().forEach(animation => animation.cancel()); });
  narrow.addEventListener('change', updateLayout);
  stacked.addEventListener('change', updateLayout);
  updateLayout();
  // Leaving the tour stops playback; returning never resumes it without consent.
  new IntersectionObserver(entries => { if (!entries[0].isIntersecting) stop(); }, { threshold: 0.05 }).observe(document.querySelector('#tour'));
})();
