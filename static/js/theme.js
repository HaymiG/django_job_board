(function () {
  const STORAGE_KEY = "jb-theme";
  const root = document.documentElement;

  function getPreferred() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function getStored() {
    return localStorage.getItem(STORAGE_KEY);
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateToggleIcon(theme);
  }

  function updateToggleIcon(theme) {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    const icon = btn.querySelector("i");
    if (!icon) return;
    icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    btn.setAttribute(
      "aria-label",
      theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
    );
    btn.setAttribute("title", theme === "dark" ? "Light mode" : "Dark mode");
  }

  function init() {
    const stored = getStored();
    const theme = stored === "light" || stored === "dark" ? stored : getPreferred();
    apply(theme);

    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        const current = root.getAttribute("data-theme") || "light";
        apply(current === "dark" ? "light" : "dark");
      });
    }

    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
      if (!getStored()) {
        apply(e.matches ? "dark" : "light");
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
