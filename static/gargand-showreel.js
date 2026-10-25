/* Lightweight animated product tour; the site background stays static. */
(() => {
  "use strict";

  const film = document.getElementById("ggCinematicFilm");
  const scenes = film ? Array.from(film.querySelectorAll("[data-film-scene-panel]")) : [];
  if (!film || !scenes.length) return;

  const reduceMotion = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const fallbackDelay = 6500;
  let current = -1;
  let fallbackTimer = 0;

  function activateScene(index) {
    if (!film || !scenes.length) return;
    index = (index + scenes.length) % scenes.length;
    if (index === current) return;
    current = index;
    film.dataset.filmScene = String(index);
    scenes.forEach((scene, sceneIndex) => {
      const active = sceneIndex === index;
      scene.classList.toggle("is-active", active);
      scene.setAttribute("aria-hidden", active ? "false" : "true");
    });
  }

  function clearFallback() {
    if (fallbackTimer) window.clearTimeout(fallbackTimer);
    fallbackTimer = 0;
  }

  function scheduleNextScene() {
    clearFallback();
    if (!film || !scenes.length || reduceMotion || document.hidden) return;
    fallbackTimer = window.setTimeout(() => {
      activateScene(current < 0 ? 0 : current + 1);
      scheduleNextScene();
    }, fallbackDelay);
  }

  film.dataset.filmState = "animated-showcase";
  activateScene(0);
  scheduleNextScene();

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      clearFallback();
    } else {
      scheduleNextScene();
    }
  });

})();
