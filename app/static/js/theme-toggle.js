(function () {
  const btnId = 'themeToggle';
  const storageKey = 'booking_theme';

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('theme-dark');
    } else {
      document.documentElement.classList.remove('theme-dark');
    }
  }

  function toggleTheme() {
    const current = localStorage.getItem(storageKey) || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(storageKey, next);
    applyTheme(next);
    updateButton(next);
  }

  function updateButton(theme) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    btn.title = theme === 'dark' ? 'Светлая тема' : 'Тёмная тема';
  }

  document.addEventListener('DOMContentLoaded', function () {
    // init
    const saved = localStorage.getItem(storageKey) || 'light';
    applyTheme(saved);
    updateButton(saved);

    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', toggleTheme);
    }
  });
})();
