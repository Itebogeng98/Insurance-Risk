(() => {
  const drawer = document.getElementById('mobileSidebar');
  const desktop = window.matchMedia('(min-width: 1200px)');
  if (drawer) {
    drawer.addEventListener('shown.bs.offcanvas', () => {
      if (desktop.matches) window.bootstrap?.Offcanvas.getInstance(drawer)?.hide();
    });
    desktop.addEventListener('change', (event) => {
      if (event.matches) window.bootstrap?.Offcanvas.getInstance(drawer)?.hide();
    });
  }

  const publicMenu = document.getElementById('publicNavigation');
  publicMenu?.addEventListener('click', (event) => {
    if (event.target.closest('a') && window.innerWidth < 1200) {
      const close = () => window.bootstrap?.Collapse.getInstance(publicMenu)?.hide();
      if (publicMenu.classList.contains('collapsing')) {
        publicMenu.addEventListener('shown.bs.collapse', close, { once: true });
      } else {
        close();
      }
    }
  });

  // Keyboard users can scroll wide data tables without moving the whole page.
  document.querySelectorAll('.table-responsive').forEach((region) => {
    region.tabIndex = 0;
    region.setAttribute('role', 'region');
    if (!region.hasAttribute('aria-label')) {
      const heading = region.closest('.card')?.querySelector('.card-header');
      region.setAttribute('aria-label', heading?.textContent.trim() || 'Records');
    }
  });
})();
