/** preload links on mouse down */
function pre(ev) {
  if (
    ev.target.tagName === "A" &&
    ev.target.href &&
    ev.target.href.startsWith(window.location.origin)
  ) {
    if (ev.target.hasAttribute("fx-action")) {
      if (ev.target.hasAttribute("no-preload")) return;
      fetch(ev.target.getAttribute("fx-action"), {
        method: "GET",
        headers: { "FX-Request": "true" },
      });
    } else {
      fetch(ev.target.href, { method: "GET", mode: "no-cors" });
    }
  }
}
document.addEventListener("mousedown", pre);
document.addEventListener("touchstart", pre);

/** preload search on input with debounce */
const preloadTimers = new Map();
function preloadInput(ev) {
  const input = ev.target;
  if (!input.hasAttribute("preload")) return;

  if (preloadTimers.has(input)) {
    clearTimeout(preloadTimers.get(input));
  }

  const timer = setTimeout(() => {
    const value = input.value.trim();
    if (!value) return;

    const form = input.closest("form");
    const action = form ? form.getAttribute("action") || "/" : "/";
    const inputName = input.getAttribute("name") || "q";

    const url = new URL(action, window.location.origin);
    url.searchParams.set(inputName, value);

    fetch(url.toString(), { method: "GET", mode: "no-cors" });

    preloadTimers.delete(input);
  }, 500);

  preloadTimers.set(input, timer);
}

document.addEventListener("input", preloadInput);
